frappe.provide('shopify');

frappe.pages['shopify-import-products'].on_page_load = function (wrapper) {
	let page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Shopify Item Sync',
		single_column: true
	});

	new shopify.ProductImporter(wrapper);

}

shopify.ProductImporter = class {

	constructor(wrapper) {

		this.wrapper = $(wrapper).find('.layout-main-section');
		this.page = wrapper.page;
		this.init();
		this.selectedRows = new Set();
		this.syncRunning = false;
		this.allRowCheckBoxStates = new Map();

	}

	init() {
		frappe.run_serially([
			() => this.addMarkup(),
			() => this.fetchProductCount(),
			() => this.addTable(),
			() => this.checkSyncStatus(),
			() => this.listen(),
		]);
	}

	async checkSyncStatus() {
		const jobs = await frappe.db.get_list("RQ Job", {filters: {"status": ("in", ("queued", "started"))}});
		this.syncRunning = jobs.find(job => job.job_name == 'shopify.job.sync.selected.products') !== undefined;

		if (this.syncRunning) {
			this.logSync();
		}
	}

	addMarkup() {

		const _markup = $(`
            <div class="row w-100 d-flex justify-content-center align-items-stretch flex-column overflow: auto m-auto">
                <div class="col-12 d-flex flex-row align-items-stretch m-auto justify-content-center">
                    <div class="w-auto">
                        <div class="card d-flex border-0 shadow-sm p-3 mb-3 rounded-sm" style="background-color: var(--card-bg)">
                            <h5 class="border-bottom pb-2">Synchronization Details</h5>
                            <div id="shopify-sync-info" class="w-auto">
                                    <button type="button" id="btn-sync-selected" class="btn btn-xl btn-primary w-100 font-weight-bold py-3" style="display: none;">Sync Selected Products</button>
                                <div class="product-count py-3 d-flex justify-content-stretch">
                                    <div class="text-center p-3 mx-2 rounded" style="background-color: var(--bg-color)">
                                        <h2 id="count-products-shopify">-</h2>
                                        <p class="text-muted m-0">in Shopify</p>
                                    </div>
                                    <div class="text-center p-3 mx-2 rounded" style="background-color: var(--bg-color)">
                                        <h2 id="count-products-erpnext">-</h2>
                                        <p class="text-muted m-0">in ERPNext</p>
                                    </div>
                                    <div class="text-center p-3 mx-2 rounded" style="background-color: var(--bg-color)">
                                        <h2 id="count-products-synced">-</h2>
                                        <p class="text-muted m-0">Synced</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="card border-0 shadow-sm p-3 mb-3 rounded-sm" style="background-color: var(--card-bg); display: none;">
                            <h5 class="border-bottom pb-2">Sync Log</h5>
                            <div class="control-value like-disabled-input for-description overflow-auto" id="shopify-sync-log" style="max-height: 500px;"></div>
                        </div>

                    </div>
                </div>
                <div class="col-12 d-flex flex-row fill-width align-items-stretch m-0 justify-content-center">
                    <div class="card border-0 shadow-sm p-3 mb-3 rounded-sm">
                        <h5 class="w-auto border-bottom pb-2">Products in Shopify</h5>
                        <div class="d-flex flex-grow fill-width" id="shopify-product-list">
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

	async fetchProductCount() {

		try {
			const {message: {erpnextCount, shopifyCount, syncedCount}} =
				await frappe.call({
					method: 'ecommerce_integrations.shopify.page.shopify_import_products.' +
						'shopify_import_products.get_product_count'
				});

			this.wrapper.find('#count-products-shopify').text(shopifyCount);
			this.wrapper.find('#count-products-erpnext').text(erpnextCount);
			this.wrapper.find('#count-products-synced').text(syncedCount);

		} catch (error) {
			frappe.throw(__('Error fetching product count.'));
		}

	}

	async addTable() {

		const listElement = this.wrapper.find('#shopify-product-list')[0];
		const instanceCopy = this;
		this.shopifyProductTable = new frappe.DataTable(listElement, {
			columns: [
				{
					name: "Created On",
					align: "center",
					editable: false,
					focusable: false,
					sortable: true,
					// By default, sort the data by creation date (descending).
					sortOrder: "desc",
					width: 120

				},
				{
					name: 'Status',
					align: 'center',
					dropdown: false,
					editable: false,
					focusable: false,
					sortable: true,
					width: 125
				},
				{
					name: 'Action',
					align: 'center',
					editable: false,
					focusable: false,
					sortable: true,
					width: 100
				},
				{
					name: 'ID',
					align: 'center',
					editable: false,
					focusable: false,
					sortable: true,
					width: 150
				},
				{
					name: 'Name',
					align: "left",
					editable: false,
					focusable: false,
					sortable: true,
					width: 300
				},
				{
					name: 'SKUs',
					align: "left",
					editable: false,
					focusable: false,
					sortable: false,
					width: 300
				}
			],
			checkedRowStatus: false,
			data: await this.fetchShopifyProducts(),
			events: {
				onCheckRow(row) {
					instanceCopy.customOnCheckRows(row);
					instanceCopy.checkAllRowCheckBoxes();
				}
			},
			layout: 'fixed',
			noDataMessage: "No Items were retrieved",  // Message when there is no data.
			serialNoColumn: false,
			checkboxColumn: true
		});

		// Make scrollbar react to resize events and increase row height size.
		this.shopifyProductTable.style.setStyle(".dt-scrollable", {
			overflow: "visible",
			height: "70vh"
		});

		this.shopifyProductTable.style.setStyle(".dt-toast__message", {
			color: "#383838",
			backgroundColor: "#f3f3f3",
			border: "2px solid rgba(0, 0, 0, 0.25)",
			borderRadius: "8px",
			minWidth: "20%",
			fontSize: "1.05rem"
		});

		this.wrapper.find('.shopify-datatable-footer').show();

	}

	createDatatable(data = null) {
		// Delete old datatable.
		this.shopifyProductTable.events.onCheckRow = () => {}
		delete this.shopifyProductTable;

		const listElement = this.wrapper.find('#shopify-product-list')[0];
		const instanceCopy = this;
		this.shopifyProductTable = new frappe.DataTable(listElement, {
			columns: [
				{
					name: "Created On",
					align: "center",
					editable: false,
					focusable: false,
					sortable: true,
					// By default, sort the data by creation date (descending).
					sortOrder: "desc",
					width: 120

				},
				{
					name: 'Status',
					align: 'center',
					dropdown: false,
					editable: false,
					focusable: false,
					sortable: true,
					width: 125
				},
				{
					name: 'Action',
					align: 'center',
					editable: false,
					focusable: false,
					sortable: true,
					width: 100
				},
				{
					name: 'ID',
					align: 'center',
					editable: false,
					focusable: false,
					sortable: true,
					width: 150
				},
				{
					name: 'Name',
					align: "left",
					editable: false,
					focusable: false,
					sortable: true,
					width: 300
				},
				{
					name: 'SKUs',
					align: "left",
					editable: false,
					focusable: false,
					sortable: false,
					width: 300
				}
			],
			data: data,
			events: {
				onCheckRow(row) {
					instanceCopy.customOnCheckRows(row);
					instanceCopy.checkAllRowCheckBoxes();
				}
			},
			layout: 'fixed',
			noDataMessage: "No Items were retrieved",  // Message when there is no data.
			serialNoColumn: false,
			checkedRowStatus: false,
			checkboxColumn: true,
		});

		// Make scrollbar react to resize events and increase row height size.
		this.shopifyProductTable.style.setStyle(".dt-scrollable", {
			overflow: "visible",
			height: "70vh"
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

	async fetchShopifyProducts(from_ = null) {

		try {
			const {
				message: {
					products,
					nextUrl,
					prevUrl
				}
			} = await frappe.call({
				method: 'ecommerce_integrations.shopify.page.shopify_import_products.shopify_import_products.get_shopify_products',
				args: {from_}
			});
			this.nextUrl = nextUrl;
			this.prevUrl = prevUrl;

			const shopifyProducts = products.map((product) => ({
				// 'Image': product.image && product.image.src && `<img style="height: 50px" src="${product.image.src}">`,
				"Created On": product.created_at.replace("T", " ").split(" ")[0],
				'ID': product.id,
				'Name': product.title,
				'SKUs': product.variants && product.variants.map(a => `${a.sku}`).join(', '),
				'Status': this.getProductSyncStatus(product.synced),
				'Action': !product.synced ?
					`<button type="button" class="btn btn-default btn-xs btn-sync mx-2" data-product="${product.id}"> Sync </button>` :
					`<button type="button" class="btn btn-default btn-xs btn-resync mx-2" data-product="${product.id}"> Re-sync </button>`,
			}));

			return shopifyProducts;
		} catch (error) {
			frappe.throw(__('Error fetching products.'));
		}

	}

	getProductSyncStatus(status) {

		return status ?
			`<span class="indicator-pill green">Synced</span>` :
			`<span class="indicator-pill orange">Not Synced</span>`;

	}

	listen() {

		$(window).on("resize", () => {
			this.shopifyProductTable.setDimensions();
		});

		$(document).ready(() => {
			$("h3").css("overflow", "visible");
			$("h3").css("text-ellipsis", "unset");
		});

		this.wrapper.on("click", "#btn-sync-selected", e => {
			const _this = $(e.currentTarget);
			frappe.confirm( __(`Are you sure you want to proceed synching these ${this.selectedRows.size} products? Careful, this action is irreversible! Proceed Anyway?`),
				() => {
					_this.prop("disabled", true).text("Syncing...");
					this.syncSelected();
					_this.prop("disabled", false).text("Sync Selected Products");
				},
				() => {});
		});

		// sync a product from table
		this.wrapper.on('click', '.btn-sync', e => {

			const _this = $(e.currentTarget);

			_this.prop('disabled', true).text('Syncing...');

			const product = _this.attr('data-product');
			this.syncProduct(product)
				.then(status => {

					if (!status) {
						frappe.throw(__('Error syncing product'));
						_this.prop('disabled', false).text('Sync');
						return;
					}

					_this.parents('.dt-row')
						.find('.indicator-pill')
						.replaceWith(this.getProductSyncStatus(true));

					_this.replaceWith(`<button type="button" class="btn btn-default btn-xs btn-resync mx-2" data-product="${product}"> Re-sync </button>`);

				});

		});

		this.wrapper.on('click', '.btn-resync', e => {
			const _this = $(e.currentTarget);

			_this.prop('disabled', true).text('Syncing...');

			const product = _this.attr('data-product');
			this.resyncProduct(product)
				.then(status => {

					if (!status) {
						frappe.throw(__('Error syncing product'));
						return;
					}

					_this.parents('.dt-row')
						.find('.indicator-pill')
						.replaceWith(this.getProductSyncStatus(true));

					_this.prop('disabled', false).text('Re-sync');

				})
				.catch(ex => {
					_this.prop('disabled', false).text('Re-sync');
					frappe.throw(__('Error syncing Product'));
				});
		});

		// pagination
		this.wrapper.on('click', '.btn-prev,.btn-next', async e => {
			await this.refresh(e);
		});
	}

	async syncProduct(product) {

		const {message: status} = await frappe.call({
			method: 'ecommerce_integrations.shopify.page.shopify_import_products.shopify_import_products.sync_product',
			args: {product},
		});

		if (status)
			this.fetchProductCount();

		return status;

	}

	async resyncProduct(product) {

		const {message: status} = await frappe.call({
			method: 'ecommerce_integrations.shopify.page.shopify_import_products.shopify_import_products.resync_product',
			args: {product},
		});

		if (status)
			this.fetchProductCount();

		return status;

	}

	async refresh({currentTarget}) {

		const _this = $(currentTarget);

		$('.btn-paginate').prop('disabled', true);
		this.shopifyProductTable.showToastMessage('Loading...');

		const newData = await this.fetchShopifyProducts(
			_this.hasClass('btn-next') ? this.nextUrl : this.prevUrl);

		this.saveRowCheckBoxStates();
		this.createDatatable(newData);

		$('.btn-paginate').prop('disabled', false);
		this.shopifyProductTable.clearToastMessage();

		setTimeout(() => this.refreshRowCheckBoxes(), 500);
	}

	syncSelected() {

		this.checkSyncStatus();

		if (this.syncRunning) {
			frappe.msgprint(__('Sync already in progress'));
		} else {
			console.log(this.selectedRows);
			frappe.call({
				method: 'ecommerce_integrations.shopify.page.shopify_import_products.' +
					'shopify_import_products.import_selected_products',
				args: {
					"products": this.selectedRows
				}
			})
		}

		this.logSync();
	}

	logSync() {

		const _log = $('#shopify-sync-log');
		_log.parents('.card').show();
		_log.text(''); // clear logs

		// define counters here to prevent calling jquery every time
		const _syncedCounter = $('#count-products-synced');
		const _erpnextCounter = $('#count-products-erpnext');

		frappe.realtime.on('shopify.key.sync.selected.products', ({
																	  message,
																	  synced,
																	  done,
																	  error
																  }) => {

			message = `<pre class="mb-0">${message}</pre>`;
			_log.append(message);
			_log.scrollTop(_log[0].scrollHeight)

			if (synced) this.updateSyncedCount(_syncedCounter, _erpnextCounter);

			if (done) {
				frappe.realtime.off('shopify.key.sync.selected.products');
				this.toggleSyncSelectedButton(false);
				this.fetchProductCount();
				this.syncRunning = false;
			}

		})

	}

	toggleSyncSelectedButton(disable = true) {

		if (disable) {
			$("#btn-sync-selected").text(`Sync Selected Products (${this.selectedRows.size})`);
			$("#btn-sync-selected").css("display", "none");
			return;
		}

		$("#btn-sync-selected").css({
			"display": "flex",
			"justify-content": "center",
			"margin": "auto"
		}).text(`Sync Selected Products (${this.selectedRows.size})`);
	}

	updateSyncedCount(_syncedCounter, _erpnextCounter) {
		let _synced = parseFloat(_syncedCounter.text());
		let _erpnext = parseFloat(_erpnextCounter.text());

		_syncedCounter.text(_synced + 1);
		_erpnextCounter.text(_erpnext + 1);

	}

	checkAllRowCheckBoxes() {
		let oneChecked = this.selectedRows.size > 0;
		if (oneChecked) {
			this.toggleSyncSelectedButton(false);
			return;
		}
		this.toggleSyncSelectedButton(true);
	}

	saveRowCheckBoxStates() {
		for (let index = 0; index < 20; ++index) {
			let productId = getProductID(index);
			let checked = getCheckBoxStatus(index);
			this.allRowCheckBoxStates.set(productId, checked);
		}


	}

	refreshRowCheckBoxes() {
		for (let index = 0; index < 20; ++index) {
			let productId = getProductID(index);
			$(".dt-row-" + index)
				.find(".dt-cell__content--col-0")
				.children(":first")
				.prop("checked", this.allRowCheckBoxStates.get(productId) !== undefined && this.allRowCheckBoxStates.get(productId))
		}
	}


	customOnCheckRows(row) {
		let checkBoxHeader = $(".dt-row")
			.find(".dt-cell__content--header-0")
			.children(":first")
			.is(":checked");  // Get checkbox value.

		if (row === undefined) {
			// We have checked the top checkbox, signaling to add or remove everything.
			for (let index = 0; index < 20; ++index) {
				let productId = getProductID(index);

				if (productId !== undefined && checkBoxHeader) {
					this.selectedRows.add(productId);
					continue;
				}
				this.selectedRows.delete(productId);
			}
			console.log(this.selectedRows);
			return;
		}

		let whichRow = row[0].rowIndex;
		let isChecked = getCheckBoxStatus(whichRow);

		// If this is checked.
		if (isChecked) {
			this.selectedRows.add(row[4].content);
			console.log(this.selectedRows, whichRow);
			return;
		}

		this.selectedRows.delete(row[4].content);
		console.log(this.selectedRows, whichRow);
	}
}

const getProductID = (rowNum) => {
	return Number($(".dt-row-" + rowNum)
		.find(".dt-cell__content--col-4")  // Find the fifth column's content div (action).
		.attr("title")  // Get product ID.
		.split(" ")
		.join(""));  // Cleanup spaces.
}

const getCheckBoxStatus = (rowNum) => {
	return $(".dt-row-" + rowNum)
		.find(".dt-cell__content--col-0")  // Find the first column's content div (checkbox).
		.children(":first")
		.is(":checked");  // Check if the input under it is checked.
}
