frappe.provide('shopify');

frappe.pages['shopify-item-code-reconciliation'].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper, title: 'Shopify Item Code Reconciliation', single_column: true
	});

	new shopify.ProductImporter(wrapper);

}

let currentJSDate = new Date();

// Set to last month.
currentJSDate.setFullYear(currentJSDate.getFullYear() - 2);
currentJSDate.setMonth(11);
currentJSDate.setDate(31);
let timezoneOffset = currentJSDate.toString().split(" ")[5].slice(3);
let currentISODate = currentJSDate.toISOString();

// YYYY-MM-DDTHH:MM:SS[timezone difference]
// Ex: 2024-08-30T17:28:18-0400
let shopifyFormattedDate = currentISODate.slice(0, -5) + timezoneOffset;
console.log(shopifyFormattedDate);

shopify.ProductImporter = class {

	constructor(wrapper) {

		this.wrapper = $(wrapper).find('.layout-main-section');
		this.page = wrapper.page;
		this.init();
		this.selectedRows = new Set();
		this.reconcileRunning = false;
		this.productCount = 0;
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
            <div class="row w-100 d-flex justify-content-center align-items-stretch flex-column overflow: auto m-auto">
                <div class="col-12 mb-3 gap-2">
                    <div class="card border-0 shadow-sm p-3 rounded-sm">
                        <div class="d-flex flex-column flex-md-row justify-content-between align-items-start align-items-md-center m-auto">
                            <div class="d-flex flex-column flex-md-row gap-5">
                                <div class="form-group w-100 w-md-auto mx-2">
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
                    <div class="card border-0 shadow-sm p-3 mb-3 rounded-sm">
                        <h5 class="w-auto border-bottom pb-2">Unreconciled Products in ERPNext</h5>
                        <div class="d-flex flex-grow fill-width justify-content-center" id="shopify-product-list">
                            <div class="text-center">Loading...</div>
                        </div>
                        <div class="shopify-datatable-footer mt-2 pt-3 pb-2 border-top text-right" style="display: none">
                            <div class="btn-group">
                                <button type="button" class="btn btn-sm btn-default btn-paginate btn-prev">Prev</button>
                                <button type="button" class="btn btn-sm btn-default btn-paginate btn-next">Next</button>
                            </div>
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
				name: 'Item Code',
				align: 'center',
				editable: false,
				focusable: true,
				sortable: true,
				width: 150
			}, {
				name: 'SKU',
				align: "left",
				editable: false,
				focusable: true,
				sortable: false,
				width: 150
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
				}
			},
			checkedRowStatus: true,
			clusterize: true,
			data: await this.fetchUnreconciledProducts(shopifyFormattedDate, null),
			layout: 'fixed',
			noDataMessage: "No Items were retrieved",  // Message when there is no data.
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
	}

	async fetchUnreconciledProducts(fromDate, toDate) {

		try {
			const products = await frappe.call({
				method: 'ecommerce_integrations.ecommerce_integrations.page.shopify_item_code_reconciliation.shopify_item_code_reconciliation.get_unreconciled_items',
				args: {
					from_date: fromDate,
					to_date: toDate
				}
			});

			if (!products.message || products.message.length === 0) return [];

			const shopifyProducts = products.message.map((product) => ({
				// 'Image': product.image && product.image.src && `<img style="height: 50px" src="${product.image.src}">`,
				"Created On": product.created_at.replace("T", " ").split(" ")[0],
				'Item Code': product.id,
				'Name': product.title,
				'SKU': product.variants && product.variants.map(a => `${a.sku}`).join(', '),
				'Action': `<button type="button" class="btn btn-default btn-xs btn-reconcile mx-2" data-product="${product.id}"> Reconcile </button>`,
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

		this.wrapper.on("click", "#btn-reconcile-selected", e => {
			// Update all states at once
			for (let index = 0; index < this.productCount; ++index) {
				const isChecked = $(`.dt-row[data-row-index="${index}"]`)
					.find('.dt-cell__content--col-0 input[type="checkbox"]')
					.is(":checked");

				const productId = $(`.dt-row[data-row-index="${index}"]`)
					.find('.dt-cell__content--col-3')
					.prop("innerText");

				if (productId && isChecked) {
					this.selectedRows.add(productId);
				} else if (productId) {
					this.selectedRows.delete(productId);
				}
			}

			console.log(this.selectedRows);

			const _this = $(e.currentTarget);
			frappe.confirm(__(`Are you sure you want to proceed reconciling these ${this.selectedRows.size} products to their SKU on Shopify? Careful, this action is irreversible! Proceed Anyway?`), async () => {
				_this.prop("disabled", true).text("Reconciling...");

				await this.reconcileSelected();
			}, () => {
			});
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
						this.wrapper.find('#to-date').val() !== '' ? this.wrapper.find('#to-date').val() : null);
				} else {
					newData = await this.fetchUnreconciledProducts(shopifyFormattedDate, null);
				}
				await this.shopifyProductTable.refresh(newData);
				await this.shopifyProductTable.sortColumn(1, 'asc');
			}

			_this.prop('disabled', false).text('Reconcile');
		});

		// Add date search handler
		this.wrapper.on('click', '#btn-search', async () => {
			const fromDate = this.wrapper.find('#from-date').val();
			const toDate = this.wrapper.find('#to-date').val();

			if (!fromDate && !toDate) {
				const products = await this.fetchUnreconciledProducts(shopifyFormattedDate, null);
				this.shopifyProductTable.refresh(products);
				await this.shopifyProductTable.sortColumn(1, 'asc');
				return;
			}

			// Convert dates to Shopify format
			let formattedFromDate = '';
			let formattedToDate = '';

			if (fromDate) {
				const fromDateObj = new Date(fromDate);
				formattedFromDate = fromDateObj.toISOString().slice(0, -5) + fromDateObj.toString().split(" ")[5].slice(3);
			}

			if (toDate) {
				const toDateObj = new Date(toDate);
				formattedToDate = toDateObj.toISOString().slice(0, -5) + toDateObj.toString().split(" ")[5].slice(3);
			}

			// Fetch and update table
			const products = await this.fetchUnreconciledProducts(formattedFromDate, formattedToDate);
			this.shopifyProductTable.refresh(products);
			await this.shopifyProductTable.sortColumn(1, 'asc');
		});
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
						this.wrapper.find('#to-date').val() !== '' ? this.wrapper.find('#to-date').val() : null);
				} else {
					newData = await this.fetchUnreconciledProducts(shopifyFormattedDate, null);
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
				await this.shopifyProductTable.sortColumn(1, 'asc');
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
				.text(`Reconcile Selected Products (${toast[0].innerText.slice(0, toast[0].innerText.indexOf(" "))})`);
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
