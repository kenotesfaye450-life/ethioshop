// frontend/config.js – hardcoded Railway backend URL
(function () {
    const API_BASE_URL = 'https://web-production-afefc.up.railway.app';

    window.API_BASE_URL = API_BASE_URL;
    window.ADMIN_API_BASE_URL = `${API_BASE_URL}/api`;

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

    window.SOCIAL_LINKS = {
        tiktok: 'https://www.tiktok.com/@ethioshopofficial',
        facebook: 'https://www.facebook.com/profile.php?id=61590636471935',
        youtube: 'https://www.youtube.com/@KenoTesfayeOfficial',
        instagram: 'https://www.instagram.com/your_ethioshop_handle/',  // replace with your actual Instagram
        telegram_channel: 'https://t.me/ethioshopchannel',
        telegram_group: 'https://t.me/ethioshopofficial',
        telegram_bot: 'https://t.me/EthioShopTrusted_bot'
    };
})();

var API_BASE_URL = window.API_BASE_URL;
var ADMIN_API_BASE_URL = window.ADMIN_API_BASE_URL;
var API_ENDPOINTS = window.API_ENDPOINTS;
var SOCIAL_LINKS = window.SOCIAL_LINKS;
