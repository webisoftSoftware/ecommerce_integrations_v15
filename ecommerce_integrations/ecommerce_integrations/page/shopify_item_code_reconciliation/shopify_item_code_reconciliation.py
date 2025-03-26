from time import process_time

import frappe
from shopify.resources import Product

from ecommerce_integrations.shopify.connection import temp_shopify_session
from frappe.model.rename_doc import rename_doc

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
			is_id_disabled = frappe.db.get_value("Item", product.id, "disabled")
			item_needs_reconciliation = is_id_disabled is not None and not is_id_disabled
			requires_merging = False

			if item_needs_reconciliation and product.variants and product.variants[0].sku:
				is_sku_disabled = frappe.db.exists("Item", product.variants[0].sku)
				requires_merging = is_sku_disabled is not None and not is_sku_disabled

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
		merge_required = bool(frappe.db.exists("Item", item.get("id")) and \
										 bool(frappe.db.exists("Item", item.get("sku"))))
		if merge_required:
			result.append(item.get("id"))

	return result

def merge(old_erp_items, sku: str) -> dict:
	try:
		# Start a transaction
		frappe.db.begin()

		# Sort items by modified date (descending) to find the most recent one
		sorted_items = sorted(old_erp_items, key=lambda x: frappe.get_value("Item", x.name, "modified") or "1900-01-01", reverse=True)

		# The most recent item is the one we'll use as the source of truth
		most_recent_item_name = sorted_items[0].name if sorted_items else None

		if not most_recent_item_name:
			return {
				"code": 404,
				"message": "No items found to merge"
			}

		# Get the most recent item's data that we want to preserve
		most_recent_item = frappe.get_doc("Item", most_recent_item_name)

		# Important fields to preserve from the most recent item
		preserved_data = {
			"stock_uom": most_recent_item.stock_uom,
			"has_batch_no": most_recent_item.has_batch_no,
			"has_serial_no": most_recent_item.has_serial_no,
			"description": most_recent_item.description,
			"item_name": most_recent_item.item_name,
			"item_group": most_recent_item.item_group,
			"brand": most_recent_item.brand,
			"image": most_recent_item.image,
			"is_stock_item": most_recent_item.is_stock_item,
			"valuation_rate": most_recent_item.valuation_rate,
			"standard_rate": most_recent_item.standard_rate,
		}

		# Find the item that has an associated Ecommerce Item (if any)
		item_with_ecommerce = None
		ecommerce_item_data = None

		for item in old_erp_items:
			ecommerce_items = frappe.db.sql("""
                SELECT name, integration_item_code, variant_id, sku, erpnext_item_code
                FROM `tabEcommerce Item`
                WHERE integration = 'shopify'
                AND (erpnext_item_code = %s OR integration_item_code = %s)
            """, (item.name, item.name), as_dict=True)

			if ecommerce_items:
				item_with_ecommerce = item.name
				ecommerce_item_data = ecommerce_items[0]
				break

		# Determine which item to keep as the target
		# Priority: 1. Item with SKU as name, 2. Item with Ecommerce Item, 3. Most recent item
		target_item_name = None

		# Check if any item already has the SKU as its name
		for item in old_erp_items:
			if item.name == sku:
				target_item_name = sku
				break

		# If no item has the SKU as name, use the item with Ecommerce Item or most recent
		if not target_item_name:
			target_item_name = item_with_ecommerce if item_with_ecommerce else most_recent_item_name

		# If target item is not already named with SKU, try to rename it
		if target_item_name != sku:
			# Check if the SKU already exists as an item
			if frappe.db.exists("Item", sku):
				# If SKU exists but is in our list, we'll merge into it
				if sku in [item.name for item in old_erp_items]:
					target_item_name = sku
				else:
					# If SKU exists as a different item not in our list, we can't rename
					# Just keep the original target
					pass
			else:
				# If SKU doesn't exist, rename the target item to the SKU
				try:
					# First update the target item with preserved data using SQL
					# This bypasses validations that might prevent the rename
					set_fields = ", ".join([f"{key} = %s" for key in preserved_data.keys()])
					values = list(preserved_data.values())
					values.append(target_item_name)

					frappe.db.sql(f"""
						UPDATE `tabItem`
						SET {set_fields}
						WHERE name = %s
					""", values)

					# Now try to rename with Frappe's API
					rename_doc("Item", target_item_name, sku, merge=True, force=True)
					target_item_name = sku
				except Exception as rename_error:
					frappe.log_error(f"Failed to rename item {target_item_name} to {sku}: {str(rename_error)}")

		# Now update the target item with the preserved data if it's not the most recent item
		if target_item_name != most_recent_item_name:
			try:
				# Update using SQL to bypass validations
				set_fields = ", ".join([f"{key} = %s" for key in preserved_data.keys()])
				values = list(preserved_data.values())
				values.append(target_item_name)

				frappe.db.sql(f"""
					UPDATE `tabItem`
					SET {set_fields}
					WHERE name = %s
				""", values)
			except Exception as update_error:
				frappe.log_error(f"Failed to update item {target_item_name} with preserved data: {str(update_error)}")

		# Get a list of items to be disabled (all except the target)
		items_to_disable = [item.name for item in old_erp_items if item.name != target_item_name]

		# Disable the old items using SQL to bypass validations
		for old_item_name in items_to_disable:
			old_item = frappe.get_doc("Item", old_item_name)
			# Set flags to ignore validations
			old_item.flags.ignore_validate = True        # Skip validation methods
			old_item.flags.ignore_links = True           # Skip link validation
			old_item.flags.ignore_mandatory = True       # Skip mandatory field validation
			old_item.disabled = 1

			old_item.save()

		# Update the Ecommerce Item records to point to the target item
		if ecommerce_item_data:
			# Check if target item already has an Ecommerce Item
			existing_ecommerce_item = frappe.db.get_value(
				"Ecommerce Item",
				{"integration": "shopify", "erpnext_item_code": target_item_name},
				"name"
			)

			if existing_ecommerce_item and existing_ecommerce_item != ecommerce_item_data.name:
				# If target already has a different Ecommerce Item, update it with data from our found one
				frappe.db.sql("""
					UPDATE `tabEcommerce Item`
					SET
						integration_item_code = %s,
						variant_id = %s,
						sku = %s,
						modified = CURRENT_TIMESTAMP(6),
						modified_by = %s
					WHERE name = %s
				""", (
					ecommerce_item_data.integration_item_code,
					ecommerce_item_data.variant_id,
					sku,
					frappe.session.user,
					existing_ecommerce_item
				))

				# Delete the old Ecommerce Item
				frappe.db.sql("""
					DELETE FROM `tabEcommerce Item`
					WHERE name = %s
				""", ecommerce_item_data.name)
			elif ecommerce_item_data.erpnext_item_code != target_item_name:
				# Update the Ecommerce Item to point to the target item
				frappe.db.sql("""
					UPDATE `tabEcommerce Item`
					SET
						erpnext_item_code = %s,
						sku = %s,
						modified = CURRENT_TIMESTAMP(6),
						modified_by = %s
					WHERE name = %s
				""", (
					target_item_name,
					sku,
					frappe.session.user,
					ecommerce_item_data.name
				))

		# Commit the transaction
		frappe.db.commit()

		# Explicitly update the modified timestamp for the target item to ensure it shows in list view
		new_item = frappe.get_doc("Item", target_item_name)
		new_item.save()

		return {
			"code": 200,
			"message": f"Successfully merged items into {target_item_name} and disabled {len(items_to_disable)} old entries"
		}

	except Exception as e:
		frappe.db.rollback()
		return {
			"code": 500,
			"message": f"Error during merge: {str(e)}"
		}


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
				# Get all items that match either the SKU or the Shopify ID
				items_to_update = frappe.get_list("Item",
									  filters=[
										  ["name", "in", [shopify_product.variants[0].sku, shopify_product.id]]
									  ],
									  order_by="modified desc")
				merge(items_to_update, shopify_product.variants[0].sku)
			else:
				rename_doc(doc=erp_item, new=shopify_product.variants[0].sku, merge=False,
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
					# Get all items that match either the SKU or the Shopify ID
					items_to_update = frappe.get_list("Item",
													  filters=[
														  ["name", "in", [shopify_product.variants[0].sku, shopify_product.id]]
													  ],
													  order_by="modified desc")
					merge(items_to_update, shopify_product.variants[0].sku)
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

def disable_item_with_sql_and_save(item_code):
	# Direct SQL update to disable the item
	frappe.db.sql("""
		UPDATE `tabItem`
		SET
			disabled = 1,
			modified = CURRENT_TIMESTAMP(6),
			modified_by = %s
		WHERE name = %s
	""", (frappe.session.user, item_code))

	# Reload and trigger save hooks
	try:
		doc = frappe.get_doc("Item", item_code)
		doc.flags.ignore_permissions = True
		doc.flags.ignore_validate = True
		doc.flags.ignore_links = True
		doc.flags.ignore_mandatory = True
		doc.save(ignore_permissions=True)

		# Clear cache
		frappe.clear_document_cache("Item", item_code)
		return True
	except Exception as e:
		frappe.log_error(f"Error triggering hooks for item {item_code}: {str(e)}")
		return False

def update_item_with_sql_and_save(item_code, update_data):
	try:
		# First, perform the direct SQL update to bypass validations
		set_fields = ", ".join([f"{key} = %s" for key in update_data.keys()])
		values = list(update_data.values())
		values.append(item_code)

		frappe.db.sql(f"""
			UPDATE `tabItem`
			SET {set_fields}
			WHERE name = %s
		""", values)

		# Then, reload the document and trigger a save with minimal validations
		doc = frappe.get_doc("Item", item_code)

		# Set flags to minimize validations during save
		doc.flags.ignore_permissions = True
		doc.flags.ignore_validate = True
		doc.flags.ignore_links = True
		doc.flags.ignore_mandatory = True

		# This is important - tell Frappe this is not a new document version
		# but we still want to trigger hooks
		doc.flags.ignore_version = False

		# Set a flag to indicate this is just to trigger hooks
		doc.flags.trigger_hooks_only = True

		# Save with ignore_permissions to bypass permission checks
		doc.save(ignore_permissions=True)

		# Clear cache to ensure changes are immediately visible
		frappe.clear_document_cache("Item", item_code)

		return True
	except Exception as e:
		frappe.log_error(f"Error updating item {item_code}: {str(e)}")
		return False
