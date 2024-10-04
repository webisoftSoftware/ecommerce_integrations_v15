import json
from collections import defaultdict

import frappe
from erpnext.accounts.doctype.sales_invoice.sales_invoice import make_sales_return
from frappe.utils import cint, cstr, getdate, nowdate
from typing import DefaultDict, List

from ecommerce_integrations.shopify.constants import (
	ORDER_ID_FIELD,
	ORDER_NUMBER_FIELD,
	SETTING_DOCTYPE,
)
from ecommerce_integrations.shopify.utils import create_shopify_log
from ecommerce_integrations.shopify.product import get_item_code
from ecommerce_integrations.shopify.invoice import make_payment_entry_against_sales_invoice

payload = {
	"admin_graphql_api_id": "gid://shopify/Refund/975224602904",
	"created_at": "2024-09-09T12:36:31-05:00",
	"duties": [],
	"id": 975224602904,
	"note": None,
	"order_adjustments": [],
	"order_id": 6022498320664,
	"processed_at": "2024-09-09T12:36:31-05:00",
	"refund_line_items": [
		{
			"id": 587955536152,
			"line_item": {
				"admin_graphql_api_id": "gid://shopify/LineItem/15075349889304",
				"discount_allocations": [
					{
						"amount": "15.99",
						"amount_set": {
							"presentment_money": {
								"amount": "15.99",
								"currency_code": "CAD"
							},
							"shop_money": {
								"amount": "15.99",
								"currency_code": "CAD"
							}
						},
						"discount_application_index": 0
					}
				],
				"duties": [],
				"fulfillable_quantity": 0,
				"fulfillment_service": "manual",
				"fulfillment_status": "fulfilled",
				"gift_card": False,
				"grams": 0,
				"id": 15075349889304,
				"name": "Dazzle Pristiva Premium Salt (18.1kg) (P/N: PRC35120)",
				"origin_location": {
					"address1": "1065 Dugald Road",
					"address2": "",
					"city": "Winnipeg",
					"country_code": "CA",
					"id": 806176948288,
					"name": "1065 Dugald Road",
					"province_code": "MB",
					"zip": "R2J 0G8"
				},
				"price": "39.99",
				"price_set": {
					"presentment_money": {
						"amount": "39.99",
						"currency_code": "CAD"
					},
					"shop_money": {
						"amount": "39.99",
						"currency_code": "CAD"
					}
				},
				"product_exists": True,
				"product_id": 2621168156736,
				"properties": [],
				"quantity": 4,
				"requires_shipping": True,
				"sku": "PRC35120",
				"tax_lines": [
					{
						"channel_liable": None,
						"price": "7.20",
						"price_set": {
							"presentment_money": {
								"amount": "7.20",
								"currency_code": "CAD"
							},
							"shop_money": {
								"amount": "7.20",
								"currency_code": "CAD"
							}
						},
						"rate": 0.05,
						"title": "GST"
					},
					{
						"channel_liable": None,
						"price": "10.08",
						"price_set": {
							"presentment_money": {
								"amount": "10.08",
								"currency_code": "CAD"
							},
							"shop_money": {
								"amount": "10.08",
								"currency_code": "CAD"
							}
						},
						"rate": 0.07,
						"title": "RST"
					}
				],
				"taxable": True,
				"title": "Dazzle Pristiva Premium Salt (18.1kg) (P/N: PRC35120)",
				"total_discount": "0.00",
				"total_discount_set": {
					"presentment_money": {
						"amount": "0.00",
						"currency_code": "CAD"
					},
					"shop_money": {
						"amount": "0.00",
						"currency_code": "CAD"
					}
				},
				"variant_id": 24199708868672,
				"variant_inventory_management": "shopify",
				"variant_title": None,
				"vendor": "Dazzle"
			},
			"line_item_id": 15075349889304,
			"location_id": 5791776832,
			"quantity": 4,
			"restock_type": "return",
			"subtotal": 143.97,
			"subtotal_set": {
				"presentment_money": {
					"amount": "143.97",
					"currency_code": "CAD"
				},
				"shop_money": {
					"amount": "143.97",
					"currency_code": "CAD"
				}
			},
			"total_tax": 17.28,
			"total_tax_set": {
				"presentment_money": {
					"amount": "17.28",
					"currency_code": "CAD"
				},
				"shop_money": {
					"amount": "17.28",
					"currency_code": "CAD"
				}
			}
		}
	],
	"restock": True,
	"return": {
		"admin_graphql_api_id": "gid://shopify/Return/6701154584",
		"id": 6701154584
	},
	"total_duties_set": {
		"presentment_money": {
			"amount": "0.00",
			"currency_code": "CAD"
		},
		"shop_money": {
			"amount": "0.00",
			"currency_code": "CAD"
		}
	},
	"transactions": [
		{
			"admin_graphql_api_id": "gid://shopify/OrderTransaction/7314461393176",
			"amount": "161.25",
			"authorization": "re_3PxBPhBT1TUnk3bS0MV9yKLh",
			"created_at": "2024-09-09T12:36:29-05:00",
			"currency": "CAD",
			"device_id": 3292135495,
			"error_code": None,
			"gateway": "shopify_payments",
			"id": 7314461393176,
			"kind": "refund",
			"location_id": 5791776832,
			"message": "Transaction approved",
			"order_id": 6022498320664,
			"parent_id": 7314460967192,
			"payment_details": {
				"avs_result_code": None,
				"buyer_action_info": None,
				"credit_card_bin": "552490",
				"credit_card_company": "Mastercard",
				"credit_card_expiration_month": 10,
				"credit_card_expiration_year": 2025,
				"credit_card_name": "DAVID/MELISSA",
				"credit_card_number": "\u2022\u2022\u2022\u2022 \u2022\u2022\u2022\u2022 \u2022\u2022\u2022\u2022 9775",
				"credit_card_wallet": None,
				"cvv_result_code": None,
				"payment_method_name": "master"
			},
			"payment_id": "#194467.3",
			"payments_refund_attributes": {
				"acquirer_reference_number": None,
				"status": "success"
			},
			"processed_at": "2024-09-09T12:36:30-05:00",
			"receipt": {
				"amount": 16125,
				"balance_transaction": {
					"exchange_rate": None,
					"id": "txn_3PxBPhBT1TUnk3bS0rPpcbDv",
					"object": "balance_transaction"
				},
				"charge": {
					"amount": 35273,
					"application_fee": "fee_1PxBVjBT1TUnk3bSPyul07TI",
					"authorization_code": "00767J",
					"balance_transaction": "txn_3PxBPhBT1TUnk3bS0rFVIyi2",
					"captured": True,
					"created": 1725903024,
					"currency": "cad",
					"failure_code": None,
					"failure_message": None,
					"fraud_details": {},
					"id": "ch_3PxBPhBT1TUnk3bS0xjQud5d",
					"livemode": True,
					"metadata": {
						"card_source": "stripe_terminal",
						"checkout_session_identifier": "DE6A7373-5568-46E0-BEF6-2B39A7B8E9A5",
						"location_id": "5791776832",
						"payment_device_name": "WisePad 3 Reader",
						"payment_device_serial": "WPC323225037517",
						"point_of_sale_device_id": "3292135495",
						"shop_id": "1703608384",
						"unique_token": "40F886ECFC594866BDCBAA2D77D399AF",
						"user_id": "109650444568"
					},
					"object": "charge",
					"outcome": {
						"network_status": "approved_by_network",
						"reason": None,
						"risk_level": "not_assessed",
						"seller_message": "Payment complete.",
						"type": "authorized"
					},
					"paid": True,
					"payment_intent": "pi_3PxBPhBT1TUnk3bS0VjZcY7r",
					"payment_method": "pm_1PxBPvBT1TUnk3bS1AaU6vG9",
					"payment_method_details": {
						"card_present": {
							"amount_authorized": 35273,
							"brand": "mastercard",
							"brand_product": "MWE",
							"capture_before": 1726075824,
							"cardholder_name": "DAVID/MELISSA",
							"country": "CA",
							"description": "World Elite MasterCard Card",
							"emv_auth_data": "8A023030910A7E14BD00DC82B3CA0012",
							"exp_month": 10,
							"exp_year": 2025,
							"fingerprint": "hldySPHHEcNAgMKl",
							"funding": "credit",
							"generated_card": None,
							"iin": "552490",
							"incremental_authorization_supported": False,
							"issuer": "ROYAL BANK OF CANADA",
							"last4": "9775",
							"network": "mastercard",
							"network_transaction_id": "MWERBLNRK0909",
							"offline": {
								"stored_at": None,
								"type": None
							},
							"overcapture_supported": False,
							"payment_account_reference": "50018VBJ4NI6ZSVA5BL4H1VUG5SP7",
							"preferred_locales": [
								"en"
							],
							"read_method": "contact_emv",
							"receipt": {
								"account_type": "credit",
								"application_cryptogram": "F692C2F753EAFAB3",
								"application_preferred_name": "MASTERCARD",
								"authorization_code": "00767J",
								"authorization_response_code": "3030",
								"cardholder_verification_method": "offline_pin",
								"dedicated_file_name": "A0000000041010",
								"terminal_verification_results": "0000008000",
								"transaction_status_information": "E800"
							}
						},
						"type": "card_present"
					},
					"refunded": False,
					"source": None,
					"status": "succeeded"
				},
				"created": 1725903389,
				"currency": "cad",
				"id": "re_3PxBPhBT1TUnk3bS0MV9yKLh",
				"metadata": {
					"order_transaction_id": "7314461393176",
					"payments_refund_id": "126839357720"
				},
				"mit_params": {},
				"object": "refund",
				"payment_method_details": {
					"card": {
						"acquirer_reference_number": None,
						"acquirer_reference_number_status": "unavailable"
					},
					"type": "card"
				},
				"reason": None,
				"status": "succeeded"
			},
			"source_name": "pos",
			"status": "success",
			"test": False,
			"total_unsettled_set": {
				"presentment_money": {
					"amount": "0.0",
					"currency": "CAD"
				},
				"shop_money": {
					"amount": "0.0",
					"currency": "CAD"
				}
			},
			"user_id": 109650444568
		}
	],
	"user_id": 109650444568
}

@frappe.whitelist()
def prepare_credit_note(request_id=None):
	refund_payload = payload
	frappe.set_user("Administrator")
	setting = frappe.get_doc(SETTING_DOCTYPE)
	frappe.flags.request_id = request_id

	try:
		sales_invoice = get_sales_invoice(cstr(refund_payload["order_id"]))
		if sales_invoice:
			make_credit_note(refund_payload, setting, sales_invoice)
			create_shopify_log(status="Success")
		else:
			create_shopify_log(status="Invalid",
							   message="Sales Invoice not found for creating Credit Note.")
	except Exception as e:
		create_shopify_log(status="Error", exception=e, rollback=True)


def make_credit_note(refund, setting, sales_invoice):
	if len(refund.get("refund_line_items")) > 0:
		credit_note = create_credit_note(sales_invoice.name, setting)

		if not refund["restock"]:
			credit_note.update_stock = 0

		return_items = defaultdict()
		for line in refund.get("refund_line_items"):
			final_price: float = handle_discounts(line)
			return_items[get_item_code(line.get("line_item"))] = {
				"qty": line.get("quantity"),
				"price": line.get("line_item").get("price"),
				"rate": line.get("line_item").get("price"),
				"final_price_with_discount": final_price
			}

		_handle_partial_returns(credit_note, return_items, sales_invoice)

		credit_note.insert(ignore_mandatory=True)
		credit_note.submit()

		# Update sales invoice amounts to prevent creation of payment entry against the whole amount.
		credit_note.grand_total = -credit_note.grand_total
		credit_note.base_grand_total = -credit_note.base_grand_total
		credit_note.base_net_total = -credit_note.base_net_total
		credit_note.base_total = -credit_note.base_total
		credit_note.base_total_taxes_and_charges = -credit_note.base_total_taxes_and_charges
		make_payment_entry_against_sales_invoice(credit_note, setting)

		difference = sales_invoice.outstanding_amount - credit_note.grand_total
		frappe.db.set_value("Sales Invoice", sales_invoice.name, "outstanding_amount",
							difference)
		sales_invoice.set_status(update=True)
		frappe.db.commit()
		return

	make_payment_entry_against_sales_invoice(sales_invoice, setting)


def create_debit_note(sales_invoice, amount, setting):
	debit_note = create_credit_note(sales_invoice.name, setting)
	debit_note.is_debit_note = 1

	original_amount = sum(
		(item.rate * item.qty) for item in debit_note.items) + debit_note.total_taxes_and_charges

	for item in debit_note.items:
		item_percent = (item.rate * item.qty) / original_amount
		item.rate = -item_percent * amount
		item.qty = 0

	for tax in debit_note.taxes:
		# reduce total value
		item_wise_tax_detail = json.loads(tax.item_wise_tax_detail)

		for item_code, tax_distribution in item_wise_tax_detail.items():
			# item_code: [rate, amount]
			if not tax_distribution[1]:
				# Ignore 0 values
				continue
			return_percent = amount / original_amount
			tax_distribution[0] *= return_percent
			tax_distribution[1] *= return_percent

		tax.tax_amount *= amount / original_amount
		tax.item_wise_tax_detail = json.dumps(item_wise_tax_detail)
	return debit_note


def create_credit_note(invoice_name, setting):
	credit_note = make_sales_return(invoice_name)

	credit_note.taxes_category = "Ecommerce Integrations - Ignore"

	for item in credit_note.items:
		item.warehouse = setting.warehouse or item.warehouse

	for tax in credit_note.taxes:
		tax.item_wise_tax_detail = json.loads(tax.item_wise_tax_detail)
		for item, tax_distribution in tax.item_wise_tax_detail.items():
			tax_distribution[1] *= -1
			tax_distribution[0] *= -1
		tax.item_wise_tax_detail = json.dumps(tax.item_wise_tax_detail)

	return credit_note


def get_sales_invoice(order_id):
	"""Get ERPNext sales invoice using shopify order id."""
	sales_invoice = frappe.db.get_value("Sales Invoice", filters={ORDER_ID_FIELD: order_id})
	if sales_invoice:
		return frappe.get_doc("Sales Invoice", sales_invoice)


def _handle_partial_returns(credit_note, returned_items: List[str], sales_invoice) -> None:
	""" Remove non-returned item from credit note and update taxes """
	item_code_to_qty_map = defaultdict(float)
	for item in sales_invoice.items:
		item_code_to_qty_map[item.item_code] -= item.qty

	# remove non-returned items
	credit_note.items = [
		item for item in credit_note.items if item.item_code in returned_items
	]
	for item in credit_note.items:
		item.qty = -1 * returned_items[item.item_code]["qty"]
		item.amount = float(returned_items[item.item_code]["price"]) * item.qty
		item.rate = float(returned_items[item.item_code]["rate"])

	returned_qty_map = defaultdict(float)
	for item in credit_note.items:
		returned_qty_map[item.item_code] += item.qty

	for tax in credit_note.taxes:
		# reduce total value
		item_wise_tax_detail = json.loads(tax.item_wise_tax_detail)
		new_tax_amt = 0.0

		for item_code, tax_distribution in item_wise_tax_detail.items():
			# item_code: [rate, amount]
			if not tax_distribution[0]:
				# Ignore 0 values
				continue
			return_percent = returned_qty_map.get(item_code, 0.0) / item_code_to_qty_map.get(
				item_code)
			tax_distribution[1] *= return_percent
			new_tax_amt += tax_distribution[1]

		tax.tax_amount = new_tax_amt
		tax.item_wise_tax_detail = json.dumps(item_wise_tax_detail)


def handle_discounts(line: dict) -> float:
	if (line.get("line_item").get("discount_allocations") and not
	line.get("line_item").get("discount_allocations").__len__() > 0):
		return (float(line.get("line_item").get("price")) -
				float(line.get("line_item").get("discount_allocations").get("amount")))
	return float(line.get("line_item").get("price")) * float(line.get("quantity"))
