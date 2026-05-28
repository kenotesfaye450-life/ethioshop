// Shop product listing

let allProducts = [];
let currentPage = 1;
let totalPages = 1;
let currentCategory = null;
let currentSearch = '';

async function loadCategories() {
    const categoryFilter = document.getElementById('categoryFilter');
    if (!categoryFilter) return;

    try {
        const res = await fetch(`${API_BASE_URL}/api/products/categories`);
        const data = await res.json();
        const categories = data.categories || data;
        categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category;
            option.textContent = category;
            categoryFilter.appendChild(option);
        });

        const urlParams = new URLSearchParams(window.location.search);
        const categoryParam = urlParams.get('category');
        if (categoryParam) {
            categoryFilter.value = categoryParam;
            currentCategory = categoryParam;
        }

        categoryFilter.addEventListener('change', (e) => {
            currentCategory = e.target.value || null;
            currentPage = 1;
            allProducts = [];
            const btn = document.getElementById('loadMoreBtn');
            if (btn) btn.remove();
            loadProducts(1, false);
            if (currentCategory) {
                window.history.pushState({}, '', `?category=${encodeURIComponent(currentCategory)}`);
            } else {
                window.history.pushState({}, '', 'shop.html');
            }
        });
    } catch (err) {
        console.error('Failed to load categories', err);
    }
}

async function loadProducts(page = 1, append = false) {
    const spinner = document.getElementById('loadingSpinner');
    const errorMessage = document.getElementById('errorMessage');
    const productGrid = document.getElementById('productGrid');

    try {
        if (spinner) spinner.style.display = 'block';
        if (errorMessage) errorMessage.style.display = 'none';
        if (!append && productGrid) productGrid.innerHTML = '';

        let url = `${API_ENDPOINTS.products}?page=${page}&limit=20`;
        if (currentCategory) url += `&category=${encodeURIComponent(currentCategory)}`;
        if (currentSearch) url += `&search=${encodeURIComponent(currentSearch)}`;

        const response = await fetch(url);
        const data = await response.json();

        const products = data.items || data.products || data;
        totalPages = data.pages || 1;
        currentPage = data.page || page;

        if (!append) allProducts = products;
        else allProducts = allProducts.concat(products);

        renderProducts(append ? products : allProducts);
        updateLoadMoreButton();
    } catch (error) {
        if (errorMessage) {
            errorMessage.textContent = `Error loading products: ${error.message}`;
            errorMessage.style.display = 'block';
        }
    } finally {
        if (spinner) spinner.style.display = 'none';
    }
}

function updateLoadMoreButton() {
    const existing = document.getElementById('loadMoreBtn');
    if (currentPage < totalPages) {
        if (!existing) {
            const btn = document.createElement('button');
            btn.id = 'loadMoreBtn';
            btn.className = 'btn btn-secondary';
            btn.style.cssText = 'display:block; margin:2rem auto; padding:0.75rem 2rem;';
            btn.textContent = 'Load More Products';
            btn.onclick = () => loadProducts(currentPage + 1, true);
            const grid = document.getElementById('productGrid');
            if (grid) grid.after(btn);
        }
    } else if (existing) {
        existing.remove();
    }
}

function renderProducts(products) {
    const productGrid = document.getElementById('productGrid');
    if (!productGrid) return;

    if (products.length === 0 && currentPage === 1) {
        productGrid.innerHTML = '<p class="no-products">No products found</p>';
        return;
    }

    products.forEach(product => {
        productGrid.appendChild(createProductCard(product));
    });
}

function createProductCard(product) {
    const card = document.createElement('div');
    card.className = 'product-card';

    const stockStatus = product.in_stock
        ? `<span class="stock-badge in-stock">In Stock</span>`
        : `<span class="stock-badge out-of-stock">Out of Stock</span>`;

    const img = product.thumbnail_url || product.image_url || 'assets/images/placeholder.jpg';

    card.innerHTML = `
        <a href="product.html?id=${product.id}" class="product-image" style="display:block;text-decoration:none;color:inherit;">
            <img src="${img}" alt="${product.name}" loading="lazy">
            ${stockStatus}
        </a>
        <div class="product-info">
            <h3><a href="product.html?id=${product.id}" style="color:inherit;text-decoration:none;">${product.name}</a></h3>
            ${(Number(product.stock || 0) > 0 && Number(product.stock) < 5) ? `<p class="low-stock-badge">⚠️ Only ${product.stock} left!</p>` : ''}
            ${(product.review_count > 0) ? `<p style="font-size:0.85rem;color:#666;">⭐ ${Number(product.avg_rating || 0).toFixed(1)} (${product.review_count} reviews)</p>` : ''}
            <p class="product-description">${product.description || ''}</p>
            <div class="product-footer">
                <span class="product-price">${product.price} ETB</span>
                <button class="btn btn-primary btn-sm"
                        onclick="addToCart(${product.id}); event.preventDefault();"
                        ${!product.in_stock ? 'disabled' : ''}>
                    Add to Cart
                </button>
            </div>
        </div>
    `;
    return card;
}

async function addToCart(productId) {
    const product = allProducts.find(p => p.id === productId);
    if (product) cart.addItem(product);
}

document.addEventListener('DOMContentLoaded', () => {
    loadCategories();
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                currentSearch = e.target.value.trim();
                currentPage = 1;
                allProducts = [];
                const btn = document.getElementById('loadMoreBtn');
                if (btn) btn.remove();
                loadProducts(1, false);
            }, 300);
        });
    }
    loadProducts(1, false);
});
