// Shared customer UI enhancements: social footer, announcement modal, mobile nav.
(function () {
    function injectFontAwesome() {
        if (document.querySelector('link[data-fa6]')) return;
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.dataset.fa6 = '1';
        link.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css';
        document.head.appendChild(link);
    }

    function ensureAboutTopRight() {
        const navLinks = document.querySelector('.nav-links');
        if (!navLinks) return;
        let about = Array.from(navLinks.querySelectorAll('a')).find(a => (a.getAttribute('href') || '').includes('about.html'));
        if (!about) {
            about = document.createElement('a');
            about.href = 'about.html';
            about.textContent = 'About';
            navLinks.appendChild(about);
        }
        about.classList.add('about-top-link');
    }

    function injectMobileMenu() {
        const nav = document.querySelector('.navbar .container');
        const links = document.querySelector('.nav-links');
        if (!nav || !links || document.getElementById('mobileMenuToggle')) return;
        const btn = document.createElement('button');
        btn.id = 'mobileMenuToggle';
        btn.className = 'mobile-menu-toggle';
        btn.type = 'button';
        btn.setAttribute('aria-label', 'Toggle navigation');
        btn.innerHTML = '<i class="fa-solid fa-bars"></i>';
        btn.onclick = () => links.classList.toggle('open');
        nav.appendChild(btn);
    }

    async function injectAnnouncementBanner() {
        try {
            const res = await fetch(`${window.API_BASE_URL || ''}/api/settings/announcement`);
            const data = await res.json();
            if (!data.success || !data.announcement?.announcement_active) return;
            if (sessionStorage.getItem('announcement_banner_dismissed') === '1') return;
            if (document.getElementById('announcementBanner')) return;

            const ann = data.announcement;
            const banner = document.createElement('div');
            banner.id = 'announcementBanner';
            banner.className = 'announcement-banner';
            banner.innerHTML = `
                <div class="announcement-banner-inner">
                    <span>📢 ${ann.announcement_message || ''}</span>
                    <button type="button" id="announcementBannerClose" aria-label="Dismiss">×</button>
                </div>
            `;
            const header = document.querySelector('header');
            if (header) {
                document.body.insertBefore(banner, header);
            } else {
                document.body.prepend(banner);
            }
            document.getElementById('announcementBannerClose').onclick = () => {
                sessionStorage.setItem('announcement_banner_dismissed', '1');
                banner.remove();
            };
        } catch (_) {
            // no-op
        }
    }

    async function injectAnnouncementModal() {
        try {
            const res = await fetch(`${window.API_BASE_URL || ''}/api/settings/announcement`);
            const data = await res.json();
            if (!data.success || !data.announcement?.announcement_active) return;
            if (sessionStorage.getItem('announcement_dismissed') === '1') return;
            if (document.getElementById('announcementModal')) return;

            const ann = data.announcement;
            const closeDelay = Math.max(Number(ann.announcement_close_delay_seconds) || 3, 3);
            const displaySeconds = Math.max(Number(ann.announcement_display_seconds) || 0, 0);

            const overlay = document.createElement('div');
            overlay.id = 'announcementModal';
            overlay.className = 'announcement-modal-overlay';
            overlay.innerHTML = `
                <div class="announcement-modal" role="dialog" aria-labelledby="announcementTitle">
                    <h3 id="announcementTitle">📢 Announcement</h3>
                    <p class="announcement-modal-body">${ann.announcement_message || ''}</p>
                    <button type="button" id="announcementCloseBtn" class="btn btn-primary" disabled>
                        Close (${closeDelay}s)
                    </button>
                </div>
            `;
            document.body.appendChild(overlay);

            const btn = document.getElementById('announcementCloseBtn');
            let remaining = closeDelay;
            const tick = setInterval(() => {
                remaining -= 1;
                if (remaining > 0) {
                    btn.textContent = `Close (${remaining}s)`;
                } else {
                    clearInterval(tick);
                    btn.disabled = false;
                    btn.textContent = 'Close';
                }
            }, 1000);

            const dismiss = () => {
                sessionStorage.setItem('announcement_dismissed', '1');
                overlay.remove();
            };
            btn.onclick = () => { if (!btn.disabled) dismiss(); };
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay && !btn.disabled) dismiss();
            });

            if (displaySeconds > 0) {
                setTimeout(() => {
                    if (document.getElementById('announcementModal')) dismiss();
                }, displaySeconds * 1000);
            }
        } catch (_) {
            // Ignore failures
        }
    }

    function injectSocialFooter() {
        let footerContainer = document.querySelector('footer .container');
        if (!footerContainer) {
            footerContainer = document.querySelector('footer');
        }
        if (!footerContainer || footerContainer.querySelector('.footer-social-icons')) return;
        const html = `
            <div class="footer-social-icons">
                <a href="https://www.tiktok.com/@ethioshopofficial" target="_blank" rel="noopener noreferrer" aria-label="TikTok"><i class="fa-brands fa-tiktok"></i></a>
                <a href="https://www.facebook.com/profile.php?id=61590636471935" target="_blank" rel="noopener noreferrer" aria-label="Facebook"><i class="fa-brands fa-facebook"></i></a>
                <a href="https://www.youtube.com/@KenoTesfayeOfficial" target="_blank" rel="noopener noreferrer" aria-label="YouTube"><i class="fa-brands fa-youtube"></i></a>
                <a href="https://t.me/ethioshopchannel" target="_blank" rel="noopener noreferrer" aria-label="Telegram Channel"><i class="fa-brands fa-telegram"></i></a>
                <a href="https://t.me/ethioshopofficial" target="_blank" rel="noopener noreferrer" aria-label="Telegram Group"><i class="fa-solid fa-user-group"></i></a>
                <a href="https://t.me/EthioShopTrusted_bot" target="_blank" rel="noopener noreferrer" aria-label="Telegram Bot"><i class="fa-solid fa-robot"></i></a>
            </div>
        `;
        footerContainer.insertAdjacentHTML('beforeend', html);
    }

    function injectTrustBadges() {
        if (document.body.classList.contains('landing-page')) return;
        const mainContainer = document.querySelector('main .container');
        if (!mainContainer || document.querySelector('.trust-badges')) return;
        const el = document.createElement('div');
        el.className = 'trust-badges';
        el.innerHTML = `
            <span><i class="fa-solid fa-shield-halved"></i> Secure payments (Telebirr/CBE)</span>
            <span><i class="fa-solid fa-circle-check"></i> Verified shop</span>
            <span><i class="fa-solid fa-truck"></i> Free delivery &gt;1000 ETB</span>
        `;
        mainContainer.prepend(el);
    }

    async function startRecentSalesPopup() {
        if (document.body.classList.contains('landing-page')) return;
        try {
            const res = await fetch(`${window.API_BASE_URL || ''}/api/products/recent-sales`);
            const data = await res.json();
            const items = data.items || [];
            if (!items.length) return;
            let idx = 0;
            const holder = document.createElement('div');
            holder.className = 'toast-container';
            holder.style.left = '1rem';
            holder.style.right = 'auto';
            holder.style.bottom = '1rem';
            document.body.appendChild(holder);

            const show = () => {
                const it = items[idx % items.length];
                idx += 1;
                const toast = document.createElement('div');
                toast.className = 'toast show';
                toast.textContent = `Someone in ${it.city || 'Addis Ababa'} just bought ${it.product_name}.`;
                holder.appendChild(toast);
                setTimeout(() => toast.remove(), 5000);
            };
            show();
            setInterval(show, 10000);
        } catch (_) {
            // no-op
        }
    }

    document.addEventListener('DOMContentLoaded', () => {
        injectFontAwesome();
        ensureAboutTopRight();
        injectMobileMenu();
        injectSocialFooter();
        injectTrustBadges();
        injectAnnouncementBanner();
        injectAnnouncementModal();
        startRecentSalesPopup();
    });
})();
