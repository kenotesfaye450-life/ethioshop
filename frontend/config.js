// frontend/config.js
(function () {
    const getApiBaseUrl = () => {
        if (typeof window !== 'undefined' && window.__ETHIOSHOP_API_BASE_URL__) {
            return window.__ETHIOSHOP_API_BASE_URL__.replace(/\/$/, '');
        }
        if (typeof window !== 'undefined' &&
            (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')) {
            return 'http://localhost:5000';
        }
        return 'https://your-backend.onrender.com';
    };

    const API_BASE_URL = getApiBaseUrl();
    const ADMIN_API_BASE_URL = `${API_BASE_URL}/api`;

    window.API_BASE_URL = API_BASE_URL;
    window.ADMIN_API_BASE_URL = ADMIN_API_BASE_URL;

    window.API_ENDPOINTS = {
        products: `${API_BASE_URL}/api/products`,
        orders: `${API_BASE_URL}/api/orders`,
        users: `${API_BASE_URL}/api/users`,
        admin: `${API_BASE_URL}/api/admin`,
        upload: `${API_BASE_URL}/api/upload`,
        requests: `${API_BASE_URL}/api/requests`,
        refunds: `${API_BASE_URL}/api/refunds`,
        settings: `${API_BASE_URL}/api/settings`
    };

    // Legacy globals used by existing scripts
    window.SOCIAL_LINKS = {
        tiktok: 'https://www.tiktok.com/@ethioshopofficial',
        facebook: 'https://www.facebook.com/profile.php?id=61590636471935',
        youtube: 'https://www.youtube.com/@KenoTesfayeOfficial',
        telegram_channel: 'https://t.me/ethioshopchannel',
        telegram_group: 'https://t.me/ethioshopofficial',
        telegram_bot: 'https://t.me/EthioShopTrusted_bot'
    };
})();

// Non-window references for scripts that use bare identifiers
var API_BASE_URL = window.API_BASE_URL;
var ADMIN_API_BASE_URL = window.ADMIN_API_BASE_URL;
var API_ENDPOINTS = window.API_ENDPOINTS;
var SOCIAL_LINKS = window.SOCIAL_LINKS;
