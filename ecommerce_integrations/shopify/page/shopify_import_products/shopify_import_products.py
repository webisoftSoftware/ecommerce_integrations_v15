from time import process_time

import frappe
from frappe import ValidationError
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
		d["synced"] = is_synced(product.id)
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
@temp_shopify_session
def sync_product(product):
	try:
		shopify_product = Product.find(product)
		shopify_product_dict = shopify_product.to_dict()
		if shopify_product_dict["variants"].__len__() > 0 and shopify_product_dict["variants"][0].get("sku"):
			return {
				"code": 500,
				"message": f"❌ Error Syncing Product {product} : No SKU found for this item"
			}
		erp_product = ShopifyProduct(product)
		erp_product.sync_product()

		return {
			"code": 200,
		}
	except Exception as e:
		return {
			"code": 500,
			"message": f"❌ Error Syncing Product {product} : {str(e)}"
		}


@frappe.whitelist()
def resync_product(product):
	return _resync_product(product)


@temp_shopify_session
def _resync_product(product):
	return sync_product(product)

@temp_shopify_session
def is_synced(product_id: str) -> bool:
	try:
		shopify_product = Product.find(product_id).to_dict()
		if not shopify_product["variants"] or shopify_product["variants"].__len__() == 0 or \
			not shopify_product["variants"][0].get("sku"):
			return False

		return ecommerce_item.is_synced(MODULE_NAME, integration_item_code=product_id,
										sku=shopify_product["variants"][0].get("sku"))
	except Exception as _:
		raise ValidationError


@frappe.whitelist()
def import_selected_products(products: str):
	product_list: list = products.split(",")

	frappe.enqueue(queue_sync_selected_products, products=product_list, queue="long",
				   job_name=SYNC_JOB_NAME,
				   key=REALTIME_KEY)


def queue_sync_selected_products(*_args, **kwargs):
	start_time = process_time()

	_sync = True
	savepoint = "shopify_product_sync"
	products: list = kwargs.get("products", [])
	publish(f"{products}")
	for product in products:
		try:
			publish(f"Syncing product {product}", br=False)
			frappe.db.savepoint(savepoint)

			if is_synced(product):
				publish(f"Product {product} already synced. Skipping...")
				continue

			erp_product = ShopifyProduct(product)
			erp_product.sync_product()
			publish(f"✅ Synced Product {product}", synced=True)

		except UniqueValidationError as e:
			publish(f"❌ Error Syncing Product {product} : {str(e)}", error=True)
			frappe.db.rollback(save_point=savepoint)
			continue

		except ValidationError as _:
			publish(f"❌ Error Syncing Product {product} : No SKU found for this item", error=True)
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
