const PRODUCT_CATEGORIES = [
    'Shoes', 'Clothing', 'Watches', 'Phones', 'Beauty', 'Bags', 'Electronics',
    'Home Essentials', 'Perfumes', 'Sports', 'Earphones', 'Blankets', 'Jewelry', 'Thermoses',
];

let allProducts = [];
let currentProductPage = 1;
let editingImages = [];

function buildCategoryOptions(selectedValue = '') {
    return PRODUCT_CATEGORIES.map(c =>
        `<option value="${c}" ${c === selectedValue ? 'selected' : ''}>${c}</option>`
    ).join('');
}

function getCategoryValue() {
    const custom = document.getElementById('customCategory').value.trim();
    if (custom) return custom;
    return document.getElementById('category').value;
}

function renderImageGallery() {
    const box = document.getElementById('existingImages');
    if (!box) return;
    if (!editingImages.length) {
        box.innerHTML = '<small style="color:#888;">No images yet. Upload below after saving.</small>';
        return;
    }
    box.innerHTML = editingImages.map(img => `
        <div style="position:relative;border:1px solid #ddd;border-radius:6px;padding:4px;">
            <img src="${img.thumbnail_url || img.image_url}" style="width:72px;height:72px;object-fit:cover;border-radius:4px;">
            ${img.is_primary ? '<span style="font-size:0.7rem;color:green;">Primary</span>' : `
                <button type="button" class="btn-small" onclick="setPrimaryImage(${img.id})">Set primary</button>
            `}
            <button type="button" class="btn-small btn-danger" onclick="deleteImage(${img.id})">×</button>
        </div>
    `).join('');
}

async function loadProducts(page = 1) {
    currentProductPage = page;
    const container = document.getElementById('productsContainer');
    container.innerHTML = '<p style="color:#999;padding:1rem;">Loading...</p>';

    try {
        const res = await apiFetch(`/products/manage?page=${page}&limit=20`);
        const data = await res.json();
        if (!data.success) throw new Error(data.error?.message);

        allProducts = data.items || data.products || [];
        if (!allProducts.length) {
            container.innerHTML = '<p style="color:#999;padding:1rem;">No products yet.</p>';
            return;
        }

        container.innerHTML = `
            <table class="products-table">
                <thead><tr>
                    <th>ID</th><th>Name</th><th>Category</th>
                    <th>Cost</th><th>Price</th><th>Stock</th><th>Status</th><th>Actions</th>
                </tr></thead>
                <tbody>
                    ${allProducts.map(p => `
                        <tr>
                            <td>#${p.id}</td>
                            <td>${p.name}</td>
                            <td>${p.category}</td>
                            <td>${(p.cost_price != null ? p.cost_price : 0).toFixed(2)}</td>
                            <td>${p.price.toFixed(2)}</td>
                            <td>${p.stock}</td>
                            <td><span class="status-badge ${p.in_stock ? 'status-confirmed' : 'status-rejected'}">
                                ${p.in_stock ? 'In Stock' : 'Out of Stock'}
                            </span></td>
                            <td>
                                <button onclick="editProduct(${p.id})" class="btn-small">Edit</button>
                                <button onclick="deleteProduct(${p.id})" class="btn-small btn-danger">Delete</button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
            ${data.pages > 1 ? `
                <div style="margin-top:1rem;display:flex;gap:0.5rem;align-items:center;">
                    ${page > 1 ? `<button onclick="loadProducts(${page - 1})" class="btn-small">← Prev</button>` : ''}
                    <span>Page ${data.page} of ${data.pages}</span>
                    ${page < data.pages ? `<button onclick="loadProducts(${page + 1})" class="btn-small">Next →</button>` : ''}
                </div>
            ` : ''}
        `;
    } catch (err) {
        container.innerHTML = `<p style="color:red;">Error: ${err.message}</p>`;
    }
}

function showAddProduct() {
    document.getElementById('modalTitle').textContent = 'Add Product';
    document.getElementById('productForm').reset();
    document.getElementById('productId').value = '';
    document.getElementById('category').innerHTML = `<option value="">Select category</option>${buildCategoryOptions()}`;
    editingImages = [];
    renderImageGallery();
    document.getElementById('productModal').style.display = 'block';
}

async function editProduct(productId) {
    try {
        const res = await apiFetch(`/products/${productId}/manage`);
        const data = await res.json();
        if (!data.success) throw new Error(data.error?.message);
        const p = data.product;

        document.getElementById('modalTitle').textContent = 'Edit Product';
        document.getElementById('productId').value = p.id;
        document.getElementById('productName').value = p.name;
        document.getElementById('productDescription').value = p.description || '';
        document.getElementById('sellingPrice').value = p.price;
        document.getElementById('costPrice').value = p.cost_price;
        document.getElementById('stock').value = p.stock;
        document.getElementById('imageUrl').value = p.image_url || '';
        document.getElementById('customCategory').value = '';
        document.getElementById('category').innerHTML = `<option value="">Select category</option>${buildCategoryOptions(p.category)}`;
        document.getElementById('productImages').value = '';
        editingImages = p.images || [];
        renderImageGallery();
        document.getElementById('productModal').style.display = 'block';
    } catch (err) {
        alert('Error: ' + err.message);
    }
}

async function uploadProductImages(productId) {
    const input = document.getElementById('productImages');
    if (!input.files || !input.files.length) return;

    const fd = new FormData();
    Array.from(input.files).forEach(f => fd.append('files', f));

    const res = await fetch(`${ADMIN_API}/products/${productId}/images`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${getToken()}` },
        body: fd,
    });
    const data = await res.json();
    if (!data.success) throw new Error(data.error?.message);
    editingImages = data.product.images || [];
    input.value = '';
    renderImageGallery();
}

async function setPrimaryImage(imageId) {
    const productId = document.getElementById('productId').value;
    const res = await apiFetch(`/products/${productId}/images/${imageId}/primary`, { method: 'PATCH' });
    const data = await res.json();
    if (!data.success) throw new Error(data.error?.message);
    editingImages = data.product.images || [];
    renderImageGallery();
}

async function deleteImage(imageId) {
    if (!confirm('Delete this image?')) return;
    const productId = document.getElementById('productId').value;
    const res = await apiFetch(`/products/${productId}/images/${imageId}`, { method: 'DELETE' });
    const data = await res.json();
    if (!data.success) throw new Error(data.error?.message);
    editingImages = data.product.images || [];
    renderImageGallery();
}

async function saveProduct(event) {
    event.preventDefault();
    const productId = document.getElementById('productId').value;
    const category = getCategoryValue();
    if (!category) {
        alert('Select or enter a category.');
        return;
    }

    const payload = {
        name: document.getElementById('productName').value,
        description: document.getElementById('productDescription').value,
        cost_price: parseFloat(document.getElementById('costPrice').value),
        selling_price: parseFloat(document.getElementById('sellingPrice').value),
        stock: parseInt(document.getElementById('stock').value, 10),
        category,
        image_url: document.getElementById('imageUrl').value || null,
    };

    try {
        const res = productId
            ? await apiFetch(`/products/${productId}`, { method: 'PATCH', body: JSON.stringify(payload) })
            : await apiFetch('/products', { method: 'POST', body: JSON.stringify(payload) });

        const data = await res.json();
        if (!data.success) throw new Error(data.error?.message);

        const savedId = productId || data.product.id;
        await uploadProductImages(savedId);

        alert(productId ? 'Product updated' : 'Product created');
        closeProductModal();
        loadProducts(currentProductPage);
    } catch (err) {
        alert('Error: ' + err.message);
    }
}

async function deleteProduct(productId) {
    if (!confirm('Delete this product? This cannot be undone.')) return;
    try {
        const res = await apiFetch(`/products/${productId}`, { method: 'DELETE' });
        const data = await res.json();
        if (!data.success) throw new Error(data.error?.message);
        alert('Product deleted');
        loadProducts(currentProductPage);
    } catch (err) {
        alert('Error: ' + err.message);
    }
}

function closeProductModal() {
    document.getElementById('productModal').style.display = 'none';
}

document.addEventListener('DOMContentLoaded', () => {
    loadProducts(1);
    window.onclick = e => {
        if (e.target === document.getElementById('productModal')) closeProductModal();
    };
});
