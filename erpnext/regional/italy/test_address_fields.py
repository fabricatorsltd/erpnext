import unittest
from unittest.mock import patch

import frappe

from erpnext.regional.italy import utils


class TestItalyAddressFields(unittest.TestCase):
	def test_validate_address_uses_country_fallback(self):
		address_data = frappe._dict(
			{
				"pincode": "25020",
				"city": "San Zeno Naviglio",
				"country": "Italy",
				"country_code": None,
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

	def test_set_state_code_populates_country_code_from_country(self):
		doc = frappe._dict({"country": "Italy", "country_code": None, "state": "Brescia", "state_code": None})

		with patch.object(utils.frappe, "get_cached_value", return_value="it"):
			utils.set_state_code(doc, None)

		self.assertEqual(doc.country_code, "IT")
		self.assertEqual(doc.state_code, "BS")
