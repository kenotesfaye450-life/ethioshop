// Browser notifications + in-app notification inbox

const NotificationCenter = {
    STORAGE_KEY: 'ethioshop_notifications',
    PERM_KEY: 'ethioshop_notif_asked',

    load() {
        try {
            return JSON.parse(localStorage.getItem(this.STORAGE_KEY) || '[]');
        } catch {
            return [];
        }
    },

    save(list) {
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(list.slice(0, 50)));
        this.updateBell();
    },

    add(title, body, type = 'info') {
        const list = this.load();
        list.unshift({
            id: Date.now(),
            title,
            body,
            type,
            read: false,
            at: new Date().toISOString(),
        });
        this.save(list);
    },

    unreadCount() {
        return this.load().filter(n => !n.read).length;
    },

    updateBell() {
        const badge = document.getElementById('notifBadge');
        const count = this.unreadCount();
        if (badge) {
            badge.textContent = count > 9 ? '9+' : count;
            badge.style.display = count > 0 ? 'inline-block' : 'none';
        }
    },

    async requestPermissionOnce() {
        if (!('Notification' in window)) return false;
        if (localStorage.getItem(this.PERM_KEY)) return Notification.permission === 'granted';
        localStorage.setItem(this.PERM_KEY, '1');
        if (Notification.permission === 'default') {
            const result = await Notification.requestPermission();
            return result === 'granted';
        }
        return Notification.permission === 'granted';
    },

    pushBrowser(title, body) {
        if (!('Notification' in window) || Notification.permission !== 'granted') return;
        try {
            new Notification(title, { body, icon: 'assets/images/placeholder.jpg' });
        } catch (e) {
            console.warn('Notification failed', e);
        }
    },

    notify(title, body, type = 'info') {
        this.add(title, body, type);
        this.pushBrowser(title, body);
        if (typeof showToast === 'function') showToast(body, type);
    },

    renderPanel() {
        const panel = document.getElementById('notifPanel');
        if (!panel) return;
        const list = this.load();
        if (!list.length) {
            panel.innerHTML = '<p style="padding:1rem;color:#888;">No notifications yet.</p>';
            return;
        }
        panel.innerHTML = list.map(n => `
            <div class="notif-item ${n.read ? '' : 'unread'}" onclick="NotificationCenter.markRead(${n.id})">
                <strong>${n.title}</strong>
                <p>${n.body}</p>
                <small>${new Date(n.at).toLocaleString()}</small>
            </div>
        `).join('');
    },

    markRead(id) {
        const list = this.load().map(n => (n.id === id ? { ...n, read: true } : n));
        this.save(list);
        this.renderPanel();
    },

    markAllRead() {
        this.save(this.load().map(n => ({ ...n, read: true })));
        this.renderPanel();
    },

    togglePanel() {
        const panel = document.getElementById('notifPanel');
        if (!panel) return;
        const open = panel.style.display === 'block';
        panel.style.display = open ? 'none' : 'block';
        if (!open) {
            this.markAllRead();
            this.renderPanel();
        }
    },
};

function showToast(message, type = 'info') {
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    const el = document.createElement('div');
    el.className = `toast toast-${type}`;
    el.textContent = message;
    container.appendChild(el);
    setTimeout(() => el.classList.add('show'), 10);
    setTimeout(() => {
        el.classList.remove('show');
        setTimeout(() => el.remove(), 300);
    }, 4500);
}
