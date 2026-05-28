// Shopping cart — single source of truth, localStorage key: 'ethioshop_cart'

const CART_KEY = 'ethioshop_cart';

class ShoppingCart {
    constructor() {
        this._migrateOldKey();
        this.items = this._load();
    }

    // One-time migration: move data from old 'cart' key to 'ethioshop_cart'
    _migrateOldKey() {
        const old = localStorage.getItem('cart');
        if (old && !localStorage.getItem(CART_KEY)) {
            localStorage.setItem(CART_KEY, old);
        }
        if (old) localStorage.removeItem('cart');
    }

    _load() {
        try {
            const saved = localStorage.getItem(CART_KEY);
            return saved ? JSON.parse(saved) : [];
        } catch { return []; }
    }

    _save() {
        localStorage.setItem(CART_KEY, JSON.stringify(this.items));
        this.updateBadge();
    }

    addItem(product) {
        const existing = this.items.find(i => i.product_id === product.id);
        if (existing) {
            existing.quantity += 1;
        } else {
            this.items.push({
                product_id: product.id,
                name: product.name,
                price: product.price,
                quantity: 1,
                image_url: product.thumbnail_url || product.image_url
            });
        }
        this._save();
        this._toast(`${product.name} added to cart`);
    }

    removeItem(productId) {
        this.items = this.items.filter(i => i.product_id !== productId);
        this._save();
    }

    updateQuantity(productId, quantity) {
        const item = this.items.find(i => i.product_id === productId);
        if (item) {
            item.quantity = Math.max(1, parseInt(quantity) || 1);
            this._save();
        }
    }

    getSubtotal() {
        return this.items.reduce((sum, i) => sum + i.price * i.quantity, 0);
    }

    getItemCount() {
        return this.items.reduce((sum, i) => sum + i.quantity, 0);
    }

    clear() {
        this.items = [];
        this._save();
    }

    updateBadge() {
        document.querySelectorAll('.cart-badge').forEach(badge => {
            const count = this.getItemCount();
            badge.textContent = count;
            badge.style.display = count > 0 ? 'inline-block' : 'none';
        });
    }

    _toast(message) {
        const el = document.createElement('div');
        el.textContent = message;
        el.style.cssText = `position:fixed;top:20px;right:20px;background:#4CAF50;color:white;
            padding:12px 20px;border-radius:6px;z-index:10000;font-size:14px;
            box-shadow:0 4px 12px rgba(0,0,0,0.15);`;
        document.body.appendChild(el);
        setTimeout(() => el.remove(), 2500);
    }
}

// Global singleton
const cart = new ShoppingCart();

document.addEventListener('DOMContentLoaded', () => cart.updateBadge());
