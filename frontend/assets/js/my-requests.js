async function loadMyRequests() {
    const phone = sessionStorage.getItem('userPhone');
    const list = document.getElementById('requestsList');
    const login = document.getElementById('loginPrompt');

    if (!phone) {
        login.style.display = 'block';
        list.innerHTML = '';
        return;
    }

    try {
        const data = await UserAPI.getRequests(phone);
        const requests = data.requests || [];

        if (!requests.length) {
            list.innerHTML = '<p>No requests yet. <a href="request.html">Submit a product request</a></p>';
            return;
        }

        list.innerHTML = requests.map(r => `
            <div class="request-card">
                <div>
                    ${r.image_url
                        ? `<a href="${r.image_url}" target="_blank"><img src="${r.image_url}" alt=""></a>`
                        : '<div style="width:80px;height:80px;background:#eee;border-radius:6px;"></div>'}
                </div>
                <div>
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                        <strong>Request #${r.id}</strong>
                        <span class="status-pill status-${r.status}">${r.status.replace(/_/g, ' ')}</span>
                    </div>
                    <p style="margin:0.5rem 0;">${r.description || ''}</p>
                    <small style="color:#888;">Submitted ${new Date(r.created_at).toLocaleString()}</small>
                    ${r.budget != null ? `<p>Budget: <strong>${r.budget.toFixed(2)} ETB</strong></p>` : ''}
                    ${r.quoted_price != null ? `<p>Quoted price: <strong style="color:#27ae60;">${r.quoted_price.toFixed(2)} ETB</strong></p>` : ''}
                    ${r.admin_response_message ? `<div class="admin-msg">💬 ${r.admin_response_message}</div>` : ''}
                    ${r.status === 'price_quoted' ? `
                        <button class="btn btn-primary" style="margin-top:0.75rem;" onclick="acceptQuote(${r.id})">
                            Accept &amp; Convert to Order
                        </button>
                    ` : ''}
                    ${r.status === 'converted' && r.converted_order_id ? `
                        <p style="margin-top:0.5rem;"><a href="order-success.html?id=${r.converted_order_id}">View order #${r.converted_order_id}</a></p>
                    ` : ''}
                </div>
            </div>
        `).join('');
    } catch (err) {
        list.innerHTML = `<p style="color:red;">${err.message}</p>`;
    }
}

async function acceptQuote(requestId) {
    const phone = sessionStorage.getItem('userPhone');
    if (!confirm('Convert this quoted request into an order? You will complete payment next.')) return;

    try {
        const data = await RequestAPI.convert(requestId, { phone, payment_method: 'Bank Transfer' });
        const orderId = data.order?.id;
        if (!orderId) throw new Error('Order was not created');
        alert(`Order #${orderId} created! Complete payment on the next page.`);
        window.location.href = `order-success.html?id=${orderId}`;
    } catch (err) {
        alert('Error: ' + err.message);
    }
}

document.addEventListener('DOMContentLoaded', loadMyRequests);
