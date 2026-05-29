// Product detail page — gallery + add to cart

let productData = null;

async function loadProductDetail() {
    const params = new URLSearchParams(window.location.search);
    const id = params.get('id');
    const container = document.getElementById('productDetail');
    if (!id) {
        container.innerHTML = '<p>Product not found.</p>';
        return;
    }

    try {
        const res = await fetch(`${API_ENDPOINTS.products}/${id}`);
        const data = await res.json();
        if (!data.success) throw new Error(data.error?.message || 'Not found');
        productData = data.product;
        renderProductDetail();
    } catch (err) {
        container.innerHTML = `<p class="error-message">${err.message}</p>`;
    }
}

function renderProductDetail() {
    const p = productData;
    const container = document.getElementById('productDetail');
    const images = (p.images && p.images.length)
        ? [...p.images].sort((a, b) => (b.is_primary - a.is_primary) || (a.sort_order - b.sort_order))
        : [{ image_url: p.image_url, thumbnail_url: p.thumbnail_url, is_primary: true }];

    const mainSrc = images[0]?.image_url || p.image_url || 'assets/images/placeholder.jpg';
    const thumbs = images.filter(img => img.thumbnail_url || img.image_url);

    container.innerHTML = `
        <div class="product-detail-grid">
            <div class="product-gallery">
                <div class="gallery-main">
                    <img id="galleryMain" src="${mainSrc}" alt="${p.name}">
                </div>
                ${thumbs.length > 1 ? `
                    <div class="gallery-thumbs">
                        ${thumbs.map((img, i) => `
                            <button type="button" class="gallery-thumb ${i === 0 ? 'active' : ''}"
                                    onclick="setGalleryImage('${img.image_url}', this)">
                                <img src="${img.thumbnail_url || img.image_url}" alt="">
                            </button>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
            <div class="product-detail-info">
                <p class="product-category">${p.category || ''}</p>
                <h1>${p.name}</h1>
                <p class="product-price-lg">${p.price} ETB</p>
                <p>${p.in_stock ? '<span class="stock-badge in-stock">In Stock</span>' : '<span class="stock-badge out-of-stock">Out of Stock</span>'}</p>
                ${(Number(p.stock || 0) > 0 && Number(p.stock) < 5) ? `<p class="low-stock-badge">⚠️ Only ${p.stock} left!</p>` : ''}
                ${p.review_count > 0 ? `<p>⭐ ${Number(p.avg_rating || 0).toFixed(1)} (${p.review_count} reviews)</p>` : '<p>No reviews yet.</p>'}
                <p class="product-description">${p.description || ''}</p>
                <button class="btn btn-primary" id="addToCartBtn"
                        ${!p.in_stock ? 'disabled' : ''}
                        onclick="addDetailToCart()">Add to Cart</button>
                <a href="shop.html" class="btn btn-secondary" style="margin-left:0.5rem;">← Back to Shop</a>
                <div class="cart-container" style="margin-top:1.5rem;">
                    <h3>Ask about stock</h3>
                    <textarea id="stockQuestion" rows="2" placeholder="e.g. Do you have size 42 in black?" style="width:100%;margin-bottom:0.5rem;"></textarea>
                    <button type="button" class="btn btn-secondary" onclick="submitStockQuestion()">Send question</button>
                    <p id="stockQuestionMsg" style="font-size:0.9rem;margin-top:0.5rem;"></p>
                </div>
            </div>
        </div>
        ${Array.isArray(p.reviews) && p.reviews.length ? `
            <div class="cart-container">
                <h3>Recent Customer Reviews</h3>
                ${p.reviews.map(r => `<p><strong>${'⭐'.repeat(Math.max(1, Number(r.rating || 0)))}</strong> ${r.comment || ''}</p>`).join('')}
            </div>
        ` : ''}
    `;
    document.title = `${p.name} - EthioShop`;
}

function setGalleryImage(url, btn) {
    document.getElementById('galleryMain').src = url;
    document.querySelectorAll('.gallery-thumb').forEach(el => el.classList.remove('active'));
    btn.classList.add('active');
}

async function addDetailToCart() {
    if (typeof requireLoginForAction === 'function') {
        const phone = await requireLoginForAction('add this item to your cart');
        if (!phone) return;
    }
    if (productData) cart.addItem(productData);
}

async function submitStockQuestion() {
    const q = document.getElementById('stockQuestion')?.value?.trim();
    const msg = document.getElementById('stockQuestionMsg');
    if (!q) { if (msg) msg.textContent = 'Enter a question.'; return; }
    let phone = sessionStorage.getItem('userPhone');
    if (!phone && typeof requireLoginForAction === 'function') {
        phone = await requireLoginForAction('ask about this product');
    }
    if (!phone) return;
    try {
        await QuestionAPI.ask(productData.id, { phone, question: q });
        if (msg) msg.textContent = 'Question sent! Check your dashboard for the answer.';
        document.getElementById('stockQuestion').value = '';
    } catch (e) {
        if (msg) msg.textContent = e.message;
    }
}

document.addEventListener('DOMContentLoaded', loadProductDetail);
