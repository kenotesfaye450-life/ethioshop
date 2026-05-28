// Orders management logic

let currentOrderPage = 1;

async function loadOrders(page = 1) {
    currentOrderPage = page;
    const container = document.getElementById('ordersContainer');
    const status    = document.getElementById('statusFilter')?.value || '';
    container.innerHTML = '<p style="color:#999;padding:1rem;">Loading...</p>';

    try {
        const res  = await apiFetch(`/admin/orders?page=${page}&limit=20${status ? '&status=' + status : ''}`);
        const data = await res.json();
        if (!data.success) throw new Error(data.error?.message);

        const orders = data.items || data.orders || [];
        if (!orders.length) { container.innerHTML = '<p style="color:#999;padding:1rem;">No orders found.</p>'; return; }

        container.innerHTML = `
            <table class="orders-table">
                <thead><tr>
                    <th>ID</th><th>Customer</th><th>Total</th><th>Paid/Remaining</th>
                    <th>Status</th><th>Delivery</th><th>Date</th><th>Actions</th>
                </tr></thead>
                <tbody>
                    ${orders.map(o => `
                        <tr>
                            <td>#${o.id}</td>
                            <td>${o.user_phone}</td>
                            <td>${o.final_total.toFixed(2)} ETB</td>
                            <td>${(o.amount_paid || 0).toFixed(2)} / ${(o.remaining_amount || 0).toFixed(2)}<br><small>${o.payment_status || 'pending'}</small></td>
                            <td><span class="status-badge status-${o.status}">${o.status.replace(/_/g,' ')}</span></td>
                            <td>${(o.delivery_status||'pending').replace(/_/g,' ')}</td>
                            <td>${new Date(o.created_at).toLocaleDateString()}</td>
                            <td>
                                <button onclick="viewOrder(${o.id})" class="btn-small">View</button>
                                ${o.status === 'pending_verification' ? `
                                    <button onclick="verifyOrder(${o.id},true)"  class="btn-small btn-success">Approve</button>
                                    <button onclick="verifyOrder(${o.id},false)" class="btn-small btn-danger">Reject</button>
                                ` : ''}
                                ${o.status === 'confirmed' && o.delivery_status === 'pending_assignment' ? `
                                    <button onclick="assignDelivery(${o.id})" class="btn-small">Assign</button>
                                ` : ''}
                                ${o.status === 'confirmed' && ['assigned','pending_assignment'].includes(o.delivery_status) ? `
                                    <button onclick="updateDelivery(${o.id},'in_transit')" class="btn-small">In Transit</button>
                                ` : ''}
                                ${o.status === 'confirmed' && o.delivery_status === 'in_transit' ? `
                                    <button onclick="updateDelivery(${o.id},'delivered')" class="btn-small btn-success">Delivered</button>
                                ` : ''}
                                ${o.payment_status !== 'paid' ? `
                                    <button onclick="markRemainingPaid(${o.id})" class="btn-small">Mark Remaining Paid</button>
                                ` : ''}
                                ${o.delivery_status === 'in_transit' ? `
                                    <button onclick="forceConfirmDelivery(${o.id})" class="btn-small btn-success">Force Confirm</button>
                                ` : ''}
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
            ${data.pages > 1 ? `
                <div style="margin-top:1rem;display:flex;gap:0.5rem;align-items:center;">
                    ${page > 1 ? `<button onclick="loadOrders(${page-1})" class="btn-small">← Prev</button>` : ''}
                    <span>Page ${data.page} of ${data.pages} (${data.total} total)</span>
                    ${page < data.pages ? `<button onclick="loadOrders(${page+1})" class="btn-small">Next →</button>` : ''}
                </div>
            ` : ''}
        `;
    } catch (err) {
        container.innerHTML = `<p style="color:red;">Error: ${err.message}</p>`;
    }
}

async function viewOrder(orderId) {
    try {
        const res  = await apiFetch(`/orders/${orderId}`);
        const data = await res.json();
        const o    = data.order;

        document.getElementById('orderDetails').innerHTML = `
            <h2>Order #${o.id}</h2>
            <p><strong>Status:</strong> ${o.status}</p>
            <p><strong>Delivery Status:</strong> ${o.delivery_status || 'pending'}</p>
            <p><strong>Payment:</strong> ${o.payment_method}</p>
            <p><strong>Plan:</strong> ${o.payment_plan || 'full'} | <strong>Payment Status:</strong> ${o.payment_status || 'pending'}</p>
            <p><strong>Amount Paid:</strong> ${(o.amount_paid || 0).toFixed(2)} ETB | <strong>Remaining:</strong> ${(o.remaining_amount || 0).toFixed(2)} ETB</p>
            <p><strong>Location:</strong> ${o.delivery_location ? JSON.stringify(o.delivery_location) : 'N/A'}</p>
            ${o.local_person_name ? `
                <div style="margin-top:1rem;padding:0.85rem;background:#f0f7ff;border-left:4px solid #2c7da0;border-radius:4px;">
                    <strong>🤝 Local delivery contact (far customer)</strong>
                    <p>Name: ${o.local_person_name}</p>
                    <p>Phone: ${o.local_person_phone || '—'}</p>
                    ${o.local_person_notes ? `<p>Notes: ${o.local_person_notes}</p>` : ''}
                </div>
            ` : ''}
            ${o.payment_proof_url ? `<p><strong>Payment Proof:</strong> <a href="${o.payment_proof_url}" target="_blank">View Image ↗</a></p>` : '<p><em>No payment proof uploaded yet</em></p>'}
            <table class="items-table" style="width:100%;margin-top:1rem;">
                <thead><tr><th>Product</th><th>Qty</th><th>Price</th><th>Total</th></tr></thead>
                <tbody>
                    ${(o.items||[]).map(i => `
                        <tr>
                            <td>${i.product_name}</td>
                            <td>${i.quantity}</td>
                            <td>${i.price.toFixed(2)} ETB</td>
                            <td>${(i.price * i.quantity).toFixed(2)} ETB</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
            <div style="margin-top:1rem;text-align:right;">
                <p>Subtotal: ${o.subtotal.toFixed(2)} ETB</p>
                ${o.credit_used > 0 ? `<p>Credit: -${o.credit_used.toFixed(2)} ETB</p>` : ''}
                <p><strong>Total: ${o.final_total.toFixed(2)} ETB</strong></p>
            </div>
            ${o.status === 'pending_verification' ? `
                <div style="margin-top:1rem;border-top:1px solid #eee;padding-top:1rem;">
                    <button onclick="requestOrderEvidence(${o.id})" class="btn-small">Request More Payment Proof</button>
                </div>
            ` : ''}
        `;
        document.getElementById('orderModal').style.display = 'block';
    } catch (err) { alert('Error: ' + err.message); }
}

async function requestOrderEvidence(orderId) {
    const note = prompt('Message to customer about what proof to upload:');
    if (!note) return;
    try {
        const res = await apiFetch(`/orders/${orderId}/request-evidence`, {
            method: 'PATCH', body: JSON.stringify({ note }),
        });
        const data = await res.json();
        if (!data.success) throw new Error(data.error?.message);
        alert('Customer notified to upload additional proof');
    } catch (err) { alert(err.message); }
}

async function verifyOrder(orderId, approved) {
    let customer_note = '';
    if (!approved) {
        customer_note = prompt('Rejection reason (shown to customer):') || '';
        if (!confirm(`Reject order #${orderId}?`)) return;
    } else if (!confirm(`Approve order #${orderId}?`)) return;
    try {
        const res = await apiFetch(`/orders/${orderId}/verify`, {
            method: 'PUT', body: JSON.stringify({ approved, customer_note })
        });
        const data = await res.json();
        if (!data.success) throw new Error(data.error?.message);
        alert(`Order ${approved ? 'approved' : 'rejected'}`);
        loadOrders(currentOrderPage);
    } catch (err) { alert('Error: ' + err.message); }
}

async function assignDelivery(orderId) {
    const name  = prompt('Delivery person name:');  if (!name)  return;
    const phone = prompt('Delivery person phone:'); if (!phone) return;
    try {
        const res = await apiFetch(`/orders/${orderId}/assign-delivery`, {
            method: 'PATCH',
            body: JSON.stringify({ delivery_person_name: name, delivery_person_phone: phone })
        });
        const data = await res.json();
        if (!data.success) throw new Error(data.error?.message);
        alert('Delivery assigned');
        loadOrders(currentOrderPage);
    } catch (err) { alert('Error: ' + err.message); }
}

async function updateDelivery(orderId, status) {
    if (!confirm(`Mark order #${orderId} as "${status.replace('_',' ')}"?`)) return;
    try {
        const res = await apiFetch(`/orders/${orderId}/delivery-status`, {
            method: 'PATCH', body: JSON.stringify({ status })
        });
        const data = await res.json();
        if (!data.success) throw new Error(data.error?.message);
        alert(`Status updated to ${status}`);
        loadOrders(currentOrderPage);
    } catch (err) { alert('Error: ' + err.message); }
}

async function markRemainingPaid(orderId) {
    if (!confirm(`Mark remaining payment as paid for order #${orderId}?`)) return;
    try {
        const res = await apiFetch(`/orders/${orderId}/mark-remaining-paid`, {
            method: 'PATCH',
            body: JSON.stringify({})
        });
        const data = await res.json();
        if (!data.success) throw new Error(data.error?.message);
        alert('Payment marked as fully paid');
        loadOrders(currentOrderPage);
    } catch (err) { alert('Error: ' + err.message); }
}

async function forceConfirmDelivery(orderId) {
    if (!confirm(`Force confirm delivery for #${orderId}?`)) return;
    try {
        const res = await apiFetch(`/orders/${orderId}/force-confirm-delivery`, {
            method: 'PATCH',
            body: JSON.stringify({})
        });
        const data = await res.json();
        if (!data.success) throw new Error(data.error?.message);
        alert('Delivery force confirmed');
        loadOrders(currentOrderPage);
    } catch (err) { alert('Error: ' + err.message); }
}

function closeModal() { document.getElementById('orderModal').style.display = 'none'; }

document.addEventListener('DOMContentLoaded', () => {
    loadOrders(1);
    document.getElementById('statusFilter')?.addEventListener('change', () => loadOrders(1));
    window.onclick = e => { if (e.target === document.getElementById('orderModal')) closeModal(); };
});
