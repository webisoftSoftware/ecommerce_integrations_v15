frappe.provide('shopify');

frappe.pages['shopify-item-code-rename'].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper, title: 'Shopify Item Code Rename Tool', single_column: true
	});

	new shopify.ProductImporter(wrapper);

}

shopify.ProductImporter = class {

	constructor(wrapper) {

		this.wrapper = $(wrapper).find('.layout-main-section');
		this.page = wrapper.page;
		this.init();
		this.selectedRows = new Set();
		this.renameRunning = false;
		this.productCount = 0;

	}

	init() {
		frappe.run_serially([() => this.addMarkup(), () => this.addTable(), () => this.checkRenameStatus(), () => this.listen(),]);
	}

	async checkRenameStatus() {
		const jobs = await frappe.db.get_list("RQ Job", {filters: {"status": ("in", ["queued", "started"])}});
		const job = jobs.find(job => job.job_name === 'shopify.job.rename.selected_products');

		this.renameRunning = job !== undefined && (job.status === "queued" || job.status === "started");

		if (this.renameRunning) {
			this.logRename();
		}
	}

	addMarkup() {

		const _markup = $(`
            <div class="row w-100 d-flex justify-content-center align-items-stretch flex-column overflow: auto m-auto">
                <div class="col-12" id="rename-details" style="display: none;">
                    <div class="w-auto">
                        <div class="card d-flex border-0 shadow-sm p-3 mb-3 rounded-sm" style="background-color: var(--card-bg)">
                            <h5 class="border-bottom pb-2">Renaming Details</h5>
                            <div id="shopify-rename-info" class="w-auto">
                                    <button type="button" id="btn-rename-selected" class="btn btn-xl btn-primary w-100 font-weight-bold py-3" style="display: none;">Rename Selected Products</button>
                            </div>
                        </div>

                        <div class="card border-0 shadow-sm p-3 mb-3 rounded-sm" style="background-color: var(--card-bg); display: none;">
                            <h5 class="border-bottom pb-2">Rename Log</h5>
                            <div class="control-value like-disabled-input for-description overflow-auto" id="shopify-rename-log" style="max-height: 500px;"></div>
                        </div>

                    </div>
                </div>
                <div class="col-12 d-flex flex-row fill-width align-items-stretch m-0 justify-content-center">
                    <div class="card border-0 shadow-sm p-3 mb-3 rounded-sm">
                        <h5 class="w-auto border-bottom pb-2">Products in ERPNext</h5>
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

	async addTable() {

		const listElement = this.wrapper.find('#shopify-product-list')[0];
		let currentJSDate = new Date();

		// Set to last month.
		currentJSDate.setMonth(currentJSDate.getMonth() - 5);
		let timezoneOffset = currentJSDate.toString().split(" ")[5].slice(3);
		let currentISODate = currentJSDate.toISOString();

		// YYYY-MM-DDTHH:MM:SS[timezone difference]
		// Ex: 2024-08-30T17:28:18-0400
		let shopifyFormattedDate = currentISODate.slice(0, -5) + timezoneOffset;
		console.log(shopifyFormattedDate);
		const this_copy = this;

		this.shopifyProductTable = new frappe.DataTable(listElement, {
			columns: [{
				name: "Created On",
				align: "center",
				editable: false,
				focusable: false,
				sortable: true, // By default, sort the data by creation date (descending).
				sortOrder: "desc",
				width: 120

			}, {
				name: 'Status',
				align: 'center',
				dropdown: false,
				editable: false,
				focusable: false,
				sortable: true,
				width: 125
			}, {
				name: 'Action',
				align: 'center',
				editable: false,
				focusable: false,
				sortable: true,
				width: 100
			}, {
				name: 'ID',
				align: 'center',
				editable: false,
				focusable: false,
				sortable: true,
				width: 150
			}, {
				name: 'Name',
				align: "left",
				editable: false,
				focusable: false,
				sortable: true,
				width: 300
			}, {
				name: 'SKUs',
				align: "left",
				editable: false,
				focusable: false,
				sortable: false,
				width: 300
			}],
			events: {
				onCheckRow(_) {
					this_copy.toggleRenameSelectedButton();
				}
			},
			checkedRowStatus: true,
			clusterize: true,
			data: await this.fetchShopifyProducts(shopifyFormattedDate),
			layout: 'fixed',
			noDataMessage: "No Items were retrieved",  // Message when there is no data.
			serialNoColumn: false,
			checkboxColumn: true,
			inlineFilters: true,
		});

		// Add these style modifications after table initialization
		this.shopifyProductTable.style.setStyle('.dt-cell--col-0 input[type="checkbox"]', {
			'transition': 'none',
			'backface-visibility': 'hidden',
			'transform': 'translateZ(0)',
			'perspective': '1000px'
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

	async fetchShopifyProducts(fromDate) {

		try {
			const {
				message: {products}
			} = await frappe.call({
				method: 'ecommerce_integrations.shopify.page.shopify_import_products.shopify_import_products.get_shopify_products',
				args: {
					from_date: fromDate
				}
			});

			const shopifyProducts = products.map((product) => ({
				// 'Image': product.image && product.image.src && `<img style="height: 50px" src="${product.image.src}">`,
				"Created On": product.created_at.replace("T", " ").split(" ")[0],
				'ID': product.id,
				'Name': product.title,
				'SKUs': product.variants && product.variants.map(a => `${a.sku}`).join(', '),
				'Status': this.getProductSyncStatus(product.synced),
				'Action': `<button type="button" class="btn btn-default btn-xs btn-rename mx-2" data-product="${product.id}"> Rename </button>`,
			}));

			console.log(shopifyProducts);
			this.productCount = shopifyProducts.length;

			return shopifyProducts;
		} catch (error) {
			frappe.throw(__(`Error fetching products: ${error}`));
		}

	}

	getProductSyncStatus(status) {

		return status ? `<span class="indicator-pill green">Synced</span>` : `<span class="indicator-pill orange">Not Synced</span>`;

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

		this.wrapper.on("click", "#btn-rename-selected", e => {
			// Update all states at once
			for (let index = 0; index < this.productCount; ++index) {
				const isChecked = $(`.dt-row[data-row-index="${index}"]`)
					.find('.dt-cell__content--col-0 input[type="checkbox"]')
					.is(":checked");

				const productId = $(`.dt-row[data-row-index="${index}"]`)
					.find('.dt-cell__content--col-4')
					.prop("innerText");

				if (productId && isChecked) {
					this.selectedRows.add(productId);
				} else if (productId) {
					this.selectedRows.delete(productId);
				}
			}

			console.log(this.selectedRows);

			const _this = $(e.currentTarget);
			frappe.confirm(__(`Are you sure you want to proceed renaming these ${this.selectedRows.size} products to their SKU on Shopify? Careful, this action is irreversible! Proceed Anyway?`), () => {
				_this.prop("disabled", true).text("Renaming...");
				this.renameSelected();
				_this.prop("disabled", false).text("Rename Selected Products");
			}, () => {
			});
		});

		// Rename a product from table
		this.wrapper.on('click', '.btn-rename', e => {

			const _this = $(e.currentTarget);

			_this.prop('disabled', true).text('Renaming...');

			const product = _this.attr('data-product');
			this.renameProduct(product)
				.then(status => {

					if (status.code === 500) {
						_this.prop('disabled', false).text('Rename');
						frappe.throw(`${status.message}`);
					}
				})
		});
	}

	async renameProduct(product) {

		const {message: status} = await frappe.call({
			method: 'ecommerce_integrations.ecommerce_integrations.page.shopify_item_code_rename.rename_products.rename',
			args: {products: product},
		});

		return status;

	}

	renameSelected() {

		this.checkRenameStatus();

		if (this.renameRunning) {
			frappe.msgprint(__('Rename already in progress'));
		} else {
			console.log([...this.selectedRows].map(id => `${id}`).join(", "));
			frappe.call({
				method: 'ecommerce_integrations.ecommerce_integrations.page.shopify_item_code_rename.rename_products.rename',
				args: {
					products: [...this.selectedRows].map(id => `${id}`).join(",")
				},
				freeze: true
			})
		}

		this.logRename();
	}

	logRename() {

		const _log = $('#shopify-rename-log');
		_log.parents('.card').show();
		_log.text(''); // clear logs

		frappe.realtime.on('shopify.key.rename.selected.products', ({
																	  message,
																	  synced,
																	  done,
																	  error
																  }) => {

			message = `<pre class="mb-0">${message}</pre>`;
			_log.append(message);
			_log.scrollTop(_log[0].scrollHeight)

			if (done) {
				frappe.realtime.off('shopify.key.rename.selected.products');
				this.toggleRenameSelectedButton();
				this.renameRunning = false;
			}

		})

	}

	toggleRenameSelectedButton() {
		const toast = $(".dt-toast__message");
		if (toast.length === 1) {
			$("#rename-details").css({
				"visibility": "visible",
				"display": "flex",
				"justify-content": "center",
				"align-items": "stretch",
				"margin": "auto"
			});
			$("#btn-rename-selected")
				.css({
					"visibility": "visible",
					"display": "flex",
					"justify-content": "center",
					"margin": "auto"
				})
				.text(`Rename Selected Products (${toast[0].innerText.slice(0, toast[0].innerText.indexOf(" "))})`);
			return;
		}

		$("#rename-details").css({
			"display": "none"
		});
		$("#btn-rename-selected")
			.css({
				"display": "none",
			});
	}
}

const getProductID = (row, rowNum = null) => {
	if (rowNum !== null) {
		return Number($(".dt-row-" + rowNum)
			.find(".dt-cell__content--col-4")  // Find the fifth column's content div (action).
			.attr("title")  // Get product ID.
			.split(" ")
			.join(""));  // Cleanup spaces.
	}

	console.log(row);
	return Number(row.find(".dt-cell__content--col-4")  // Find the fifth column's content div (action).
		.attr("title")  // Get product ID.
		.split(" ")
		.join(""));  // Cleanup spaces.
}
