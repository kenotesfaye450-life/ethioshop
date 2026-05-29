let currentUser = null;
let ordersSnapshot = {};
let requestsSnapshot = {};
let refundsSnapshot = {};
let pollTimer = null;
let activeDashboardTab = 'overview';
let seenAnsweredQuestionIds = new Set(
    JSON.parse(sessionStorage.getItem('seenAnsweredQuestions') || '[]').map(String)
);

function getReferralLink(code) {
    return `${window.location.origin}/?ref=${encodeURIComponent(code)}`;
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
        const hashTab = (location.hash || '').replace(/^#/, '');
        if (['overview', 'orders', 'requests', 'questions', 'settings'].includes(hashTab)) {
            switchDashboardTab(hashTab);
        } else {
            switchDashboardTab('overview');
        }
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
        const response = await UserAPI.getOrders(phone, 1, 20);
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
        if (response.total > orders.length) {
            const note = document.createElement('p');
            note.id = 'ordersPaginationNote';
            note.style.cssText = 'color:#666;font-size:0.9rem;margin-top:0.5rem;';
            note.textContent = `Showing ${orders.length} of ${response.total} orders (most recent).`;
            container.appendChild(note);
        }
    } catch (error) {
        container.innerHTML = `<p>Error loading orders: ${error.message}</p>`;
    }
}

async function pollForUpdates() {
    const phone = sessionStorage.getItem('userPhone');
    if (!phone) return;

    if (activeDashboardTab === 'overview') {
        try {
            const userRes = await UserAPI.getByPhone(phone);
            if (userRes.user.total_referrals !== currentUser.total_referrals) {
                currentUser = userRes.user;
                document.getElementById('totalReferrals').textContent = currentUser.total_referrals;
                const referralEarnings = Number(currentUser.referral_earnings ?? (currentUser.total_referrals * 50));
                document.getElementById('referralEarned').textContent = `${referralEarnings.toFixed(2)} ETB`;
            }
        } catch (e) { /* ignore */ }
    }

    if (activeDashboardTab === 'orders') {
        await loadOrders(false);
    }

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

function switchDashboardTab(tab) {
    activeDashboardTab = tab;
    if (location.hash !== `#${tab}`) {
        history.replaceState(null, '', `#${tab}`);
    }
    document.querySelectorAll('#dashboardNav .dash-tab, #dashboardBottomNav .dash-tab').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tab);
    });
    document.querySelectorAll('.dash-panel').forEach(panel => {
        panel.classList.toggle('active', panel.id === `panel-${tab}`);
    });
    if (tab === 'requests') loadRequestsPanel();
    if (tab === 'questions') loadQuestionsPanel();
    if (tab === 'orders') loadOrders(true);
}

function initDashboardTabs() {
    document.querySelectorAll('.dash-tab').forEach(btn => {
        btn.addEventListener('click', () => switchDashboardTab(btn.dataset.tab));
    });
    const bottom = document.getElementById('dashboardBottomNav');
    if (bottom && window.matchMedia('(max-width: 768px)').matches) {
        bottom.innerHTML = document.getElementById('dashboardNav').innerHTML;
        bottom.querySelectorAll('.dash-tab').forEach(btn => {
            btn.addEventListener('click', () => switchDashboardTab(btn.dataset.tab));
        });
    }
}

async function loadRequestsPanel() {
    const phone = sessionStorage.getItem('userPhone');
    const el = document.getElementById('requestsContainer');
    if (!el || !phone) return;
    try {
        const data = await UserAPI.getRequests(phone);
        const requests = data.requests || [];
        el.innerHTML = requests.length
            ? requests.map(r => `<div class="order-card"><strong>#${r.id}</strong> — ${r.status} — ${r.description || ''}</div>`).join('')
            : '<p>No requests yet.</p>';
    } catch (e) {
        el.innerHTML = `<p style="color:red;">${e.message}</p>`;
    }
}

async function loadQuestionsPanel() {
    const phone = sessionStorage.getItem('userPhone');
    const el = document.getElementById('questionsContainer');
    if (!el || !phone) return;
    try {
        const data = await UserAPI.getQuestions(phone);
        const items = data.questions || [];
        if (!items.length) {
            el.innerHTML = '<p>No questions yet. Open a product and ask about stock.</p>';
            return;
        }
        el.innerHTML = items.map(q => `
            <div class="order-card">
                <strong>${q.product_name || 'Product'}</strong>
                <span class="status-badge status-${q.status === 'answered' ? 'confirmed' : 'pending'}">${q.status}</span>
                <p><strong>Q:</strong> ${q.question}</p>
                ${q.answer ? `<p style="color:#27ae60;"><strong>A:</strong> ${q.answer}</p>` : '<p><em>Waiting for shop reply…</em></p>'}
            </div>
        `).join('');
        items.filter(q => q.status === 'answered').forEach(q => {
            const key = String(q.id);
            if (!seenAnsweredQuestionIds.has(key)) {
                seenAnsweredQuestionIds.add(key);
                NotificationCenter.notify('Product question answered', `${q.product_name}: ${q.answer}`, 'success');
            }
        });
        sessionStorage.setItem('seenAnsweredQuestions', JSON.stringify([...seenAnsweredQuestionIds]));
    } catch (e) {
        el.innerHTML = `<p style="color:red;">${e.message}</p>`;
    }
}

function saveSettingsName() {
    const name = document.getElementById('settingsName')?.value?.trim();
    if (name) sessionStorage.setItem('userName', name);
    if (currentUser) currentUser.name = name;
    alert('Name saved locally. Full profile update coming soon.');
}

function logoutUser() {
    sessionStorage.removeItem('userPhone');
    sessionStorage.removeItem('userName');
    if (pollTimer) clearInterval(pollTimer);
    window.location.href = 'index.html';
}

window.addEventListener('hashchange', () => {
    const tab = (location.hash || '').replace(/^#/, '');
    if (['overview', 'orders', 'requests', 'questions', 'settings'].includes(tab)) {
        switchDashboardTab(tab);
    }
});

document.addEventListener('DOMContentLoaded', () => {
    initDashboardTabs();
    initDashboard().then(() => {
        const sn = document.getElementById('settingsName');
        if (sn) sn.value = sessionStorage.getItem('userName') || '';
    });
    NotificationCenter.updateBell();
});

window.addEventListener('beforeunload', () => {
    if (pollTimer) clearInterval(pollTimer);
});
