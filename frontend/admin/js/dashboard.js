// Dashboard analytics logic

async function loadStats() {
    try {
        const res  = await apiFetch('/admin/stats');
        const data = await res.json();
        if (!data.success) throw new Error(data.error?.message);

        const s = data.stats;

        document.getElementById('totalSales').textContent    = s.total_sales_etb.toFixed(2);
        document.getElementById('pendingOrders').textContent  = s.pending_orders;
        document.getElementById('totalOrders').textContent    = s.total_orders;
        document.getElementById('dailyOrders').textContent    = s.daily_orders;
        document.getElementById('refundCount').textContent    = s.refunds.count;
        document.getElementById('refundTotal').textContent    = `${s.refunds.total_refunded_etb.toFixed(2)} ETB`;
        document.getElementById('referralCount').textContent  = s.referrals.count;
        document.getElementById('referralCredit').textContent = `${s.referrals.total_credit_etb.toFixed(2)} ETB awarded`;

        // Recent orders table
        const tbody = document.getElementById('recentOrdersBody');
        if (!s.recent_orders.length) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:#999;padding:2rem;">No orders yet</td></tr>';
        } else {
            tbody.innerHTML = s.recent_orders.map(o => `
                <tr>
                    <td><strong>#${o.id}</strong></td>
                    <td>${o.user_phone}</td>
                    <td>${o.final_total.toFixed(2)}</td>
                    <td><span class="status-badge status-${o.status === 'pending_verification' ? 'pending' : o.status}">
                        ${o.status.replace(/_/g,' ')}
                    </span></td>
                    <td>${(o.delivery_status||'pending').replace(/_/g,' ')}</td>
                    <td>${new Date(o.created_at).toLocaleDateString()}</td>
                </tr>
            `).join('');
        }

        // Top products table
        const topBody = document.getElementById('topProductsBody');
        if (!s.top_products || !s.top_products.length) {
            topBody.innerHTML = '<tr><td colspan="3" style="text-align:center;color:#999;padding:1rem;">No sales data yet</td></tr>';
        } else {
            topBody.innerHTML = s.top_products.map((p, i) => `
                <tr>
                    <td>${i + 1}</td>
                    <td>${p.name}</td>
                    <td>${p.total_sold} units</td>
                </tr>
            `).join('');
        }

    } catch (err) {
        document.getElementById('recentOrdersBody').innerHTML =
            `<tr><td colspan="6" style="color:red;padding:1rem;">Error: ${err.message}</td></tr>`;
    }
}

async function loadReferralStats() {
    const topBody = document.getElementById('topReferrersBody');
    if (!topBody) return;
    try {
        const res = await apiFetch('/admin/referral-stats');
        const data = await res.json();
        if (!data.success) throw new Error(data.error?.message);
        const top = data.stats.top_referrers || [];
        if (!top.length) {
            topBody.innerHTML = '<tr><td colspan="3" style="text-align:center;color:#999;padding:1rem;">No referrals yet</td></tr>';
            return;
        }
        topBody.innerHTML = top.map((r, i) => `
            <tr>
                <td>${i + 1}</td>
                <td>${r.name || r.phone}</td>
                <td>${r.count}</td>
            </tr>
        `).join('');
    } catch (err) {
        topBody.innerHTML = `<tr><td colspan="3" style="color:red;padding:0.5rem;">${err.message}</td></tr>`;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    loadReferralStats();
});
