// =============================================
// OGONG HARDWARE POS SCRIPT
// =============================================

let products = [];
let transactionItems = [];
let receiptSale = null;
let currentSelectedProduct = null;


// =============================================
// INITIALIZE POS
// =============================================

async function initPOS() {

    const user = requireAuth();

    if (!user) return;


    // Setup modals

    setupModalClose('receipt-modal');
    setupModalClose('quantity-modal');


    // =============================================
    // SEARCH PRODUCTS
    // =============================================

    document.getElementById('pos-search')
        ?.addEventListener('input', () => {

            clearTimeout(window._posSearchTimer);

            window._posSearchTimer = setTimeout(
                loadProducts,
                300
            );

        });


    // =============================================
    // CATEGORY FILTER
    // =============================================

    document.getElementById('pos-category')
        ?.addEventListener(
            'change',
            renderProductGrid
        );


    // =============================================
    // PAYMENT METHOD
    // =============================================

    document.getElementById('payment-method')
        ?.addEventListener(
            'change',
            handlePaymentMethod
        );


    // =============================================
    // AMOUNT RECEIVED
    // =============================================

    document.getElementById('amount-received')
        ?.addEventListener(
            'input',
            updateTotals
        );


    // =============================================
    // COMPLETE SALE
    // =============================================

    document.getElementById('complete-sale-btn')
        ?.addEventListener(
            'click',
            completeSale
        );


    // =============================================
    // NEW SALE
    // =============================================

    document.getElementById('new-sale-btn')
        ?.addEventListener(
            'click',
            startNewSale
        );


    // =============================================
    // RECEIPT NEW SALE
    // =============================================

    document.getElementById('receipt-new-sale-btn')
        ?.addEventListener(
            'click',
            () => {

                closeModal('receipt-modal');

                receiptSale = null;

                startNewSale();

            }
        );


    // =============================================
    // PRINT RECEIPT
    // =============================================

    document.getElementById('print-receipt-btn')
        ?.addEventListener(
            'click',
            () => window.print()
        );


    // =============================================
    // QUANTITY MODAL CONTROLS
    // =============================================

    document.getElementById('qm-increase')
        ?.addEventListener(
            'click',
            () => {

                const input =
                    document.getElementById('qm-quantity');

                input.value =
                    Number(input.value || 0) + 1;

            }
        );


    document.getElementById('qm-decrease')
        ?.addEventListener(
            'click',
            () => {

                const input =
                    document.getElementById('qm-quantity');

                input.value =
                    Math.max(
                        1,
                        Number(input.value || 1) - 1
                    );

            }
        );


    // =============================================
    // ADD PRODUCT TO SALE
    // =============================================

    document.getElementById('qm-add-btn')
        ?.addEventListener(
            'click',
            addProductToTransaction
        );


    // =============================================
    // LOAD INITIAL DATA
    // =============================================

    await loadCategories();

    await loadProducts();

    handlePaymentMethod();

}


// =============================================
// PAYMENT METHOD HANDLER
// =============================================

function handlePaymentMethod() {

    const paymentMethod =
        document.getElementById('payment-method')
            ?.value;

    const cashFields =
        document.getElementById('cash-fields');

    const amountReceived =
        document.getElementById('amount-received');


    // Show cash input only for CASH

    if (cashFields) {

        cashFields.style.display =
            paymentMethod === 'Cash'
                ? 'block'
                : 'none';

    }


    // Clear amount received if not cash

    if (
        paymentMethod !== 'Cash' &&
        amountReceived
    ) {

        amountReceived.value = '';

    }


    updateTotals();

}


// =============================================
// LOAD CATEGORIES
// =============================================

async function loadCategories() {

    try {

        const categories =
            await apiFetch('/categories');


        const select =
            document.getElementById(
                'pos-category'
            );


        if (!select) return;


        select.innerHTML =
            '<option value="">All Categories</option>';


        categories.forEach(category => {

            const option =
                document.createElement('option');

            option.value =
                category.category_name;

            option.textContent =
                category.category_name;

            select.appendChild(option);

        });

    } catch (error) {

        showAlert(
            'Unable to load categories.',
            'danger'
        );

    }

}


// =============================================
// LOAD PRODUCTS
// =============================================

async function loadProducts() {

    try {

        const searchInput =
            document.getElementById('pos-search');


        const search =
            searchInput
                ? searchInput.value.trim()
                : '';


        const endpoint =
            `/products${
                search
                    ? `?search=${encodeURIComponent(search)}`
                    : ''
            }`;


        const data =
            await apiFetch(endpoint);


        products = data;


        renderProductGrid();

    } catch (error) {

        showAlert(
            'Unable to load products.',
            'danger'
        );

    }

}


// =============================================
// PRODUCT IMAGE
// =============================================

function getProductImage(name) {

    const n =
        (name || '')
            .toLowerCase();


    const imageMap = [
        ['wire brush', 'images/brush1.jpg'],
        ['paint brush', 'images/brush.jpg'],
        ['cement', 'images/cement.jpg'],
        ['concrete', 'images/cement.jpg'],
        ['adjust', 'images/adjust.jpg'],
        ['wrench', 'images/adjust.jpg'],
        ['brush', 'images/brush.jpg'],
        ['hammer', 'images/hammer.jpg'],
        ['helmet', 'images/helmet.jpg'],
        ['hard hat', 'images/helmet.jpg'],
        ['nail', 'images/lansang.jpg'],
        ['lansang', 'images/lansang.jpg'],
        ['shovel', 'images/pala.jpg'],
        ['spade', 'images/pala.jpg'],
        ['pala', 'images/pala.jpg'],
        ['pvc', 'images/pvc.jpg'],
        ['pipe', 'images/pvc.jpg'],
        ['hose', 'images/pvc.jpg'],
        ['thhn', 'images/THHN.webp'],
        ['wire', 'images/THHN.webp']
    ];


    for (const [keyword, image] of imageMap) {

        if (n.includes(keyword)) {

            return image;

        }

    }


    return null;

}


// =============================================
// RENDER PRODUCT GRID
// =============================================

function renderProductGrid() {

    const grid =
        document.getElementById(
            'product-grid'
        );


    if (!grid) return;


    const category =
        document.getElementById(
            'pos-category'
        )?.value || '';


    grid.innerHTML = '';


    const filteredProducts =
        products.filter(product => {

            return (
                !category ||
                product.category_name === category
            );

        });


    if (!filteredProducts.length) {

        grid.innerHTML = `
            <div class="no-products">
                No products found.
            </div>
        `;

        return;

    }


    filteredProducts.forEach(product => {

        const outOfStock =
            Number(product.stock_quantity) <= 0;


        const card =
            document.createElement('div');


        card.className =
            'product-card';


        const image =
            getProductImage(
                product.product_name
            );


        const price =
            Number(product.price || 0);


        card.innerHTML = `

            <div class="product-image">

                ${image ? `
                    <img
                        src="${image}"
                        alt="${product.product_name}"
                        onerror="this.hidden=true; this.nextElementSibling.hidden=false"
                    >
                ` : ''}

                <span class="product-image-placeholder" ${image ? 'hidden' : ''} aria-hidden="true">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M3 7.5 12 3l9 4.5v9L12 21l-9-4.5z"></path>
                        <path d="m3.5 7.7 8.5 4.4 8.5-4.4M12 12.1V21"></path>
                    </svg>
                </span>

            </div>


            <div class="product-name">

                ${product.product_name}

            </div>


        `;


        card.setAttribute('role', 'button');
        card.setAttribute('tabindex', outOfStock ? '-1' : '0');
        card.setAttribute('aria-label', `Add ${product.product_name} to sale`);
        card.setAttribute('aria-disabled', String(outOfStock));

        if (!outOfStock) {
            const selectProduct = () => showQuantityModal(product);
            card.addEventListener('click', selectProduct);
            card.addEventListener('keydown', event => {
                if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault();
                    selectProduct();
                }
            });
        }


        grid.appendChild(card);

    });

}


// =============================================
// SHOW QUANTITY MODAL
// =============================================

function showQuantityModal(product) {

    currentSelectedProduct = product;


    const nameElement =
        document.getElementById(
            'qm-product-name'
        );


    const stockElement =
        document.getElementById(
            'qm-product-stock'
        );


    const quantityElement =
        document.getElementById(
            'qm-quantity'
        );


    const alertElement =
        document.getElementById(
            'qm-alert'
        );


    if (nameElement) {

        nameElement.textContent =
            product.product_name;

    }


    if (stockElement) {

        stockElement.textContent =
            `Available: ${product.stock_quantity}`;

    }


    if (quantityElement) {

        quantityElement.value = 1;

        quantityElement.max =
            product.stock_quantity;

    }


    if (alertElement) {

        alertElement.innerHTML = '';

    }


    openModal('quantity-modal');

}


// =============================================
// ADD PRODUCT TO TRANSACTION
// =============================================

function addProductToTransaction() {

    const quantity =
        Number(
            document.getElementById(
                'qm-quantity'
            ).value
        ) || 0;


    if (!currentSelectedProduct) return;


    const alertElement =
        document.getElementById(
            'qm-alert'
        );


    // Validate quantity

    if (quantity <= 0) {

        alertElement.innerHTML = `
            <div class="alert alert-danger">
                Enter a valid quantity.
            </div>
        `;

        return;

    }


    // Validate stock

    if (
        quantity >
        Number(currentSelectedProduct.stock_quantity)
    ) {

        alertElement.innerHTML = `
            <div class="alert alert-danger">
                Insufficient stock.
                Available:
                ${currentSelectedProduct.stock_quantity}
            </div>
        `;

        return;

    }


    const existingItem =
        transactionItems.find(item => {

            return (
                item.product_id ===
                currentSelectedProduct.id
            );

        });


    if (existingItem) {

        const newQuantity =
            existingItem.quantity +
            quantity;


        if (
            newQuantity >
            Number(
                currentSelectedProduct.stock_quantity
            )
        ) {

            alertElement.innerHTML = `
                <div class="alert alert-danger">

                    Insufficient stock.

                    Available:
                    ${currentSelectedProduct.stock_quantity}

                </div>
            `;

            return;

        }


        existingItem.quantity =
            newQuantity;


        existingItem.subtotal =
            Number(
                (
                    existingItem.price *
                    newQuantity
                ).toFixed(2)
            );


        existingItem.cost_subtotal =
            Number(
                (
                    existingItem.cost *
                    newQuantity
                ).toFixed(2)
            );

    } else {

        const sellingPrice =
            Number(
                currentSelectedProduct.price
            );


        const cost =
            Number(
                currentSelectedProduct.cost || 0
            );


        transactionItems.push({

            product_id:
                currentSelectedProduct.id,

            product_name:
                currentSelectedProduct.product_name,

            quantity,

            price:
                sellingPrice,

            cost,

            subtotal:
                Number(
                    (
                        sellingPrice *
                        quantity
                    ).toFixed(2)
                ),

            cost_subtotal:
                Number(
                    (
                        cost *
                        quantity
                    ).toFixed(2)
                )

        });

    }


    closeModal('quantity-modal');


    renderTransaction();

}


// =============================================
// UPDATE TOTALS
// =============================================

function updateTotals() {

    const total =
        transactionItems.reduce(
            (sum, item) =>
                sum + Number(item.subtotal),
            0
        );


    const totalCost =
        transactionItems.reduce(
            (sum, item) =>
                sum +
                Number(
                    item.cost_subtotal ||
                    (
                        Number(item.cost || 0) *
                        Number(item.quantity || 0)
                    )
                ),
            0
        );


    const totalProfit =
        total - totalCost;


    const totalElement =
        document.getElementById(
            'transaction-total'
        );


    if (totalElement) {

        totalElement.textContent =
            formatCurrency(total);

    }


    // Optional Total Cost element
    // Add id="transaction-cost" in POS HTML

    const costElement =
        document.getElementById(
            'transaction-cost'
        );


    if (costElement) {

        costElement.textContent =
            formatCurrency(totalCost);

    }


    // Optional Total Profit element
    // Add id="transaction-profit" in POS HTML

    const profitElement =
        document.getElementById(
            'transaction-profit'
        );


    if (profitElement) {

        profitElement.textContent =
            formatCurrency(totalProfit);

    }


    const paymentMethod =
        document.getElementById(
            'payment-method'
        )?.value;


    const received =
        Number(
            document.getElementById(
                'amount-received'
            )?.value
        ) || 0;


    let change = 0;


    if (paymentMethod === 'Cash') {

        change =
            Math.max(
                0,
                received - total
            );

    }


    const changeElement =
        document.getElementById(
            'transaction-change'
        );


    if (changeElement) {

        changeElement.textContent =
            formatCurrency(change);

    }

}


// =============================================
// RENDER CURRENT TRANSACTION
// =============================================

function renderTransaction() {

    const body =
        document.getElementById(
            'transaction-body'
        );


    if (!body) return;


    body.innerHTML = '';


    if (!transactionItems.length) {

        body.innerHTML = `

            <tr>

                <td colspan="7" class="pos-empty-row">

                    No items added.

                </td>

            </tr>

        `;


        updateTotals();

        return;

    }


    transactionItems.forEach(
        (item, index) => {

            const profitPerUnit =
                Number(item.price) -
                Number(item.cost || 0);


            const totalProfit =
                Number(item.subtotal) -
                Number(
                    item.cost_subtotal ||
                    (
                        Number(item.cost || 0) *
                        Number(item.quantity)
                    )
                );


            const row =
                document.createElement('tr');


            row.innerHTML = `

                <td colspan="7">
                    <div class="sale-item">
                        <div class="sale-item-heading">
                            <span class="sale-item-name">${item.product_name}</span>
                            <button class="button sale-item-remove" type="button" onclick="window.posRemoveTransactionItem(${index})">Remove</button>
                        </div>
                        <div class="sale-item-quantity">
                            <label for="sale-quantity-${index}">Qty</label>
                            <input id="sale-quantity-${index}" type="number" min="1" value="${item.quantity}" onchange="window.posUpdateItemQuantity(${index}, this.value)">
                        </div>
                        <div class="sale-item-details">
                            <div class="sale-item-detail">Unit price<strong>${formatCurrency(item.price)}</strong></div>
                            <div class="sale-item-detail">Subtotal<strong>${formatCurrency(item.subtotal)}</strong></div>
                            <div class="sale-item-detail">Profit<strong>${formatCurrency(totalProfit)}</strong></div>
                        </div>
                    </div>
                </td>

            `;


            body.appendChild(row);

        }
    );


    updateTotals();

}


// =============================================
// UPDATE ITEM QUANTITY
// =============================================

window.posUpdateItemQuantity =
function (index, value) {

    const quantity =
        Number(value);


    if (quantity <= 0) {

        showAlert(
            'Quantity must be at least 1.',
            'danger'
        );

        renderTransaction();

        return;

    }


    const item =
        transactionItems[index];


    const product =
        products.find(product =>
            product.id === item.product_id
        );


    if (!product) return;


    if (
        quantity >
        Number(product.stock_quantity)
    ) {

        showAlert(
            `Insufficient stock. Available: ${product.stock_quantity}`,
            'danger'
        );

        renderTransaction();

        return;

    }


    item.quantity =
        quantity;


    item.subtotal =
        Number(
            (
                item.price *
                quantity
            ).toFixed(2)
        );


    item.cost_subtotal =
        Number(
            (
                Number(item.cost || 0) *
                quantity
            ).toFixed(2)
        );


    renderTransaction();

};


// =============================================
// REMOVE TRANSACTION ITEM
// =============================================

window.posRemoveTransactionItem =
function (index) {

    transactionItems.splice(
        index,
        1
    );


    renderTransaction();

};


// =============================================
// COMPLETE SALE
// =============================================

async function completeSale() {

    if (!transactionItems.length) {

        showAlert(
            'No items in current sale. Select products to begin.',
            'danger'
        );

        return;

    }


    const user =
        requireAuth();


    if (!user) return;


    const paymentMethod =
        document.getElementById(
            'payment-method'
        ).value;


    const total =
        transactionItems.reduce(
            (sum, item) =>
                sum + Number(item.subtotal),
            0
        );


    let amountReceived = null;


    // =============================================
    // CASH VALIDATION
    // =============================================

    if (paymentMethod === 'Cash') {

        amountReceived =
            Number(
                document.getElementById(
                    'amount-received'
                ).value
            );


        if (
            !amountReceived ||
            amountReceived <= 0
        ) {

            showAlert(
                'Enter the amount received.',
                'danger'
            );

            return;

        }


        if (amountReceived < total) {

            showAlert(
                'Amount received is insufficient.',
                'danger'
            );

            return;

        }

    }


    // =============================================
    // PREPARE SALE DATA
    // =============================================

    const payload = {

        user_id:
            user.id,

        payment_method:
            paymentMethod,

        amount_received:
            amountReceived,

        current_transaction:
            transactionItems.map(item => ({

                product_id:
                    item.product_id,

                product_name:
                    item.product_name,

                quantity:
                    item.quantity,

                price:
                    item.price,

                cost:
                    item.cost,

                subtotal:
                    item.subtotal

            }))

    };


    try {

        const result =
            await apiFetch(
                '/sales',
                {

                    method:
                        'POST',

                    body:
                        JSON.stringify(payload)

                }
            );


        receiptSale =
            result;


        await showReceipt(result);


        transactionItems = [];


        renderTransaction();


        await loadProducts();


        document.getElementById(
            'amount-received'
        ).value = '';


    } catch (error) {

        showAlert(
            error.message,
            'danger'
        );

    }

}


// =============================================
// START NEW SALE
// =============================================

function startNewSale() {

    transactionItems = [];


    currentSelectedProduct = null;


    const amountInput =
        document.getElementById(
            'amount-received'
        );


    if (amountInput) {

        amountInput.value = '';

    }


    renderTransaction();


    updateTotals();

}


// =============================================
// SHOW RECEIPT
// =============================================

async function showReceipt(result) {

    const saleId =
        result.sale_id ||
        result.id;


    const saleDetail =
        await apiFetch(
            `/sales/${saleId}`
        );


    const container =
        document.getElementById(
            'receipt-content'
        );


    if (!container) return;


    const rows =
        saleDetail.items
            .map(item => {

                const itemCost =
                    Number(item.cost || 0);


                const itemProfit =
                    Number(item.subtotal) -
                    (
                        itemCost *
                        Number(item.quantity)
                    );


                return `

                    <tr>

                        <td>
                            ${item.product_name}
                        </td>

                        <td>
                            ${item.quantity}
                        </td>

                        <td>
                            ${formatCurrency(item.price)}
                        </td>

                        <td>
                            ${formatCurrency(itemCost)}
                        </td>

                        <td>
                            ${formatCurrency(item.subtotal)}
                        </td>

                    </tr>

                `;

            })
            .join('');


    container.innerHTML = `

        <div class="table-card">

            <p>

                <strong>
                    Invoice:
                </strong>

                ${saleDetail.invoice_number}

            </p>


            <p>

                <strong>
                    Date:
                </strong>

                ${new Date(
                    saleDetail.sale_date
                ).toLocaleString()}

            </p>


            <p>

                <strong>
                    Cashier:
                </strong>

                ${saleDetail.cashier}

            </p>


            <div class="table-responsive">

                <table>

                    <thead>

                        <tr>

                            <th>
                                Product
                            </th>

                            <th>
                                Qty
                            </th>

                            <th>
                                Price
                            </th>

                            <th>
                                Cost
                            </th>

                            <th>
                                Amount
                            </th>

                        </tr>

                    </thead>


                    <tbody>

                        ${rows}

                    </tbody>

                </table>

            </div>


            <p>

                <strong>
                    Total:
                </strong>

                ${formatCurrency(
                    saleDetail.total_amount
                )}

            </p>


            <p>

                <strong>
                    Payment:
                </strong>

                ${saleDetail.payment_method}

            </p>


            ${
                saleDetail.payment_method === 'Cash'

                    ? `

                        <p>

                            <strong>
                                Received:
                            </strong>

                            ${formatCurrency(
                                saleDetail.amount_received
                            )}

                        </p>


                        <p>

                            <strong>
                                Change:
                            </strong>

                            ${formatCurrency(
                                saleDetail.change_amount
                            )}

                        </p>

                    `

                    : ''
            }


            ${
                saleDetail.payment_method === 'Credit/Utang'

                    ? `

                        <p
                            style="
                                margin-top:16px;
                                font-weight:700;
                            "
                        >

                            ⚠ This transaction is recorded as CREDIT / UTANG.

                        </p>

                    `

                    : ''
            }


            <p
                style="
                    margin-top:16px;
                    font-weight:700;
                "
            >

                THANK YOU

            </p>

        </div>

    `;


    openModal('receipt-modal');

}