let currentPage = 1;

async function loadRefunds(page = 1) {
    currentPage = page;
    const container = document.getElementById('refundsContainer');
    const status = document.getElementById('statusFilter').value;
    container.innerHTML = '<p>Loading...</p>';

    try {
        let url = `/refunds?page=${page}&limit=20`;
        if (status) url += `&status=${status}`;
        const res = await apiFetch(url);
        const data = await res.json();
        if (!data.success) throw new Error(data.error?.message);

        const items = data.items || [];
        if (!items.length) {
            container.innerHTML = '<p>No refunds found.</p>';
            return;
        }

        container.innerHTML = items.map(r => `
            <div class="order-card" style="margin-bottom:1rem;padding:1rem;background:#fff;border-radius:8px;">
                <strong>Refund #${r.id}</strong> — Order #${r.order_id}
                <span class="status-badge status-${r.status === 'pending_review' ? 'pending' : r.status}">${r.status}</span>
                <p style="margin:0.5rem 0;">Reason: ${r.reason}</p>
                <p>Order total: ${r.order_total != null ? r.order_total.toFixed(2) : '-'} ETB</p>
                ${r.additional_evidence_url ? `<p><a href="${r.additional_evidence_url}" target="_blank">View customer evidence</a></p>` : ''}
                ${r.status === 'pending_review' ? `
                    <textarea id="note-${r.id}" placeholder="Note to customer (visible on rejection/approval)" rows="2" style="width:100%;margin:0.5rem 0;"></textarea>
                    <div style="display:flex;gap:0.5rem;flex-wrap:wrap;">
                        <button class="btn-small" onclick="processRefund(${r.id}, true)">Approve</button>
                        <button class="btn-small btn-danger" onclick="processRefund(${r.id}, false)">Reject</button>
                        <button class="btn-small" onclick="requestEvidence(${r.id})">Request More Evidence</button>
                        <button class="btn-small" onclick="sendMessage(${r.id})">Send Message</button>
                    </div>
                ` : `<p><small>Admin: ${r.admin_notes || r.customer_visible_note || '-'}</small></p>`}
            </div>
        `).join('');
    } catch (err) {
        container.innerHTML = `<p style="color:red;">${err.message}</p>`;
    }
}

async function processRefund(id, approved) {
    const note = document.getElementById(`note-${id}`)?.value || '';
    if (!approved && !note && !confirm('Reject without a note to customer?')) return;
    try {
        const res = await apiFetch(`/refunds/${id}/process`, {
            method: 'PATCH',
            body: JSON.stringify({ approved, admin_notes: note, customer_visible_note: note }),
        });
        const data = await res.json();
        if (!data.success) throw new Error(data.error?.message);
        alert(approved ? 'Refund approved' : 'Refund rejected');
        loadRefunds(currentPage);
    } catch (err) { alert(err.message); }
}

async function requestEvidence(id) {
    const note = prompt('Message to customer about what evidence to upload:');
    if (!note) return;
    try {
        const res = await apiFetch(`/refunds/${id}/request-evidence`, {
            method: 'PATCH',
            body: JSON.stringify({ note }),
        });
        const data = await res.json();
        if (!data.success) throw new Error(data.error?.message);
        alert('Evidence requested — customer notified');
        loadRefunds(currentPage);
    } catch (err) { alert(err.message); }
}

async function sendMessage(id) {
    const message = prompt('Message to customer:');
    if (!message) return;
    try {
        const res = await apiFetch(`/refunds/${id}/messages`, {
            method: 'POST',
            body: JSON.stringify({ message }),
        });
        const data = await res.json();
        if (!data.success) throw new Error(data.error?.message);
        alert('Message sent');
    } catch (err) { alert(err.message); }
}

document.addEventListener('DOMContentLoaded', () => loadRefunds(1));
