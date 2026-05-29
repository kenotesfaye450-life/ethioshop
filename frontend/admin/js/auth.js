// Shared admin auth helpers + login page handler

// Hardcoded Railway backend API root (no trailing slash)
const ADMIN_API = 'https://web-production-afefc.up.railway.app/api';

function getToken() {
    const token = localStorage.getItem('adminToken');
    if (!token) {
        window.location.href = 'index.html';
        throw new Error('Not authenticated');
    }
    return token;
}

function authHeaders() {
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`
    };
}

function logout() {
    localStorage.removeItem('adminToken');
    localStorage.removeItem('adminUser');
    window.location.href = 'index.html';
}

async function apiFetch(path, options = {}) {
    const res = await fetch(`${ADMIN_API}${path}`, {
        ...options,
        headers: { ...authHeaders(), ...(options.headers || {}) }
    });
    if (res.status === 401) {
        logout();
        throw new Error('Session expired');
    }
    return res;
}

function initAdminName() {
    const admin = JSON.parse(localStorage.getItem('adminUser') || '{}');
    const el = document.getElementById('adminName');
    if (el) el.textContent = admin.username || 'Admin';
}

async function handleLogin(event) {
    event.preventDefault();

    const loginBtn = document.getElementById('loginBtn');
    const errorEl = document.getElementById('error');

    loginBtn.disabled = true;
    loginBtn.textContent = 'Logging in...';
    errorEl.style.display = 'none';

    try {
        const username = document.getElementById('username').value;
        const phone = document.getElementById('phone').value;
        const password = document.getElementById('password').value;

        const response = await fetch(`${ADMIN_API}/admin/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, phone, password })
        });

        const data = await response.json();

        if (!data.success) {
            throw new Error(data.error?.message || 'Login failed');
        }

        localStorage.setItem('adminToken', data.token);
        localStorage.setItem('adminUser', JSON.stringify(data.admin));
        window.location.href = 'orders.html';
    } catch (error) {
        errorEl.textContent = error.message;
        errorEl.style.display = 'block';
        loginBtn.disabled = false;
        loginBtn.textContent = 'Login';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        if (localStorage.getItem('adminToken')) {
            window.location.href = 'orders.html';
            return;
        }
        loginForm.addEventListener('submit', handleLogin);
        return;
    }
    initAdminName();
});
