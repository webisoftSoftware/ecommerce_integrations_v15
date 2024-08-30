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

payload = refund = {
	"admin_graphql_api_id": "gid://shopify/Refund/974007468312",
	"created_at": "2024-08-21T12:57:12-05:00",
	"duties": [],
	"id": 974007468312,
	"note": "Order canceled",
	"order_adjustments": [],
	"order_id": 5992405729560,
	"processed_at": "2024-08-21T12:57:12-05:00",
	"refund_line_items": [
		{
			"id": 586381361432,
			"line_item": {
				"admin_graphql_api_id": "gid://shopify/LineItem/15020224119064",
				"discount_allocations": [
					{
						"amount": "19.99",
						"amount_set": {
							"presentment_money": {
								"amount": "19.99",
								"currency_code": "CAD"
							},
							"shop_money": {
								"amount": "19.99",
								"currency_code": "CAD"
							}
						},
						"discount_application_index": 0
					}
				],
				"duties": [],
				"fulfillable_quantity": 0,
				"fulfillment_service": "manual",
				"fulfillment_status": None,
				"gift_card": False,
				"grams": 0,
				"id": 15020224119064,
				"name": "BioGuard Balance Pak\u00ae 100 (1kg) (P/N: 4506)",
				"price": "19.99",
				"price_set": {
					"presentment_money": {
						"amount": "19.99",
						"currency_code": "CAD"
					},
					"shop_money": {
						"amount": "19.99",
						"currency_code": "CAD"
					}
				},
				"product_exists": True,
				"product_id": 2621069197376,
				"properties": [],
				"quantity": 1,
				"requires_shipping": True,
				"sku": "4506",
				"tax_lines": [
					{
						"channel_liable": False,
						"price": "0.00",
						"price_set": {
							"presentment_money": {
								"amount": "0.00",
								"currency_code": "CAD"
							},
							"shop_money": {
								"amount": "0.00",
								"currency_code": "CAD"
							}
						},
						"rate": 0.05,
						"title": "GST"
					},
					{
						"channel_liable": False,
						"price": "0.00",
						"price_set": {
							"presentment_money": {
								"amount": "0.00",
								"currency_code": "CAD"
							},
							"shop_money": {
								"amount": "0.00",
								"currency_code": "CAD"
							}
						},
						"rate": 0.07,
						"title": "RST"
					}
				],
				"taxable": True,
				"title": "BioGuard Balance Pak\u00ae 100 (1kg) (P/N: 4506)",
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
				"variant_id": 24198955991104,
				"variant_inventory_management": "shopify",
				"variant_title": None,
				"vendor": "BioGuard"
			},
			"line_item_id": 15020224119064,
			"location_id": 5791776832,
			"quantity": 1,
			"restock_type": "cancel",
			"subtotal": 0.0,
			"subtotal_set": {
				"presentment_money": {
					"amount": "0.00",
					"currency_code": "CAD"
				},
				"shop_money": {
					"amount": "0.00",
					"currency_code": "CAD"
				}
			},
			"total_tax": 0.0,
			"total_tax_set": {
				"presentment_money": {
					"amount": "0.00",
					"currency_code": "CAD"
				},
				"shop_money": {
					"amount": "0.00",
					"currency_code": "CAD"
				}
			}
		},
		{
			"id": 586381394200,
			"line_item": {
				"admin_graphql_api_id": "gid://shopify/LineItem/15020224151832",
				"discount_allocations": [
					{
						"amount": "114.99",
						"amount_set": {
							"presentment_money": {
								"amount": "114.99",
								"currency_code": "CAD"
							},
							"shop_money": {
								"amount": "114.99",
								"currency_code": "CAD"
							}
						},
						"discount_application_index": 0
					}
				],
				"duties": [],
				"fulfillable_quantity": 0,
				"fulfillment_service": "manual",
				"fulfillment_status": None,
				"gift_card": False,
				"grams": 0,
				"id": 15020224151832,
				"name": "BioGuard Balance Pak\u00ae 100 (15kg) (P/N: 4509)",
				"price": "114.99",
				"price_set": {
					"presentment_money": {
						"amount": "114.99",
						"currency_code": "CAD"
					},
					"shop_money": {
						"amount": "114.99",
						"currency_code": "CAD"
					}
				},
				"product_exists": True,
				"product_id": 2621068836928,
				"properties": [],
				"quantity": 1,
				"requires_shipping": True,
				"sku": "4509",
				"tax_lines": [
					{
						"channel_liable": False,
						"price": "0.00",
						"price_set": {
							"presentment_money": {
								"amount": "0.00",
								"currency_code": "CAD"
							},
							"shop_money": {
								"amount": "0.00",
								"currency_code": "CAD"
							}
						},
						"rate": 0.05,
						"title": "GST"
					},
					{
						"channel_liable": False,
						"price": "0.00",
						"price_set": {
							"presentment_money": {
								"amount": "0.00",
								"currency_code": "CAD"
							},
							"shop_money": {
								"amount": "0.00",
								"currency_code": "CAD"
							}
						},
						"rate": 0.07,
						"title": "RST"
					}
				],
				"taxable": True,
				"title": "BioGuard Balance Pak\u00ae 100 (15kg) (P/N: 4509)",
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
				"variant_id": 24198948814912,
				"variant_inventory_management": "shopify",
				"variant_title": None,
				"vendor": "BioGuard"
			},
			"line_item_id": 15020224151832,
			"location_id": 5791776832,
			"quantity": 1,
			"restock_type": "cancel",
			"subtotal": 0.0,
			"subtotal_set": {
				"presentment_money": {
					"amount": "0.00",
					"currency_code": "CAD"
				},
				"shop_money": {
					"amount": "0.00",
					"currency_code": "CAD"
				}
			},
			"total_tax": 0.0,
			"total_tax_set": {
				"presentment_money": {
					"amount": "0.00",
					"currency_code": "CAD"
				},
				"shop_money": {
					"amount": "0.00",
					"currency_code": "CAD"
				}
			}
		},
		{
			"id": 586381426968,
			"line_item": {
				"admin_graphql_api_id": "gid://shopify/LineItem/15020224184600",
				"discount_allocations": [
					{
						"amount": "19.99",
						"amount_set": {
							"presentment_money": {
								"amount": "19.99",
								"currency_code": "CAD"
							},
							"shop_money": {
								"amount": "19.99",
								"currency_code": "CAD"
							}
						},
						"discount_application_index": 0
					}
				],
				"duties": [],
				"fulfillable_quantity": 0,
				"fulfillment_service": "manual",
				"fulfillment_status": None,
				"gift_card": False,
				"grams": 0,
				"id": 15020224184600,
				"name": "BioGuard Lo 'N Slo\u00ae (1.25kg) (P/N: 4101)",
				"price": "19.99",
				"price_set": {
					"presentment_money": {
						"amount": "19.99",
						"currency_code": "CAD"
					},
					"shop_money": {
						"amount": "19.99",
						"currency_code": "CAD"
					}
				},
				"product_exists": True,
				"product_id": 2621078667328,
				"properties": [],
				"quantity": 1,
				"requires_shipping": True,
				"sku": "4101",
				"tax_lines": [
					{
						"channel_liable": False,
						"price": "0.00",
						"price_set": {
							"presentment_money": {
								"amount": "0.00",
								"currency_code": "CAD"
							},
							"shop_money": {
								"amount": "0.00",
								"currency_code": "CAD"
							}
						},
						"rate": 0.05,
						"title": "GST"
					},
					{
						"channel_liable": False,
						"price": "0.00",
						"price_set": {
							"presentment_money": {
								"amount": "0.00",
								"currency_code": "CAD"
							},
							"shop_money": {
								"amount": "0.00",
								"currency_code": "CAD"
							}
						},
						"rate": 0.07,
						"title": "RST"
					}
				],
				"taxable": True,
				"title": "BioGuard Lo 'N Slo\u00ae (1.25kg) (P/N: 4101)",
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
				"variant_id": 24199033454656,
				"variant_inventory_management": "shopify",
				"variant_title": None,
				"vendor": "BioGuard"
			},
			"line_item_id": 15020224184600,
			"location_id": 5791776832,
			"quantity": 1,
			"restock_type": "cancel",
			"subtotal": 0.0,
			"subtotal_set": {
				"presentment_money": {
					"amount": "0.00",
					"currency_code": "CAD"
				},
				"shop_money": {
					"amount": "0.00",
					"currency_code": "CAD"
				}
			},
			"total_tax": 0.0,
			"total_tax_set": {
				"presentment_money": {
					"amount": "0.00",
					"currency_code": "CAD"
				},
				"shop_money": {
					"amount": "0.00",
					"currency_code": "CAD"
				}
			}
		},
		{
			"id": 586381459736,
			"line_item": {
				"admin_graphql_api_id": "gid://shopify/LineItem/15020224217368",
				"discount_allocations": [
					{
						"amount": "99.99",
						"amount_set": {
							"presentment_money": {
								"amount": "99.99",
								"currency_code": "CAD"
							},
							"shop_money": {
								"amount": "99.99",
								"currency_code": "CAD"
							}
						},
						"discount_application_index": 0
					}
				],
				"duties": [],
				"fulfillable_quantity": 0,
				"fulfillment_service": "manual",
				"fulfillment_status": None,
				"gift_card": False,
				"grams": 0,
				"id": 15020224217368,
				"name": "BioGuard Stabilizer 100\u2122 (2.25kg) (P/N: 1303)",
				"price": "99.99",
				"price_set": {
					"presentment_money": {
						"amount": "99.99",
						"currency_code": "CAD"
					},
					"shop_money": {
						"amount": "99.99",
						"currency_code": "CAD"
					}
				},
				"product_exists": True,
				"product_id": 2621099966528,
				"properties": [],
				"quantity": 1,
				"requires_shipping": True,
				"sku": "1303",
				"tax_lines": [
					{
						"channel_liable": False,
						"price": "0.00",
						"price_set": {
							"presentment_money": {
								"amount": "0.00",
								"currency_code": "CAD"
							},
							"shop_money": {
								"amount": "0.00",
								"currency_code": "CAD"
							}
						},
						"rate": 0.05,
						"title": "GST"
					},
					{
						"channel_liable": False,
						"price": "0.00",
						"price_set": {
							"presentment_money": {
								"amount": "0.00",
								"currency_code": "CAD"
							},
							"shop_money": {
								"amount": "0.00",
								"currency_code": "CAD"
							}
						},
						"rate": 0.07,
						"title": "RST"
					}
				],
				"taxable": True,
				"title": "BioGuard Stabilizer 100\u2122 (2.25kg) (P/N: 1303)",
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
				"variant_id": 24199177076800,
				"variant_inventory_management": "shopify",
				"variant_title": None,
				"vendor": "BioGuard"
			},
			"line_item_id": 15020224217368,
			"location_id": 5791776832,
			"quantity": 1,
			"restock_type": "cancel",
			"subtotal": 0.0,
			"subtotal_set": {
				"presentment_money": {
					"amount": "0.00",
					"currency_code": "CAD"
				},
				"shop_money": {
					"amount": "0.00",
					"currency_code": "CAD"
				}
			},
			"total_tax": 0.0,
			"total_tax_set": {
				"presentment_money": {
					"amount": "0.00",
					"currency_code": "CAD"
				},
				"shop_money": {
					"amount": "0.00",
					"currency_code": "CAD"
				}
			}
		},
		{
			"id": 586381492504,
			"line_item": {
				"admin_graphql_api_id": "gid://shopify/LineItem/15020224250136",
				"discount_allocations": [
					{
						"amount": "69.98",
						"amount_set": {
							"presentment_money": {
								"amount": "69.98",
								"currency_code": "CAD"
							},
							"shop_money": {
								"amount": "69.98",
								"currency_code": "CAD"
							}
						},
						"discount_application_index": 0
					}
				],
				"duties": [],
				"fulfillable_quantity": 0,
				"fulfillment_service": "manual",
				"fulfillment_status": None,
				"gift_card": False,
				"grams": 0,
				"id": 15020224250136,
				"name": "BioGuard Balance Pak\u00ae 300 (2.5kg) (P/N: 4540)",
				"price": "34.99",
				"price_set": {
					"presentment_money": {
						"amount": "34.99",
						"currency_code": "CAD"
					},
					"shop_money": {
						"amount": "34.99",
						"currency_code": "CAD"
					}
				},
				"product_exists": True,
				"product_id": 2621070770240,
				"properties": [],
				"quantity": 2,
				"requires_shipping": True,
				"sku": "4540",
				"tax_lines": [
					{
						"channel_liable": False,
						"price": "0.00",
						"price_set": {
							"presentment_money": {
								"amount": "0.00",
								"currency_code": "CAD"
							},
							"shop_money": {
								"amount": "0.00",
								"currency_code": "CAD"
							}
						},
						"rate": 0.05,
						"title": "GST"
					},
					{
						"channel_liable": False,
						"price": "0.00",
						"price_set": {
							"presentment_money": {
								"amount": "0.00",
								"currency_code": "CAD"
							},
							"shop_money": {
								"amount": "0.00",
								"currency_code": "CAD"
							}
						},
						"rate": 0.07,
						"title": "RST"
					}
				],
				"taxable": True,
				"title": "BioGuard Balance Pak\u00ae 300 (2.5kg) (P/N: 4540)",
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
				"variant_id": 24198979256384,
				"variant_inventory_management": "shopify",
				"variant_title": None,
				"vendor": "BioGuard"
			},
			"line_item_id": 15020224250136,
			"location_id": 5791776832,
			"quantity": 2,
			"restock_type": "cancel",
			"subtotal": 0.0,
			"subtotal_set": {
				"presentment_money": {
					"amount": "0.00",
					"currency_code": "CAD"
				},
				"shop_money": {
					"amount": "0.00",
					"currency_code": "CAD"
				}
			},
			"total_tax": 0.0,
			"total_tax_set": {
				"presentment_money": {
					"amount": "0.00",
					"currency_code": "CAD"
				},
				"shop_money": {
					"amount": "0.00",
					"currency_code": "CAD"
				}
			}
		},
		{
			"id": 586381525272,
			"line_item": {
				"admin_graphql_api_id": "gid://shopify/LineItem/15020224282904",
				"discount_allocations": [
					{
						"amount": "39.98",
						"amount_set": {
							"presentment_money": {
								"amount": "39.98",
								"currency_code": "CAD"
							},
							"shop_money": {
								"amount": "39.98",
								"currency_code": "CAD"
							}
						},
						"discount_application_index": 0
					}
				],
				"duties": [],
				"fulfillable_quantity": 0,
				"fulfillment_service": "manual",
				"fulfillment_status": None,
				"gift_card": False,
				"grams": 0,
				"id": 15020224282904,
				"name": "BioGuard Smart Shock\u00ae (400gm Bags Only) (P/N: 2450)",
				"price": "19.99",
				"price_set": {
					"presentment_money": {
						"amount": "19.99",
						"currency_code": "CAD"
					},
					"shop_money": {
						"amount": "19.99",
						"currency_code": "CAD"
					}
				},
				"product_exists": True,
				"product_id": 2621097410624,
				"properties": [],
				"quantity": 2,
				"requires_shipping": True,
				"sku": "2450",
				"tax_lines": [
					{
						"channel_liable": False,
						"price": "0.00",
						"price_set": {
							"presentment_money": {
								"amount": "0.00",
								"currency_code": "CAD"
							},
							"shop_money": {
								"amount": "0.00",
								"currency_code": "CAD"
							}
						},
						"rate": 0.05,
						"title": "GST"
					},
					{
						"channel_liable": False,
						"price": "0.00",
						"price_set": {
							"presentment_money": {
								"amount": "0.00",
								"currency_code": "CAD"
							},
							"shop_money": {
								"amount": "0.00",
							},
							"rate": 0.07,
							"title": "RST"
						}
					}
				],
				"taxable": True,
				"title": "BioGuard Smart Shock\u00ae (400gm Bags Only) (P/N: 2450)",
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
				"variant_id": 24199155777600,
				"variant_inventory_management": "shopify",
				"variant_title": None,
				"vendor": "BioGuard"
			},
			"line_item_id": 15020224282904,
			"location_id": 5791776832,
			"quantity": 2,
			"restock_type": "cancel",
			"subtotal": 0.0,
			"subtotal_set": {
				"presentment_money": {
					"amount": "0.00",
					"currency_code": "CAD"
				},
				"shop_money": {
					"amount": "0.00",
					"currency_code": "CAD"
				}
			},
			"total_tax": 0.0,
			"total_tax_set": {
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
	"transactions": [],
	"user_id": 34730967104
}

@frappe.whitelist(allow_guest=True)
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
			return_items[get_item_code(line.get("line_item"))] = {
				"qty": line.get("quantity"),
				"price": line["line_item"]["price"],
				"rate": line["line_item"]["discount_allocations"][0]["amount"]
			}

		_handle_partial_returns(credit_note, return_items, sales_invoice)

		credit_note.insert(ignore_mandatory=True)
		credit_note.submit()

	if len(refund.get("order_adjustments")) > 0:
		amount = sum(
			float(adjustment.get("amount")) + float(adjustment.get("tax_amount")) for adjustment in
			refund.get("order_adjustments"))
		debit_note = create_debit_note(sales_invoice, amount, setting)
		debit_note.insert(ignore_mandatory=True)
		debit_note.submit()
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

	# Ignore taxes.
	credit_note.taxes_category = "Ecommerce Integrations - Ignore"

	for item in credit_note.items:
		item.warehouse = setting.warehouse or item.warehouse

	for tax in credit_note.taxes:
		tax.item_wise_tax_detail = json.loads(tax.item_wise_tax_detail)
		for item, tax_distribution in tax.item_wise_tax_detail.items():
			tax_distribution[1] *= 0
			tax_distribution[0] *= 0
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
		item.amount = -1.0 * float(returned_items[item.item_code]["price"])
		item.rate = float(returned_items[item.item_code]["rate"]) / (-item.qty)

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
