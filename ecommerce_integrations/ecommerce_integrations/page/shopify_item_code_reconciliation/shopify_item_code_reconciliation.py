from time import process_time

import frappe
from shopify.resources import Product

from ecommerce_integrations.shopify.connection import temp_shopify_session

# constants
SYNC_JOB_NAME = "shopify.job.reconcile.selected.products"
REALTIME_KEY = "shopify.key.reconcile.selected.products"

@frappe.whitelist()
@temp_shopify_session
def get_unreconciled_items(from_date: str, to_date: str | None):
	"""Get All item in ERP's inventory that do not have the appropriate SKU displayed on Shopify
		as their item code."""
	result = []
	collection = Product.find(created_at_min=from_date, created_at_max=to_date, limit=250)

	while collection.has_next_page():
		for product in collection:
			item_needs_reconciliation = bool(frappe.db.exists("Item", product.id))
			if product.variants and product.variants[0].sku:
				requires_merging = bool(frappe.db.exists("Item", product.variants[0].sku))

				if item_needs_reconciliation:
					result.append({"requires_merging": requires_merging, "product": product.to_dict()})
		next_url = collection.next_page_url
		collection = Product.find(from_=next_url)

	return {
		"products": result
	}


@frappe.whitelist()
def get_merge_required_items(shopify_items) -> list[str]:
	shopify_items_list = list(frappe.parse_json(shopify_items))
	"""Get All items in ERP's inventory that already have an SKU as for the product ID given,
		requiring a merge to be done. This will attempt to merge all the items having the same SKU
		and combining them into one. Warning, this can be destructive.
		@param shopify_items: List of items to merge. These must be unreconciled products from Shopify
	"""
	result = []

	for item in shopify_items_list:
		# Only 'merge' if there's an existing product ID associated with an item and its SKU.
		item_needs_reconciliation = bool(frappe.db.exists("Item", item.get("id")) and \
										 bool(frappe.db.exists("Item", item.get("sku"))))
		if item_needs_reconciliation:
			result.append(item.get("id"))

	return result


@frappe.whitelist(methods=["POST"])
@temp_shopify_session
def reconcile(product: str) -> dict:
	"""Reconcile one Shopify product in ERP's inventory by renaming the item to the
		SKU recorded in Shopify."""
	from frappe.model.rename_doc import rename_doc

	savepoint = "reconcile_product"
	frappe.db.savepoint(savepoint)

	shopify_product = Product.find(product)
	if shopify_product.variants.__len__() > 0 and shopify_product.variants[0].sku:
		try:
			erp_item = frappe.get_doc("Item", shopify_product.id)

			if bool(frappe.db.exists("Item", shopify_product.variants[0].sku)):
				erp_item.name = rename_doc(doc=erp_item, new=shopify_product.variants[0].sku, merge=True,
										   force=False, validate=True, show_alert=False)
			else:
				erp_item.name = rename_doc(doc=erp_item, new=shopify_product.variants[0].sku, merge=False,
								   force=False, validate=True, show_alert=False)

		except frappe.DoesNotExistError as _:
			frappe.db.rollback(save_point=savepoint)
			return {
				"code": 404,
				"message": f"❌ [404] Error reconciling product {shopify_product.id}: Item not found"
			}

		except frappe.PermissionError as _:
			frappe.db.rollback(save_point=savepoint)
			return {
				"code": 403,
				"message": f"❌ [403] Error reconciling product {shopify_product.id}: Access denied"
			}

		except Exception as e:
			frappe.db.rollback(save_point=savepoint)
			return {
				"code": 500,
				"message": f"❌ [500] Error reconciling product {shopify_product.id}: {str(e)}"
			}
	else:
		return {
			"code": 400,
			"message": f"❌ [400] Error reconciling product {shopify_product.id}: No SKU found for this product"
		}

	return {
		"code": 200,
		"message": "Successful"
	}


@frappe.whitelist()
@temp_shopify_session
def reconcile_multiple(comma_delimited_products: str) -> dict:
	"""Reconcile many Shopify products in ERP's inventory by renaming the item(s) to the
		SKU recorded in Shopify. This variant is mainly used to publish real time logs."""
	from frappe.model.rename_doc import rename_doc

	start_time = process_time()
	savepoint = "reconcile_product"

	for item in comma_delimited_products.split(","):
		frappe.db.savepoint(savepoint)

		shopify_product = Product.find(id_=item)
		if shopify_product.variants.__len__() > 0 and shopify_product.variants[0].sku:
			try:
				erp_item = frappe.get_doc("Item", shopify_product.id)

				if bool(frappe.db.exists("Item", shopify_product.variants[0].sku)):
					erp_item.name = rename_doc(doc=erp_item, new=shopify_product.variants[0].sku, merge=True,
											   force=False, validate=True, show_alert=False)
				else:
					erp_item.name = rename_doc(doc=erp_item, new=shopify_product.variants[0].sku, merge=False,
											   force=False, validate=True, show_alert=False)

				publish(f"✅ Reconciled product {shopify_product.id} to {shopify_product.variants[0].sku}", reconciled=True)

			except frappe.DoesNotExistError as _:
				frappe.db.rollback(save_point=savepoint)
				publish(f"❌ Error reconciling product {shopify_product.id}: Item not found", error=True)
				continue

			except frappe.PermissionError as _:
				frappe.db.rollback(save_point=savepoint)
				publish(f"❌ Error reconciling product {shopify_product.id}: Access denied", error=True)
				continue

			except Exception as e:
				frappe.db.rollback(save_point=savepoint)
				publish(f"❌ Error reconciling product {shopify_product.id}: {str(e)}", error=True)
				continue
		else:
			publish(f"❌ Error reconciling product {shopify_product.id}: No SKU found for this product", error=True)
			continue

	end_time = process_time()
	publish(f"🎉 Done in {end_time - start_time}s", done=True)
	return {
		"code": 200,
		"message": "Successful"
	}

def publish(message, reconciled=False, error=False, done=False, br=True):
	frappe.publish_realtime(
		REALTIME_KEY,
		{
			"reconciled": reconciled,
			"error": error,
			"message": message + ("<br /><br />" if br else ""),
			"done": done,
		},
	)
