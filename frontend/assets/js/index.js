// Landing page — load real social proof and owner message
async function loadLandingData() {
    try {
        const [landingRes, salesRes, reviewsRes] = await Promise.all([
            fetch(`${API_BASE_URL}/api/settings/landing`),
            fetch(`${API_BASE_URL}/api/products/recent-sales`),
            fetch(`${API_BASE_URL}/api/products/reviews/recent`),
        ]);
        const landing = (await landingRes.json()).landing || {};
        const sales = (await salesRes.json()).items || [];
        const reviews = (await reviewsRes.json()).reviews || [];

        const ownerMsg = document.getElementById('ownerMessageText');
        if (ownerMsg) ownerMsg.textContent = landing.owner_message || landing.owner_bio || '';

        const ownerImg = document.getElementById('ownerMessageImg');
        if (ownerImg && landing.owner_image_url) {
            ownerImg.src = landing.owner_image_url;
            ownerImg.style.display = 'block';
        }
        const ownerName = document.getElementById('ownerMessageName');
        if (ownerName) ownerName.textContent = landing.owner_name || 'EthioShop Team';

        const refText = document.getElementById('landingReferralText');
        if (refText) {
            refText.innerHTML = `Earn <strong>${landing.referral_reward_etb || 50} ETB</strong> store credit when a friend you referred completes their <strong>first confirmed order</strong> (not signup only). Annual cap: <strong>${landing.max_referral_per_year || 2000} ETB</strong>.`;
        }

        const reqText = document.getElementById('landingRequestText');
        if (reqText) {
            reqText.innerHTML = `Don't see what you need? <a href="request.html">Request a product</a>. If we add it to our catalog, you get <strong>${landing.request_reward_etb || 20} ETB</strong> store credit.`;
        }

        const salesEl = document.getElementById('recentSalesList');
        if (salesEl) {
            salesEl.innerHTML = sales.length
                ? sales.slice(0, 6).map(s => `<div class="sale-item">Someone in <strong>${s.city}</strong> bought <strong>${s.product_name}</strong></div>`).join('')
                : '<p style="color:#888;">Recent sales will appear here as orders are confirmed.</p>';
        }

        const reviewsEl = document.getElementById('recentReviewsList');
        if (reviewsEl) {
            reviewsEl.innerHTML = reviews.length
                ? reviews.map(r => `<div class="review-item">${'⭐'.repeat(r.rating)} <strong>${r.product_name}</strong> — ${r.comment || 'Great product!'}</div>`).join('')
                : '<p style="color:#888;">Customer reviews appear after delivered orders.</p>';
        }

        const lowStockEl = document.getElementById('lowStockHint');
        if (lowStockEl && sales.length) {
            lowStockEl.textContent = 'We show real stock levels on every product — watch for “Only X left!” badges when stock is low.';
        }
    } catch (e) {
        console.warn('Landing data load failed', e);
    }
}

document.addEventListener('DOMContentLoaded', loadLandingData);
