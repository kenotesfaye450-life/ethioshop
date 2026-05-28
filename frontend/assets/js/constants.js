// Shared constants — single source of truth for the entire frontend.
// Include this before any script that needs these values.

const PRODUCT_CATEGORIES = [
    'Shoes', 'Clothing', 'Watches', 'Phones', 'Beauty',
    'Bags', 'Electronics', 'Home Essentials', 'Perfumes',
    'Sports', 'Earphones', 'Blankets', 'Jewelry', 'Thermoses'
];

const ORDER_STATUSES = [
    'pending_verification', 'confirmed', 'rejected',
    'in_transit', 'delivered', 'refunded'
];

const DELIVERY_STATUSES = [
    'pending_assignment', 'assigned', 'in_transit', 'delivered'
];

const PAYMENT_METHODS = [
    { value: 'Telebirr',      label: 'Telebirr',           account: '0912345678',    holder: 'EthioShop Trading' },
    { value: 'CBE',           label: 'CBE Birr',           account: '1000123456789', holder: 'EthioShop Trading' },
    { value: 'Bank Transfer', label: 'Awash Bank Transfer', account: '013456789012',  holder: 'EthioShop Trading' }
];

const MIN_ORDER_ETB = 500;
