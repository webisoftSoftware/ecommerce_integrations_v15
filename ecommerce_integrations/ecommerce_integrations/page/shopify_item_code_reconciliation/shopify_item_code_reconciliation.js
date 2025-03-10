frappe.provide('shopify');

frappe.pages['shopify-item-code-reconciliation'].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper, title: 'Shopify Item Code Reconciliation', single_column: true
	});

	$('.page-title .title-area .title-text').css({
		'flex': 1,
		'max-width': '100vw',
	})
	new shopify.ProductImporter(wrapper);
}

let testShopifyDatatable;

shopify.ProductImporter = class {

	constructor(wrapper) {

		this.wrapper = $(wrapper).find('.layout-main-section');
		this.page = wrapper.page;
		this.init();
		this.selectedRows = new Set();
		this.reconcileRunning = false;
		this.productCount = 0;

		let fromDate = new Date();
		let toDate = new Date();

		// Set to last month.
		fromDate.setFullYear(fromDate.getFullYear() - 2);
		fromDate.setMonth(1);
		let currentISOFromDate = fromDate.toISOString();
		let currentISOToDate = toDate.toISOString();

		let timezoneOffsetFromDate = fromDate.toString().split(" ")[5].slice(3);
		let timezoneOffsetToDate = toDate.toString().split(" ")[5].slice(3);

		// YYYY-MM-DDTHH:MM:SS[timezone difference]
		// Ex: 2024-08-30T17:28:18-0400
		let shopifyFormattedFromDate = currentISOFromDate.slice(0, -5) + timezoneOffsetFromDate;
		let shopifyFormattedToDate = currentISOToDate.slice(0, -5) + timezoneOffsetToDate;

		this.from = shopifyFormattedFromDate;
		this.to = shopifyFormattedToDate;
	}

	init() {
		frappe.run_serially([() => this.addMarkup(), () => this.addTable(), () => this.checkReconcileStatus(), () => this.listen(),]);
	}

	async checkReconcileStatus() {
		const jobs = await frappe.db.get_list("RQ Job", {filters: {"status": ("in", ["queued", "started"])}});
		const job = jobs.find(job => job.job_name === 'shopify.job.reconcile.selected_products');

		this.reconcileRunning = job !== undefined && (job.status === "queued" || job.status === "started");

		if (this.reconcileRunning) {
			this.logReconcile();
		}
	}

	addMarkup() {
		const _markup = $(`
            <div class="row w-100 d-flex justify-content-center align-items-stretch flex-column overflow-auto m-auto">
                <div class="col-12 mt-2 gap-2">
                    <div class="border-0 p-1 rounded-sm">
                        <div class="d-flex flex-column flex-lg-row justify-content-between align-items-start m-auto">
                            <div class="d-flex flex-column flex-sm-row justify-content-sm-center m-auto m-sm-0 gap-5 mb-3 mb-lg-0">
                                <div class="form-group w-100 mx-2">
                                    <label>From Date</label>
                                    <input type="date" class="form-control p-2" id="from-date">
                                </div>
                                <div class="form-group w-100 w-md-auto mx-2">
                                    <label>To Date</label>
                                    <input type="date" class="form-control p-2" id="to-date">
                                </div>
                                <div class="form-group d-flex align-items-end w-100 justify-content-center w-md-auto mt-3 mt-md-0 ml-md-2">
                                    <button class="btn btn-primary w-sm-75 w-md-100" id="btn-search">Search</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-12" id="reconcile-details" style="display: none;">
                    <div class="w-auto">
                        <div class="card d-flex border-0 shadow-sm p-3 mb-3 rounded-sm" style="background-color: var(--card-bg)">
                            <h5 class="border-bottom pb-2">Reconciliation Details</h5>
                            <div id="shopify-reconcile-info" class="w-auto">
                                    <button type="button" id="btn-reconcile-selected" class="btn btn-xl btn-primary w-100 font-weight-bold py-3" style="display: none;">Reconcile Selected Products</button>
                            </div>
                        </div>

                        <div class="card border-0 shadow-sm p-3 mb-3 rounded-sm" style="background-color: var(--card-bg); display: none;">
                            <h5 class="border-bottom pb-2">Reconcile Log</h5>
                            <div class="control-value like-disabled-input for-description overflow-auto" id="shopify-reconcile-log" style="max-height: 500px;"></div>
                        </div>

                    </div>
                </div>
                <div class="col-12 d-flex flex-row fill-width align-items-stretch justify-content-center m-auto">
                    <div class="card border-0 shadow-sm p-3 mb-3 rounded-sm w-100">
                        <div class="d-flex flex-grow align-center border-bottom pb-2">
                            <h5 class="mr-4">Unreconciled Products in ERPNext</h5>
                            <div class="form-group h-auto ml-auto mr-0 position-relative">
                                <button type="button" class="btn btn-default btn-sm" id="toggle-legend">
                                    <i class="fa fa-question-circle mr-1"></i>
                                    <span>Show Legend</span>
                                </button>
                                <div class="card border-0 shadow-sm p-3 rounded-sm" id="legend-box"
                                    style="background-color: var(--card-bg);
                                           min-width: 300px;
                                           max-width: 450px;
                                           display: none;
                                           position: absolute;
                                           right: 0;
                                           margin-top: 10px;
                                           z-index: 100;">
                                    <h6 class="border-bottom pb-2 font-weight-bold">Legend</h6>
                                    <div class="mt-2">
                                        <div class="d-flex align-items-start mb-2">
                                            <div class="mr-2">
                                                <i class="fa fa-link text-primary" style="font-size: 1em;"></i>
                                            </div>
                                            <div>
                                                <div class="font-weight-bold mb-1">Reconciling</div>
                                                <p class="text-muted mb-0" style="font-size: 0.9em;">
                                                    Links Shopify products with ERPNext items using SKUs for inventory sync.
                                                </p>
                                            </div>
                                        </div>

                                        <div class="d-flex align-items-start mb-2">
                                            <div class="mr-2">
                                                <i class="fa fa-compress text-warning" style="font-size: 1em;"></i>
                                            </div>
                                            <div>
                                                <div class="font-weight-bold mb-1">Merging <span class="badge badge-warning ml-1" style="font-size: 0.7em;">Requires Attention</span></div>
                                                <p class="text-muted mb-0" style="font-size: 0.9em;">
                                                    Combines multiple Shopify products with same SKU.
                                                    <span class="text-danger">Cannot be undone.</span>
                                                </p>
                                            </div>
                                        </div>

                                        <div class="d-flex align-items-start">
                                            <div class="mr-2">
                                                <i class="fa fa-exclamation-circle text-warning" style="font-size: 1em;"></i>
                                            </div>
                                            <div>
                                                <div class="font-weight-bold mb-1">RM</div>
                                                <p class="text-muted mb-0" style="font-size: 0.9em;">
                                                    Indicates if an item will require merging (RM) during reconciliation.
                                                    'Yes' means the SKU already exists as an item code in ERPNext's inventory.
                                                </p>
                                            </div>
                                        </div>

                                        <div class="d-flex align-items-start">
                                            <div class="mr-2">
                                                <i class="fa fa-mouse-pointer text-info" style="font-size: 1em;"></i>
                                            </div>
                                            <div>
                                                <div class="font-weight-bold mb-1">Quick Navigation</div>
                                                <p class="text-muted mb-0" style="font-size: 0.9em;">
                                                    <span class="font-weight-medium">Item Codes:</span> Double-click to search in Item List.<br>
                                                    <span class="font-weight-medium">SKUs:</span> Click or double-click to search in Item List.
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="d-flex flex-grow fill-width align-center justify-content-center" id="shopify-product-list">
                            <div class="text-center">Loading...</div>
                        </div>
                    </div>
                </div>
            </div>
        `);

		this.wrapper.append(_markup);
	}

	async addTable() {

		const listElement = this.wrapper.find('#shopify-product-list')[0];
		const this_copy = this;

		this.shopifyProductTable = new frappe.DataTable(listElement, {
			columns: [{
				name: "Created On",
				align: "center",
				editable: false,
				focusable: true,
				sortable: true, // By default, sort the data by creation date (ascending).
				sortOrder: "asc",
				width: 120

			}, {
				name: 'Action',
				align: 'center',
				editable: false,
				focusable: true,
				sortable: true,
				width: 120
			}, {
				name: 'RM',
				align: 'center',
				editable: false,
				focusable: true,
				sortable: true,
				width: 50
			}, {
				name: 'Item Code',
				align: 'center',
				editable: false,
				focusable: true,
				sortable: true,
				width: 150,
				format: (value) => `<span class="cursor-pointer" title="Double-click to view item in ERPNext">${value}</span>`
			}, {
				name: 'SKU',
				align: "left",
				editable: false,
				focusable: true,
				sortable: false,
				width: 150,
				format: (value) => `<span class="cursor-pointer" title="Double-click to view item in ERPNext">${value}</span>`
			}, {
				name: 'Name',
				align: "left",
				editable: false,
				focusable: true,
				sortable: true,
				width: 750
			}],
			events: {
				onCheckRow(_) {
					const headerCheckbox = $(`.dt-cell__content--header-0`)
						.children(":first");
					const toast = $(`.dt-toast__message`);

					// Add/Remove the check for the header checkbox depending on if all items are
					// selected or not.
					if (headerCheckbox.is(":checked") && toast.length === 1 && Number(toast[0].innerText.slice(0, toast[0].innerText.indexOf(" "))) !== this_copy.productCount) {
						headerCheckbox.prop("checked", false);
					} else if (!headerCheckbox.is(":checked") && toast.length === 1 && Number(toast[0].innerText.slice(0, toast[0].innerText.indexOf(" "))) === this_copy.productCount) {
						headerCheckbox.prop("checked", true);
					}

					this_copy.toggleReconcileSelectedButton();
				},
				onCellDoubleClick(cell) {
					const column = cell.column.id;
					const value = cell.content;

					// Only handle double clicks on Item Code or SKU columns
					if (column === 3 || column === 4) { // Item Code is column 3, SKU is column 4
						// Navigate to Item List with filter
						frappe.set_route('List', 'Item', {
							'item_code': ['like', `%${value}%`]
						});
					}
				}
			},
			checkedRowStatus: true,
			clusterize: true,
			data: await this.fetchUnreconciledProducts(this.from, this.to),
			layout: 'fixed',
			noDataMessage: "No Items to reconcile",  // Message when there is no data.
			serialNoColumn: false,
			checkboxColumn: true,
			inlineFilters: true,
		});

		// Make scrollbar react to resize events and increase row height size.
		this.shopifyProductTable.style.setStyle('.dt-scrollable', {
			transform: 'translateZ(0)',
			backfaceVisibility: 'hidden',
			overflow: 'visible',
			minHeight: '70vh'
		});

		this.shopifyProductTable.style.setStyle(".dt-toast__message", {
			color: "#383838",
			backgroundColor: "#f3f3f3",
			border: "2px solid rgba(0, 0, 0, 0.25)",
			borderRadius: "8px",
			minWidth: "20%",
			fontSize: "1.05rem"
		});

		this.shopifyProductTable.style.setStyle(".dt-cell--header .dt-cell__content", {
			paddingRight: "5px",
		});

		// Add cursor pointer style for clickable cells
		this.shopifyProductTable.style.setStyle('.cursor-pointer', {
			cursor: 'pointer'
		});

		testShopifyDatatable = this.shopifyProductTable;
	}

	async fetchUnreconciledProducts(fromDate, toDate) {

		try {
			const { message: { products } } = await frappe.call({
				method: 'ecommerce_integrations.ecommerce_integrations.page.shopify_item_code_reconciliation.shopify_item_code_reconciliation.get_unreconciled_items',
				args: {
					from_date: fromDate,
					to_date: toDate
				}
			});

			if (!products || products.length === 0) return [];

			const shopifyProducts = products
				.sort((a, b) => new Date(a.product.created_at) - new Date(b.product.created_at))
				.map((dict) => ({
					"Created On": dict.product.created_at.replace("T", " ").split(" ")[0],
					'Item Code': dict.product.id,
					'Name': dict.product.title,
					'SKU': dict.product.variants && dict.product.variants.map(a => `${a.sku}`).join(', '),
					'Action': `<button type="button" class="btn btn-default btn-xs btn-reconcile mx-2" data-product="${dict.product.id}"> Reconcile </button>`,
					'RM': dict.requires_merging ? 'Yes' : 'No'
				}));

			console.log(shopifyProducts);
			this.productCount = shopifyProducts.length;

			return shopifyProducts;
		} catch (error) {
			frappe.throw(__(`Error fetching products: ${JSON.stringify(error)}`));
		}
	}

	listen() {

		$(window).on("resize", () => {
			this.shopifyProductTable.setDimensions();
		});

		$(document).ready(() => {
			$("h3").css({
				"overflow": "visible",
				"text-ellipsis": "unset"
			});
		});

		this.wrapper.on("click", "#btn-reconcile-selected", async e => {
			// Update all states at once
			for (let index = 0; index < this.productCount; ++index) {
				const checkbox = $(`.dt-row[data-row-index="${index}"]`)
					.find('.dt-cell__content--col-0 input[type="checkbox"]');

				const productId = $(`.dt-row[data-row-index="${index}"]`)
					.find('.dt-cell__content--col-4')
					.prop("innerText");

				if (index >= 50) {
					checkbox.prop("checked", false);  // Remove checks for items past 60.
				}

				if (productId && checkbox.is(":checked")) {
					this.selectedRows.add(productId);
				} else if (productId) {
					this.selectedRows.delete(productId);
				}
			}

			console.log(this.selectedRows);
			const result = await this.get_required_merge_items();
			console.debug(result);
			const _this = $(e.currentTarget);

			frappe.confirm(__(`Are you sure you want to proceed reconciling these ${this.selectedRows.size} products to their SKU on Shopify? Careful, this action is irreversible! Proceed Anyway?`), async () => {
					if (result && result.length > 0) {
						frappe.confirm(__(`WARNING: ${result.length} detected items needing to be merged. Proceed to merge them anyway? THIS ACTION CANNOT BE UNDONE.`),
							async () => {
								_this.prop("disabled", true).text("Reconciling...");
								await this.reconcileSelected();
							}, () => {
							});
					}
				},
				() => {}
			);
		});

		// Reconcile a product from table
		this.wrapper.on('click', '.btn-reconcile', async e => {

			const _this = $(e.currentTarget);

			_this.prop('disabled', true).text('Reconciling...');

			const product = _this.attr('data-product');
			const status = await this.reconcileProduct(product);

			console.log(status);
			if (status.code === 200) {
				frappe.msgprint("Product reconciled successfully");
				// Refresh data.
				let newData;

				if (this.wrapper.find('#from-date').val() !== '') {
					newData = await this.fetchUnreconciledProducts(this.wrapper.find('#from-date').val(),
						this.wrapper.find('#to-date').val() !== '' ? this.wrapper.find('#to-date').val() : this.to);
				} else {
					newData = await this.fetchUnreconciledProducts(this.from, this.to);
				}
				await this.shopifyProductTable.refresh(newData);
			}

			_this.prop('disabled', false).text('Reconcile');
		});

		// Add date search handler
		this.wrapper.on('click', '#btn-search', async () => {
			const fromDate = this.wrapper.find('#from-date').val();
			const toDate = this.wrapper.find('#to-date').val();

			if (!fromDate && !toDate) {
				this.shopifyProductTable.freeze();
				const products = await this.fetchUnreconciledProducts(this.from, this.to);
				await this.shopifyProductTable.refresh(products);
				this.clearSelection();
				this.shopifyProductTable.unfreeze();
				return;
			}

			let formattedFromDate = null;
			let formattedToDate = null;

			console.debug(fromDate);
			if (fromDate && fromDate.split("-")[0].length !== 4) {
				frappe.throw(__("Incorrect From Date Format"));
				return;
			}

			if (fromDate) {
				const date = new Date(fromDate);
				const tzOffset = date.toString().split(" ")[5].slice(3);
				const ISODate = date.toISOString();
				formattedFromDate = ISODate.slice(0, -5) + tzOffset;
			}

			if (toDate && toDate.split("-")[0].length !== 4) {
				frappe.throw(__("Incorrect To Date Format"));
				return;
			}

			if (toDate) {
				const date = new Date(toDate);
				const tzOffset = date.toString().split(" ")[5].slice(3);
				const ISODate = date.toISOString();
				formattedToDate = ISODate.slice(0, -5) + tzOffset;
			}

			// Fetch and update table
			console.log("From Date:", formattedFromDate, "To Date:", formattedToDate);
			this.shopifyProductTable.freeze();
			const products = await this.fetchUnreconciledProducts(formattedFromDate, formattedToDate);
			await this.shopifyProductTable.refresh(products);
			this.clearSelection();
			this.shopifyProductTable.unfreeze();
		});

		// Add legend toggle handler
		this.wrapper.on('click', '#toggle-legend', function(e) {
			e.stopPropagation(); // Prevent clicks from bubbling up
			const $button = $(this);
			const $legendBox = $('#legend-box');
			const isVisible = $legendBox.is(':visible');

			$legendBox.slideToggle(200); // Animate the show/hide

			// Update button text
			$button.html(
				isVisible ?
				'<i class="fa fa-question-circle mr-1"></i><span>Show Legend</span>' :
				'<i class="fa fa-question-circle mr-1"></i><span>Hide Legend</span>'
			);
		});

		// Add double-click handler for Item Code and SKU columns
		this.wrapper.on('dblclick', '.dt-cell__content--col-4, .dt-cell__content--col-5', function() {
			const value = $(this).text().trim();
			if (value) {
				frappe.set_route('List', 'Item', {
					'item_code': ['like', `%${value}%`]
				});
			}
		});
	}

	async get_required_merge_items() {
		// Find all the products selected and map them to only have sku and id.
		const itemsNeedingToMerge = [];
		for (let index = 0; index < this.productCount; ++index) {
			const isChecked = $(`.dt-row[data-row-index="${index}"]`)
				.find('.dt-cell__content--col-0 input[type="checkbox"]')
				.is(":checked");

			if (isChecked) {
				const row = $(`.dt-row[data-row-index="${index}"]`);
				const id = row.find('.dt-cell__content--col-4').prop("innerText");
				const sku = row.find('.dt-cell__content--col-5').prop("innerText");

				if (id && sku) {
					itemsNeedingToMerge.push({
						id: id.toString(),
						sku: sku.toString()
					});
				}
			}
		}
		console.debug("Items needing to be potentially merged:", itemsNeedingToMerge);

		if (itemsNeedingToMerge.length > 0) {
			try {
				const response = await frappe.call({
					method: 'ecommerce_integrations.ecommerce_integrations.page.shopify_item_code_reconciliation.shopify_item_code_reconciliation.get_merge_required_items',
					args: {
						shopify_items: JSON.stringify(itemsNeedingToMerge)
					}
				});
				return response.message || [];
			} catch (error) {
			}
		}
		return [];
	}

	clearSelection() {
		this.selectedRows.clear();
		this.shopifyProductTable.clearToastMessage();
		// Clear all states at once
		for (let index = 0; index < this.productCount; ++index) {
			const checkbox = $(`.dt-row[data-row-index="${index}"]`)
				.find('.dt-cell__content--col-0 input[type="checkbox"]');

			if (checkbox) {
				checkbox.prop("checked", false);
			}
		}

		// Uncheck the top header checkbox (fall selecting all).
		$(`.dt-cell__content--header-0`)
			.children(":first")
			.prop("checked", false);
		this.toggleReconcileSelectedButton();
	}

	async reconcileProduct(product) {

		const {message: status} = await frappe.call({
			method: 'ecommerce_integrations.ecommerce_integrations.page.shopify_item_code_reconciliation.shopify_item_code_reconciliation.reconcile',
			args: {product: product},
		});

		return status;

	}

	async reconcileSelected() {

		this.checkReconcileStatus();

		if (this.reconcileRunning) {
			frappe.msgprint(__('Reconcile already in progress'));
		} else {
			console.log([...this.selectedRows].map(id => `${id}`).join(", "));
			frappe.call({
				method: 'ecommerce_integrations.ecommerce_integrations.page.shopify_item_code_reconciliation.shopify_item_code_reconciliation.reconcile_multiple',
				args: {
					comma_delimited_products: [...this.selectedRows].map(id => `${id}`).join(",")
				},
			}).then(async () => {
				// Refresh data.
				let newData;
				if (this.wrapper.find('#from-date').val() !== '') {
					newData = await this.fetchUnreconciledProducts(this.wrapper.find('#from-date').val(),
						this.wrapper.find('#to-date').val() !== '' ? this.wrapper.find('#to-date').val() : this.to);
				} else {
					newData = await this.fetchUnreconciledProducts(this.from, this.to);
				}
				this.selectedRows.clear();

				// Clear all checkboxes.
				for (let index = 0; index < this.productCount; ++index) {
					const checkbox = $(`.dt-row[data-row-index="${index}"]`)
						.find('.dt-cell__content--col-0 input[type="checkbox"]');

					if (checkbox.is(":checked")) {
						checkbox.prop("checked", false);
					}
				}

				await this.shopifyProductTable.refresh(newData);
				console.log(this.shopifyProductTable.getColumns());
				$('#btn-reconcile-selected').prop("disabled", false).text("Reconcile Selected Products");
			})
			this.logReconcile();
		}
	}

	logReconcile() {

		const _log = $('#shopify-reconcile-log');
		_log.parents('.card').show();
		_log.text(''); // clear logs

		frappe.realtime.on('shopify.key.reconcile.selected.products', ({
																	  message,
																	  done,
																  }) => {

			message = `<pre class="mb-0">${message}</pre>`;
			_log.append(message);
			_log.scrollTop(_log[0].scrollHeight)

			if (done) {
				frappe.realtime.off('shopify.key.reconcile.selected.products');
				this.toggleReconcileSelectedButton();
				this.reconcileRunning = false;
			}
		})

	}

	toggleReconcileSelectedButton() {
		const toast = $(".dt-toast__message");
		if (toast.length === 1) {
			const numberSelected = Number(toast[0].innerText.slice(0, toast[0].innerText.indexOf(" ")));
			$("#reconcile-details").css({
				"visibility": "visible",
				"display": "flex",
				"justify-content": "center",
				"align-items": "stretch",
				"margin": "auto"
			});
			$("#btn-reconcile-selected")
				.css({
					"visibility": "visible",
					"display": "flex",
					"justify-content": "center",
					"margin": "auto"
				})
				.text(`Reconcile Selected Products (${numberSelected <= 50 ? numberSelected : '50 [MAX]'})`);
			return;
		}

		$("#reconcile-details").css({
			"display": "none"
		});
		$("#btn-reconcile-selected")
			.css({
				"display": "none",
			});
	}
}
