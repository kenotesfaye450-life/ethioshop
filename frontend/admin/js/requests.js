let currentPage = 1;
let requestMap = {};

async function loadRequests(page = 1) {
    currentPage = page;
    const container = document.getElementById('requestsContainer');
    const status = document.getElementById('statusFilter').value;
    container.innerHTML = '<p>Loading...</p>';

    try {
        let url = `/requests?page=${page}&limit=20`;
        if (status) url += `&status=${encodeURIComponent(status)}`;

        const res = await apiFetch(url);
        const data = await res.json();
        if (!data.success) throw new Error(data.error?.message);

        const items = data.items || data.requests || [];
        requestMap = {};
        items.forEach(r => { requestMap[r.id] = r; });
        if (!items.length) {
            container.innerHTML = '<p>No requests found.</p>';
            return;
        }

        container.innerHTML = `
            <table class="products-table">
                <thead><tr>
                    <th>ID</th><th>Phone</th><th>Description</th><th>Image</th>
                    <th>Budget</th><th>Status</th><th>Quoted</th><th>Created</th><th>Actions</th>
                </tr></thead>
                <tbody>
                    ${items.map(r => `
                        <tr>
                            <td>#${r.id}</td>
                            <td>${r.user_phone}</td>
                            <td style="max-width:200px;">${r.description}</td>
                            <td>${r.image_url ? `<a href="${r.image_url}" target="_blank"><img src="${r.image_url}" style="width:48px;height:48px;object-fit:cover;border-radius:4px;"></a>` : '-'}</td>
                            <td>${r.budget != null ? r.budget.toFixed(2) + ' ETB' : '-'}</td>
                            <td><span class="status-badge status-${r.status}">${r.status}</span></td>
                            <td>${r.quoted_price != null ? r.quoted_price.toFixed(2) + ' ETB' : '-'}</td>
                            <td>${new Date(r.created_at).toLocaleDateString()}</td>
                            <td>
                                ${r.status === 'pending_sourcing' || r.status === 'price_quoted' ? `
                                    <button class="btn-small" onclick="quoteRequest(${r.id})">Quote</button>
                                    <button class="btn-small btn-danger" onclick="rejectRequest(${r.id})">Reject</button>
                                    <button class="btn-small" onclick="convertToProduct(${r.id})">Convert to Product</button>
                                ` : '-'}
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
            ${data.pages > 1 ? `
                <div style="margin-top:1rem;display:flex;gap:0.5rem;align-items:center;">
                    ${page > 1 ? `<button class="btn-small" onclick="loadRequests(${page - 1})">← Prev</button>` : ''}
                    <span>Page ${data.page} of ${data.pages}</span>
                    ${page < data.pages ? `<button class="btn-small" onclick="loadRequests(${page + 1})">Next →</button>` : ''}
                </div>
            ` : ''}
        `;
    } catch (err) {
        container.innerHTML = `<p style="color:red;">Error: ${err.message}</p>`;
    }
}

async function quoteRequest(id) {
    const price = prompt('Enter quoted price (ETB):');
    if (!price) return;
    const admin_message = prompt('Message to customer (optional):') || '';
    try {
        const res = await apiFetch(`/requests/${id}/quote`, {
            method: 'PATCH',
            body: JSON.stringify({ quoted_price: parseFloat(price), admin_message }),
        });
        const data = await res.json();
        if (!data.success) throw new Error(data.error?.message);
        alert('Price quoted successfully');
        loadRequests(currentPage);
    } catch (err) {
        alert('Error: ' + err.message);
    }
}

async function rejectRequest(id) {
    if (!confirm('Reject this request?')) return;
    const admin_message = prompt('Message to customer (optional):') || '';
    try {
        const res = await apiFetch(`/requests/${id}/reject`, {
            method: 'PATCH',
            body: JSON.stringify({ admin_message }),
        });
        const data = await res.json();
        if (!data.success) throw new Error(data.error?.message);
        alert('Request rejected');
        loadRequests(currentPage);
    } catch (err) {
        alert('Error: ' + err.message);
    }
}

document.addEventListener('DOMContentLoaded', () => loadRequests(1));

async function convertToProduct(id) {
    const req = requestMap[id] || {};
    const nameDefault = (req.description || 'Requested Product').slice(0, 100);
    const name = prompt('Product name:', nameDefault);
    if (!name) return;
    const category = prompt('Category (or new category name):', 'General') || 'General';
    const selling_price = Number(prompt('Selling price (ETB):', '0') || 0);
    const cost_price = Number(prompt('Cost price (ETB):', '0') || 0);
    const stock = Number(prompt('Stock:', '1') || 1);
    try {
        const res = await apiFetch(`/requests/${id}/convert-to-product`, {
            method: 'POST',
            body: JSON.stringify({
                name,
                description: req.description || '',
                category,
                selling_price,
                cost_price,
                stock,
                mark_converted: true,
            }),
        });
        const data = await res.json();
        if (!data.success) throw new Error(data.error?.message);
        alert(`Converted to product #${data.product.id}`);
        loadRequests(currentPage);
    } catch (err) {
        alert('Error: ' + err.message);
    }
}
