import json
from collections import defaultdict

import frappe
from erpnext.accounts.doctype.sales_invoice.sales_invoice import make_sales_return
from frappe.utils import cstr

from ecommerce_integrations.shopify.constants import (
	ORDER_ID_FIELD,
	SETTING_DOCTYPE,
)
from ecommerce_integrations.shopify.utils import create_shopify_log
from ecommerce_integrations.shopify.product import get_item_code
from ecommerce_integrations.shopify.invoice import make_payment_entry_against_sales_invoice

test = {
	"admin_graphql_api_id": "gid://shopify/Refund/1022629085464",
	"created_at": "2025-11-10T09:58:21-06:00",
	"duties": [],
	"id": 1022629085464,
	"note": "",
	"order_adjustments": [
		{
			"amount": "277.61",
			"amount_set": {
				"presentment_money": {
					"amount": "277.61",
					"currency_code": "CAD"
				},
				"shop_money": {
					"amount": "277.61",
					"currency_code": "CAD"
				}
			},
			"id": 347964244248,
			"kind": "refund_discrepancy",
			"order_id": 6749596057880,
			"reason": "Refund discrepancy",
			"refund_id": 1022629085464,
			"tax_amount": "0.00",
			"tax_amount_set": {
				"presentment_money": {
					"amount": "0.00",
					"currency_code": "CAD"
				},
				"shop_money": {
					"amount": "0.00",
					"currency_code": "CAD"
				}
			}
		}
	],
	"order_id": 6749596057880,
	"processed_at": "2025-11-10T09:58:21-06:00",
	"refund_line_items": [
		{
			"id": 653531316504,
			"line_item": {
				"admin_graphql_api_id": "gid://shopify/LineItem/16353368736024",
				"discount_allocations": [],
				"duties": [],
				"fulfillable_quantity": 0,
				"fulfillment_service": "manual",
				"fulfillment_status": None,
				"gift_card": False,
				"grams": 0,
				"id": 16353368736024,
				"name": "Sundance Spas Jacuzzi DCU:PIN LIGHT DAISY CHAIN (P/N: 6560-555)  SHIPS IN 8 TO 10 WEEKS",
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
				"price": "245.67",
				"price_set": {
					"presentment_money": {
						"amount": "245.67",
						"currency_code": "CAD"
					},
					"shop_money": {
						"amount": "245.67",
						"currency_code": "CAD"
					}
				},
				"product_exists": True,
				"product_id": 4545493434439,
				"properties": [],
				"quantity": 1,
				"requires_shipping": True,
				"sku": "893050101",
				"tax_lines": [
					{
						"channel_liable": None,
						"price": "31.94",
						"price_set": {
							"presentment_money": {
								"amount": "31.94",
								"currency_code": "CAD"
							},
							"shop_money": {
								"amount": "31.94",
								"currency_code": "CAD"
							}
						},
						"rate": 0.13,
						"title": "HST"
					}
				],
				"taxable": True,
				"title": "Sundance Spas Jacuzzi DCU:PIN LIGHT DAISY CHAIN (P/N: 6560-555)  SHIPS IN 8 TO 10 WEEKS",
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
				"variant_id": 31939875864647,
				"variant_inventory_management": "shopify",
				"variant_title": None,
				"vendor": "Sundance"
			},
			"line_item_id": 16353368736024,
			"location_id": 5791776832,
			"quantity": 1,
			"restock_type": "cancel",
			"subtotal": 245.67,
			"subtotal_set": {
				"presentment_money": {
					"amount": "245.67",
					"currency_code": "CAD"
				},
				"shop_money": {
					"amount": "245.67",
					"currency_code": "CAD"
				}
			},
			"total_tax": 31.94,
			"total_tax_set": {
				"presentment_money": {
					"amount": "31.94",
					"currency_code": "CAD"
				},
				"shop_money": {
					"amount": "31.94",
					"currency_code": "CAD"
				}
			}
		}
	],
	"refund_shipping_lines": [],
	"restock": True,
	"return": None,
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
			"admin_graphql_api_id": "gid://shopify/OrderTransaction/8213622358296",
			"amount": "277.61",
			"amount_rounding": None,
			"authorization": "ch_3SQwAkBT1TUnk3bS2b2B1ECA",
			"created_at": "2025-11-10T09:58:20-06:00",
			"currency": "CAD",
			"device_id": None,
			"error_code": None,
			"gateway": "shopify_payments",
			"id": 8213622358296,
			"kind": "refund",
			"location_id": None,
			"manual_payment_gateway": False,
			"message": None,
			"order_id": 6749596057880,
			"parent_id": 8207462269208,
			"payment_details": {
				"avs_result_code": "Y",
				"buyer_action_info": None,
				"credit_card_bin": "452070",
				"credit_card_company": "Visa",
				"credit_card_expiration_month": 4,
				"credit_card_expiration_year": 2028,
				"credit_card_name": "Dana Boucher",
				"credit_card_number": "\u2022\u2022\u2022\u2022 \u2022\u2022\u2022\u2022 \u2022\u2022\u2022\u2022 8233",
				"credit_card_wallet": None,
				"cvv_result_code": "M",
				"payment_method_name": "visa"
			},
			"payment_id": "zQaKW1xmo6hTpJjtEmEe0X1if",
			"payments_refund_attributes": {
				"acquirer_reference_number": None,
				"status": "deferred"
			},
			"processed_at": "2025-11-10T09:58:20-06:00",
			"receipt": {
				"refund_id": "zQaKW1xmo6hTpJjtEmEe0X1if"
			},
			"source_name": "1830279",
			"status": "pending",
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
			"user_id": 34727460928
		}
	],
	"user_id": 34727460928
}

@frappe.whitelist(allow_guest=True)
def prepare_credit_note(payload=None, request_id=None):
	if payload is None:
		payload = test
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

		return_items = {}
		for line in refund.get("refund_line_items"):
			total_discount = 0.0
			discount_per_item = 0.0
			discounts: list = line.get("line_item").get("discount_allocations", [])

			if discounts.__len__() > 0:
				first_discount: dict = discounts[0]
				total_discount: float = float(first_discount.get("amount"))
				discount_per_item: float = total_discount / int(line.get("quantity"))

			return_items[get_item_code(line.get("line_item"))] = {
				"qty": line.get("quantity"),
				"price": float(line.get("line_item").get("price")) - total_discount,
				"rate": float(line.get("line_item").get("price")) - discount_per_item,
			}

		_handle_partial_returns(credit_note, return_items)

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


def _handle_partial_returns(credit_note, returned_items: dict) -> None:
	""" Remove non-returned item from credit note and update taxes """
	# remove non-returned items
	credit_note.items = [
		item for item in credit_note.items if item.item_code in returned_items
	]
	for item in credit_note.items:
		item.qty = -1 * returned_items[item.item_code]["qty"]
		item.amount = returned_items[item.item_code]["price"] * item.qty
		item.rate = returned_items[item.item_code]["rate"]

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
			return_percent = returned_qty_map.get(item_code, 0.0) / returned_qty_map.get(item_code, 1.0)
			tax_distribution[1] *= return_percent
			new_tax_amt += tax_distribution[1]

		tax.tax_amount = new_tax_amt
		tax.item_wise_tax_detail = json.dumps(item_wise_tax_detail)
