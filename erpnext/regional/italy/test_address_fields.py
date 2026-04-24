import unittest
from types import SimpleNamespace
from unittest.mock import patch

import frappe

from erpnext.regional.italy import utils


class TestItalyAddressFields(unittest.TestCase):
	def test_validate_address_accepts_italian_province_code_in_state(self):
		address_data = frappe._dict(
			{
				"pincode": "38057",
				"city": "Pergine Valsugana",
				"country": "Italy",
				"country_code": "IT",
				"state": "TN",
				"state_code": None,
			}
		)

		with (
			patch.object(utils.frappe, "get_cached_value", return_value=address_data),
			patch.object(utils.frappe, "throw") as throw,
		):
			utils.validate_address("Legal Addr-Billing")

		throw.assert_not_called()

	def test_validate_address_uses_country_fallback(self):
		address_data = frappe._dict(
			{
				"pincode": "25020",
				"city": "San Zeno Naviglio",
				"country": "Italy",
				"country_code": None,
				"state": "Brescia",
				"state_code": None,
			}
		)

		with (
			patch.object(utils.frappe, "get_cached_value", side_effect=[address_data, "it"]),
			patch.object(utils.frappe, "throw") as throw,
		):
			utils.validate_address("Legal Addr-Billing")

		throw.assert_not_called()

	def test_validate_address_uses_readable_postal_code_label(self):
		address_data = frappe._dict(
			{
				"pincode": None,
				"city": "San Zeno Naviglio",
				"country": "Italy",
				"country_code": "IT",
			}
		)

		with (
			patch.object(utils.frappe, "get_cached_value", return_value=address_data),
			patch.object(utils.frappe, "throw", side_effect=frappe.ValidationError) as throw,
		):
			with self.assertRaises(frappe.ValidationError):
				utils.validate_address("Legal Addr-Billing")

		self.assertIn("Postal Code", throw.call_args.args[0])

	def test_validate_address_requires_state_code_for_italy(self):
		address_data = frappe._dict(
			{
				"pincode": "25020",
				"city": "San Zeno Naviglio",
				"country": "Italy",
				"country_code": "IT",
				"state": None,
				"state_code": None,
			}
		)

		with (
			patch.object(utils.frappe, "get_cached_value", return_value=address_data),
			patch.object(utils.frappe, "throw", side_effect=frappe.ValidationError) as throw,
		):
			with self.assertRaises(frappe.ValidationError):
				utils.validate_address("Legal Addr-Billing")

		self.assertIn("State/Province Code", throw.call_args.args[0])

	def test_get_customer_fiscal_code_uses_tax_id_for_italian_company(self):
		customer = frappe._dict({"customer_type": "Company", "fiscal_code": None})
		self.assertEqual(
			utils.get_customer_fiscal_code(customer, "IT02697330229", "IT"),
			"02697330229",
		)

	def test_set_state_code_populates_country_code_from_country(self):
		doc = frappe._dict({"country": "Italy", "country_code": None, "state": "Brescia", "state_code": None})

		with patch.object(utils.frappe, "get_cached_value", return_value="it"):
			utils.set_state_code(doc, None)

		self.assertEqual(doc.country_code, "IT")
		self.assertEqual(doc.state_code, "BS")

	def test_set_state_code_accepts_existing_province_code(self):
		doc = frappe._dict({"country": "Italy", "country_code": "IT", "state": "TN", "state_code": None})

		utils.set_state_code(doc, None)

		self.assertEqual(doc.state_code, "TN")

	def test_prepare_payment_schedule_sets_default_payment_reference(self):
		schedule = frappe._dict()

		utils.prepare_payment_schedule([schedule], frappe._dict({"default_bank_account": None}), "ACC-SINV-2026-00001")

		self.assertEqual(schedule.payment_reference, "ACC-SINV-2026-00001")

	def test_get_progressive_name_and_number_replace_removes_all_existing_xmls(self):
		doc = frappe._dict({"doctype": "Sales Invoice", "name": "ACC-SINV-2026-00001", "company_tax_id": "IT04266880980"})
		attachments = [
			SimpleNamespace(name="newer", file_name="IT04266880980_00005392f7f.xml"),
			SimpleNamespace(name="older", file_name="IT04266880980_00002.xml"),
		]

		with (
			patch.object(utils, "get_e_invoice_attachments", return_value=attachments),
			patch.object(utils, "remove_file") as remove_file,
		):
			progressive_name, progressive_number = utils.get_progressive_name_and_number(doc, replace=True)

		self.assertEqual(progressive_name, "IT04266880980_00005")
		self.assertEqual(progressive_number, "00005")
		self.assertEqual(remove_file.call_count, 2)

	def test_get_e_invoice_attachments_uses_invoice_names_in_filter(self):
		invoice = frappe._dict({"name": "ACC-SINV-2026-00001", "company_tax_id": "04266880980"})

		with patch.object(utils.frappe, "get_all", return_value=[] ) as get_all:
			utils.get_e_invoice_attachments(invoice)

		self.assertEqual(
			get_all.call_args.kwargs["filters"]["attached_to_name"],
			("in", ["ACC-SINV-2026-00001"]),
		)
