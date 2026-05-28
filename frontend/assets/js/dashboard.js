let currentUser = null;
let ordersSnapshot = {};
let requestsSnapshot = {};
let refundsSnapshot = {};
let pollTimer = null;

function getReferralLink(code) {
    const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    return isLocal
        ? `${window.location.origin}/index.html?ref=${encodeURIComponent(code)}`
        : `https://ethioshop.et/?ref=${encodeURIComponent(code)}`;
}

async function initDashboard() {
    const phone = sessionStorage.getItem('userPhone');
    if (!phone) {
        document.getElementById('loginPrompt').style.display = 'block';
        return;
    }

    try {
        const response = await UserAPI.getByPhone(phone);
        currentUser = response.user;
        displayDashboard();
        await loadOrders(true);
        await pollForUpdates();
        NotificationCenter.requestPermissionOnce();
        pollTimer = setInterval(pollForUpdates, 10000);
    } catch (error) {
        document.getElementById('loginPrompt').style.display = 'block';
    }
}

function displayDashboard() {
    document.getElementById('dashboardContent').style.display = 'block';
    const displayName = currentUser.name || sessionStorage.getItem('userName') || 'Customer';
    document.getElementById('welcomeUser').textContent = `Welcome, ${displayName}! (${currentUser.phone})`;
    if (currentUser.name) sessionStorage.setItem('userName', currentUser.name);

    document.getElementById('creditBalance').textContent = `${currentUser.credit_balance.toFixed(2)} ETB`;
    document.getElementById('totalReferrals').textContent = currentUser.total_referrals;
    const referralEarnings = Number(currentUser.referral_earnings ?? (currentUser.total_referrals * 50));
    const reward = Number(currentUser.referral_reward_etb ?? 50);
    const cap = Number(currentUser.referral_cap_per_year ?? 2000);
    const earnedYear = Number(currentUser.referral_earned_this_year ?? 0);
    const remaining = Number(currentUser.referral_remaining_cap ?? Math.max(cap - earnedYear, 0));
    document.getElementById('referralEarned').textContent = `${referralEarnings.toFixed(2)} ETB`;
    document.getElementById('referralCode').textContent = currentUser.referral_code;
    const capNote = document.getElementById('referralCapNote');
    if (capNote) {
        capNote.textContent = `${reward} ETB per confirmed referral · ${remaining.toFixed(0)} ETB cap left this year (max ${cap} ETB/year)`;
    }
    const rules = document.getElementById('referralRulesText');
    if (rules) {
        rules.innerHTML = `You earn <strong>${reward} ETB</strong> store credit after your friend's <strong>first order is confirmed</strong> (not just signup). Credit can be used on your next purchase. Annual cap: <strong>${cap} ETB</strong> referral credit per year (${remaining.toFixed(0)} ETB remaining).`;
    }

    const refLink = getReferralLink(currentUser.referral_code);
    document.getElementById('referralLinkHidden').value = refLink;

    const shareText = encodeURIComponent(`Join EthioShop — use my link and earn rewards! ${refLink}`);
    document.getElementById('shareWhatsApp').href = `https://wa.me/?text=${shareText}`;
    document.getElementById('shareTelegram').href = `https://t.me/share/url?url=${encodeURIComponent(refLink)}&text=${shareText}`;
    document.getElementById('shareMessenger').href = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(refLink)}`;
}

function openReferralShare() {
    const link = document.getElementById('referralLinkHidden').value;
    const menu = document.getElementById('referralShareMenu');
    menu.style.display = menu.style.display === 'flex' ? 'none' : 'flex';
    if (navigator.share) {
        navigator.share({
            title: 'EthioShop — Share & Earn 50 Birr',
            text: 'Join EthioShop with my referral link!',
            url: link,
        }).catch(() => {});
    }
}

function copyReferralLink() {
    const link = document.getElementById('referralLinkHidden').value;
    navigator.clipboard.writeText(link).then(() => {
        showToast('Referral link copied!', 'success');
    });
}

function orderKey(o) {
    return `${o.status}|${o.delivery_status}`;
}

function renderOrders(orders) {
    const container = document.getElementById('ordersContainer');
    if (!orders.length) {
        container.innerHTML = '<p>No orders yet. <a href="shop.html">Start shopping!</a></p>';
        return;
    }

    container.innerHTML = orders.map(order => `
        <div class="order-card" data-order-id="${order.id}">
            <div class="order-header">
                <div>
                    <strong>Order #${order.id}</strong><br>
                    <small>${new Date(order.created_at).toLocaleString()}</small>
                </div>
                <span class="order-status status-${order.status}">${order.status.replace(/_/g, ' ')}</span>
            </div>
            <p><strong>Delivery:</strong> ${(order.delivery_status || 'pending').replace(/_/g, ' ')}</p>
            ${order.customer_note ? `<p class="admin-note">📌 ${order.customer_note}</p>` : ''}
            ${order.evidence_requested ? `
                <p style="color:#c0392b;font-weight:bold;">⚠️ Additional payment proof requested</p>
                <a href="upload-evidence.html?order_id=${order.id}" class="btn btn-primary btn-sm">Upload Proof</a>
            ` : ''}
            ${order.payment_status && order.payment_status !== 'paid' ? `
                <p style="color:#8e44ad;font-weight:bold;">Payment: ${order.payment_status} (Remaining: ${(order.remaining_amount || 0).toFixed(2)} ETB)</p>
                <a class="btn btn-primary btn-sm" href="upload-evidence.html?order_id=${order.id}&remaining=1">Pay Remaining</a>
            ` : ''}
            ${order.delivery_status === 'in_transit' ? `
                <button class="btn btn-secondary btn-sm" onclick="confirmDelivery(${order.id})">Confirm Delivery</button>
            ` : ''}
            ${order.status === 'delivered' ? `
                <button class="btn btn-secondary btn-sm" onclick="rateOrder(${order.id})">Rate Products</button>
            ` : ''}
            <div style="display:flex;justify-content:space-between;align-items:center;margin-top:0.75rem;">
                <p class="order-total">Total: ${order.final_total.toFixed(2)} ETB</p>
                ${(order.status === 'confirmed' || order.status === 'delivered') ? `
                    <button onclick="requestRefund(${order.id})" class="btn btn-secondary btn-sm">Request Refund</button>
                ` : order.status === 'pending_verification' ? `
                    <a href="order-success.html?id=${order.id}" class="btn btn-secondary btn-sm">Upload Payment</a>
                ` : ''}
            </div>
        </div>
    `).join('');
}

async function confirmDelivery(orderId) {
    try {
        await OrderAPI.confirmDelivery(orderId, { phone: sessionStorage.getItem('userPhone') });
        showToast('Delivery confirmed. Thank you!', 'success');
        await loadOrders(true);
    } catch (error) {
        alert(error.message);
    }
}

async function rateOrder(orderId) {
    try {
        const orderRes = await OrderAPI.getById(orderId);
        const items = orderRes.order?.items || [];
        if (!items.length) return;
        const reviews = [];
        for (const item of items) {
            const rating = Number(prompt(`Rate ${item.product_name} (1-5):`, '5'));
            if (!rating || rating < 1 || rating > 5) continue;
            const comment = prompt(`Comment for ${item.product_name} (optional):`) || '';
            reviews.push({ product_id: item.product_id, rating, comment });
        }
        if (!reviews.length) return;
        await OrderAPI.submitReviews(orderId, { phone: sessionStorage.getItem('userPhone'), reviews });
        showToast('Thanks for your review!', 'success');
    } catch (error) {
        alert(error.message);
    }
}

async function loadOrders(isInitial = false) {
    const phone = sessionStorage.getItem('userPhone');
    const container = document.getElementById('ordersContainer');
    try {
        const response = await UserAPI.getOrders(phone);
        const orders = response.orders || [];
        if (!isInitial) {
            orders.forEach(o => {
                const prev = ordersSnapshot[o.id];
                const key = orderKey(o);
                if (prev && prev !== key) {
                    const msg = `Order #${o.id}: ${o.status.replace(/_/g, ' ')} — delivery ${(o.delivery_status || '').replace(/_/g, ' ')}`;
                    NotificationCenter.notify('Order update', msg, 'order');
                }
            });
        }
        const next = {};
        orders.forEach(o => { next[o.id] = orderKey(o); });
        ordersSnapshot = next;
        renderOrders(orders);
    } catch (error) {
        container.innerHTML = `<p>Error loading orders: ${error.message}</p>`;
    }
}

async function pollForUpdates() {
    const phone = sessionStorage.getItem('userPhone');
    if (!phone) return;

    try {
        const userRes = await UserAPI.getByPhone(phone);
        if (userRes.user.total_referrals !== currentUser.total_referrals) {
            currentUser = userRes.user;
            document.getElementById('totalReferrals').textContent = currentUser.total_referrals;
            const referralEarnings = Number(currentUser.referral_earnings ?? (currentUser.total_referrals * 50));
            document.getElementById('referralEarned').textContent = `${referralEarnings.toFixed(2)} ETB`;
        }
    } catch (e) { /* ignore */ }

    await loadOrders(false);

    try {
        const reqRes = await UserAPI.getRequests(phone);
        (reqRes.requests || []).forEach(r => {
            const prev = requestsSnapshot[r.id];
            if (prev && prev !== r.status) {
                if (r.status === 'price_quoted') {
                    NotificationCenter.notify('Request quoted', `Request #${r.id} — ${r.quoted_price} ETB. View My Requests to accept.`, 'request');
                } else if (r.status === 'rejected') {
                    NotificationCenter.notify('Request update', `Request #${r.id} was declined.`, 'request');
                }
            }
            requestsSnapshot[r.id] = r.status;
        });
    } catch (e) { /* ignore */ }

    try {
        const refRes = await UserAPI.getRefunds(phone);
        (refRes.refunds || []).forEach(r => {
            const prev = refundsSnapshot[r.id];
            if (prev && prev !== r.status) {
                NotificationCenter.notify('Refund update', `Refund for order #${r.order_id}: ${r.status}`, 'refund');
            }
            if (r.evidence_requested && !refundsSnapshot[`ev_${r.id}`]) {
                NotificationCenter.notify('Evidence needed', `Please upload documents for refund #${r.id}`, 'refund');
                refundsSnapshot[`ev_${r.id}`] = true;
            }
            refundsSnapshot[r.id] = r.status;
        });
    } catch (e) { /* ignore */ }
}

async function requestRefund(orderId) {
    const reason = prompt('Please enter reason for refund:');
    if (!reason) return;
    try {
        const res = await fetch(`${API_BASE_URL}/api/refunds`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                order_id: orderId,
                reason,
                phone: sessionStorage.getItem('userPhone'),
            }),
        });
        const data = await res.json();
        if (data.success) {
            showToast('Refund request submitted', 'success');
            await loadOrders(true);
        } else {
            alert('Error: ' + data.error.message);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initDashboard();
    NotificationCenter.updateBell();
});

window.addEventListener('beforeunload', () => {
    if (pollTimer) clearInterval(pollTimer);
});
