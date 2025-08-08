# Copyright (c) 2025, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):

	columns = get_columns()
	data = get_data(filters if filters else {})

	return columns, data

def get_columns():
	"""Define the columns for the report"""
	return [
		{
			"label": _("Document Type"),
			"fieldname": "document_type",
			"fieldtype": "Select",
			"options": " \nSales Invoice\nDelivery Note\nPayment Entry",
			"width": 120
		},
		{
			"label": _("Document No"),
			"fieldname": "document_no",
			"fieldtype": "Dynamic Link",
			"options": "document_type",
			"width": 200
		},
		{
			"label": _("Posting Date"),
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"width": 120
		},
		{
			"label": _("Party"),
			"fieldname": "party",
			"fieldtype": "Link",
			"options": "Customer",
			"width": 150
		},
		{
			"label": _("Item Code"),
			"fieldname": "item_code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 120
		},
		{
			"label": _("Income Account"),
			"fieldname": "income_account",
			"fieldtype": "Link",
			"options": "Account",
			"width": 70
		},
		{
			"label": _("Expense Account"),
			"fieldname": "expense_account",
			"fieldtype": "Link",
			"options": "Account",
			"width": 70
		},
		{
			"label": _("Paid To"),
			"fieldname": "paid_to",
			"fieldtype": "Link",
			"options": "Account",
			"width": 70
		},
		{
			"label": _("Paid From"),
			"fieldname": "paid_from",
			"fieldtype": "Link",
			"options": "Account",
			"width": 70
		},
		{
			"label": _("Sales Parts & Service Pool"),
			"fieldname": "account_4320",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("Sales Parts & Service Spa"),
			"fieldname": "account_4322",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("Cost of Goods"),
			"fieldname": "account_5001",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("Qty"),
			"fieldname": "qty",
			"fieldtype": "Float",
			"width": 80
		},
		{
			"label": _("Rate"),
			"fieldname": "rate",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("Amount"),
			"fieldname": "amount",
			"fieldtype": "Currency",
			"width": 100
		},
	]


def get_data(filters):
	"""Get the data for the report by combining invoices, delivery notes, and payment entries"""
	data = []

	document_type = filters.get("document_type")

	# If no document type specified, get all
	if not document_type:
		# Get all data types
		invoice_data = get_sales_invoice_data(filters)
		data.extend(invoice_data)

		delivery_note_data = get_delivery_note_data(filters)
		data.extend(delivery_note_data)

		payment_entry_data = get_payment_entry_data(filters)
		data.extend(payment_entry_data)

	# If specific document type is selected, get only that type
	elif document_type == "Sales Invoice":
		invoice_data = get_sales_invoice_data(filters)
		data.extend(invoice_data)

	elif document_type == "Delivery Note":
		delivery_note_data = get_delivery_note_data(filters)
		data.extend(delivery_note_data)

	elif document_type == "Payment Entry":
		payment_entry_data = get_payment_entry_data(filters)
		data.extend(payment_entry_data)

	return data


def get_sales_invoice_data(filters):
	"""Get Sales Invoice data with item details"""
	conditions = get_conditions(filters, "Sales Invoice")

	query = f"""
        SELECT
            'Sales Invoice' as document_type,
            si.name as document_no,
            si.posting_date,
            si.customer as party,
            sii.item_code,
            sii.income_account,
            sii.expense_account,
            CASE
                WHEN sii.income_account LIKE '4320 - Sales - Parts & service - Pool service - A' THEN sii.base_net_amount
                ELSE 0
            END as account_4320,
            CASE
                WHEN sii.income_account LIKE '4322 - Sales - Parts & service - Spa service - A' THEN sii.base_net_amount
                ELSE 0
            END as account_4322,
            CASE
                WHEN sii.expense_account LIKE '5001 - Cost of Goods Sold - A' THEN COALESCE(pii.base_net_amount, 0)
                ELSE 0
            END as account_5001,
            sii.qty,
            sii.base_rate as rate,
            sii.base_net_amount as amount
        FROM
            `tabSales Invoice` si
        INNER JOIN
            `tabSales Invoice Item` sii ON si.name = sii.parent
        LEFT JOIN
            (
                SELECT
                    pii.item_code,
                    pii.base_net_amount,
                    pii.parent,
                    pi.posting_date
                FROM
                    `tabPurchase Invoice Item` pii
                INNER JOIN
                    `tabPurchase Invoice` pi ON pii.parent = pi.name
                WHERE
                    pi.docstatus = 1
                AND
                    (pii.item_code, pi.posting_date) IN (
                        SELECT
                            item_code,
                            MAX(pi2.posting_date) as max_posting_date
                        FROM
                            `tabPurchase Invoice Item` pii2
                        INNER JOIN
                            `tabPurchase Invoice` pi2 ON pii2.parent = pi2.name
                        WHERE
                            pi2.docstatus = 1
                        GROUP BY
                            pii2.item_code
                    )
            ) pii ON sii.item_code = pii.item_code
        WHERE
            si.docstatus = 1
            {conditions}
        ORDER BY
            si.posting_date DESC
    """

	return frappe.db.sql(query, filters, as_dict=1)

def get_delivery_note_data(filters):
	"""Get Delivery Note data with item details"""
	conditions = get_conditions(filters, "Delivery Note")

	query = f"""
		SELECT
			'Delivery Note' as document_type,
			dn.name as document_no,
			dn.posting_date,
			dn.customer as party,
			dni.item_code,
			dni.expense_account,
			CASE
				WHEN dni.expense_account LIKE '5001 - Cost of Goods Sold - A' THEN dni.base_net_amount
				ELSE 0
			END as account_5001,
			dni.qty,
			dni.base_rate as rate,
			dni.base_net_amount as amount
		FROM
			`tabDelivery Note` dn
		INNER JOIN
			`tabDelivery Note Item` dni ON dn.name = dni.parent
		WHERE
			dn.docstatus = 1
			{conditions}
		ORDER BY
			dn.posting_date DESC, dn.name
	"""

	return frappe.db.sql(query, filters, as_dict=True)


def get_payment_entry_data(filters):
	"""Get Payment Entry data"""
	conditions = get_conditions(filters, "Payment Entry")

	query = f"""
		SELECT
			'Payment Entry' as document_type,
			pe.name as document_no,
			pe.posting_date,
			pe.party as party,
			'' as item_code,
			'' as item_name,
			pe.paid_to as paid_to,
			pe.paid_from as paid_from,
			0 as account_4320,
			0 as account_4322,
			0 as account_5001,
			1 as qty,
			pe.base_paid_amount as rate,
			pe.base_paid_amount as amount
		FROM
			`tabPayment Entry` pe
		WHERE
			pe.docstatus = 1
			AND pe.payment_type IN ('Receive', 'Pay')
			{conditions}
		ORDER BY
			pe.posting_date DESC, pe.name
	"""

	return frappe.db.sql(query, filters, as_dict=True)


def get_conditions(filters, doctype):
	"""Get filter conditions for invoices and delivery notes"""
	conditions = ""

	prefix = "si"
	if doctype == "Delivery Note":
		prefix = "dn"
	elif doctype == "Payment Entry":
		prefix = "pe"

	if filters.get("from_date") and filters.get("to_date"):
		conditions += f" AND {prefix}.posting_date BETWEEN %(from_date)s AND %(to_date)s"
	elif filters.get("from_date"):
		conditions += f" AND {prefix}.posting_date >= %(from_date)s"
	elif filters.get("to_date"):
		conditions += f" AND {prefix}.posting_date <= %(to_date)s"

	if filters.get("party") and doctype == "Payment Entry":
		conditions += " AND pe.party = %(party)s"

	if filters.get("party") and doctype != "Payment Entry":
		conditions += f" AND {prefix}.customer = %(party)s"

	if filters.get("item") and doctype == "Sales Invoice":
		conditions += " AND sii.item_code = %(item)s"

	if filters.get("item") and doctype == "Delivery Note":
		conditions += " AND dni.item_code = %(item)s"

	if filters.get("income_account") and doctype == "Sales Invoice":
		conditions += " AND sii.income_account = %(income_account)s"

	if filters.get("expense_account") and doctype == "Sales Invoice":
		conditions += " AND sii.expense_account = %(expense_account)s"

	if filters.get("expense_account") and doctype == "Delivery Note":
		conditions += " AND dni.expense_account = %(expense_account)s"

	if filters.get("invoice") and doctype == "Sales Invoice":
		conditions += " AND si.name = %(invoice)s"

	if filters.get("paid_to") and doctype == "Payment Entry":
		conditions += " AND pe.paid_to = %(paid_to)s"

	if filters.get("paid_from") and doctype == "Payment Entry":
		conditions += " AND pe.paid_from = %(paid_from)s"

	return conditions
