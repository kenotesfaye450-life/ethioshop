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

async function loadFeaturedProducts() {
    const grid = document.getElementById('featuredProducts');
    if (!grid) return;
    try {
        const res = await fetch(`${API_BASE_URL}/api/products?limit=6&page=1`);
        const data = await res.json();
        const items = data.items || [];
        if (!items.length) {
            grid.innerHTML = '<p style="grid-column:1/-1;text-align:center;color:#888;">Products coming soon.</p>';
            return;
        }
        grid.innerHTML = items.map(p => `
            <article class="product-card" style="background:#fff;border-radius:12px;padding:1rem;box-shadow:0 2px 8px rgba(0,0,0,0.08);display:flex;flex-direction:column;">
                <a href="product.html?id=${p.id}" style="text-decoration:none;color:inherit;">
                    <img src="${p.thumbnail_url || p.image_url || ''}" alt="" style="width:100%;height:140px;object-fit:cover;border-radius:8px;background:#eee;">
                    <h4 style="margin:0.75rem 0 0.25rem;font-size:1rem;">${p.name}</h4>
                    <p style="margin:0;font-weight:bold;color:#2c7da0;">${p.price.toFixed(2)} ETB</p>
                </a>
                <button type="button" class="btn btn-primary btn-sm" style="margin-top:0.75rem;" data-featured-add="${p.id}">Add to cart</button>
            </article>
        `).join('');
        grid.querySelectorAll('[data-featured-add]').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.preventDefault();
                const id = Number(btn.getAttribute('data-featured-add'));
                const phone = await requireLoginForAction('add items to your cart');
                if (!phone) return;
                const product = items.find(x => x.id === id);
                if (product && typeof addToCart === 'function') {
                    addToCart(product, 1);
                    if (typeof showToast === 'function') showToast('Added to cart!', 'success');
                }
            });
        });
    } catch (e) {
        grid.innerHTML = '<p style="color:#888;">Could not load products.</p>';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    loadLandingData();
    loadFeaturedProducts();
    const dash = document.getElementById('navDashboard');
    if (dash) {
        dash.addEventListener('click', async (e) => {
            if (!sessionStorage.getItem('userPhone')) {
                e.preventDefault();
                const phone = await requireLoginForAction('open your dashboard');
                if (phone) window.location.href = 'dashboard.html';
            }
        });
    }
});
