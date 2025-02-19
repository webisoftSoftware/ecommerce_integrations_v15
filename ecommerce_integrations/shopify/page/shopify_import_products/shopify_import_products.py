from time import process_time

import frappe
from frappe import _
from frappe.exceptions import UniqueValidationError
from shopify.resources import Product

from ecommerce_integrations.ecommerce_integrations.doctype.ecommerce_item import ecommerce_item
from ecommerce_integrations.shopify.connection import temp_shopify_session
from ecommerce_integrations.shopify.constants import MODULE_NAME
from ecommerce_integrations.shopify.product import ShopifyProduct

# constants
SYNC_JOB_NAME = "shopify.job.sync.selected.products"
REALTIME_KEY = "shopify.key.sync.selected.products"


@frappe.whitelist()
def get_shopify_products(from_date):
	shopify_products = fetch_all_products(from_date)
	return shopify_products


def fetch_all_products(from_date):
	# format shopify collection for datatable

	collection = _fetch_products_from_shopify(from_date)

	products = []
	for product in collection:
		d = product.to_dict()
		if d["variants"] and d["variants"][0].get("sku"):
			shopify_product = ShopifyProduct(product.id, sku=d["variants"][0]["sku"])
			d["synced"] = is_synced(product.id, shopify_product.sku)
		else:
			d["synced"] = is_synced(product.id, None)
		products.append(d)

	return {"products": products}


@temp_shopify_session
def _fetch_products_from_shopify(from_date, limit=50):
	return Product.find(created_at_min=from_date, limit=limit)


@frappe.whitelist()
def get_product_count():
	items = frappe.db.get_list("Item", {"variant_of": ["is", "not set"]})
	erpnext_count = len(items)

	sync_items = frappe.db.get_list("Ecommerce Item", {"variant_of": ["is", "not set"]})
	synced_count = len(sync_items)

	shopify_count = get_shopify_product_count()

	return {
		"shopifyCount": shopify_count,
		"syncedCount": synced_count,
		"erpnextCount": erpnext_count,
	}


@temp_shopify_session
def get_shopify_product_count():
	return Product.count()


@frappe.whitelist()
def sync_product(product):
	try:
		shopify_product = ShopifyProduct(product)
		shopify_product.sync_product()

		return True
	except Exception:
		frappe.db.rollback()
		return False


@frappe.whitelist()
def resync_product(product):
	return _resync_product(product)


@temp_shopify_session
def _resync_product(product):
	savepoint = "shopify_resync_product"
	try:
		item = Product.find(product)

		frappe.db.savepoint(savepoint)
		for variant in item.variants:
			shopify_product = ShopifyProduct(product, variant_id=variant.id)
			shopify_product.sync_product()

		return True
	except Exception:
		frappe.db.rollback(save_point=savepoint)
		return False

def is_synced(product_id: str, product_sku: str | None) -> bool:
	if not product_sku:
		return False

	return ecommerce_item.is_synced(MODULE_NAME, integration_item_code=product_id, sku=product_sku)


@frappe.whitelist()
def import_selected_products(products: str):
	product_list: list = products.split(",")

	frappe.enqueue(queue_sync_selected_products, products=product_list, queue="long",
				   job_name=SYNC_JOB_NAME,
				   key=REALTIME_KEY)


def queue_sync_selected_products(*args, **kwargs):
	start_time = process_time()

	_sync = True
	savepoint = "shopify_product_sync"
	products: list = kwargs.get("products", [])
	publish(f"{products}")
	for product in products:
		try:
			publish(f"Syncing product {product}", br=False)
			frappe.db.savepoint(savepoint)

			shopify_product = ShopifyProduct(product)
			if is_synced(shopify_product.product_id, shopify_product.sku):
				publish(f"Product {product} already synced. Skipping...")
				continue

			shopify_product.sync_product()
			publish(f"✅ Synced Product {product}", synced=True)

		except UniqueValidationError as e:
			publish(f"❌ Error Syncing Product {product} : {str(e)}", error=True)
			frappe.db.rollback(save_point=savepoint)
			continue

		except Exception as e:
			publish(f"❌ Error Syncing Product {product} : {str(e)}", error=True)
			frappe.db.rollback(save_point=savepoint)
			continue

	end_time = process_time()
	publish(f"🎉 Done in {end_time - start_time}s", done=True)
	return True


def publish(message, synced=False, error=False, done=False, br=True):
	frappe.publish_realtime(
		REALTIME_KEY,
		{
			"synced": synced,
			"error": error,
			"message": message + ("<br /><br />" if br else ""),
			"done": done,
		},
	)
