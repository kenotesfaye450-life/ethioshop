function uploadBaseUrl() {
    return ADMIN_API.replace(/\/api\/?$/, '');
}

const SETTING_FIELDS = [
    'owner_name', 'owner_title', 'owner_image_url', 'owner_bio', 'years_experience',
    'contact_phone', 'social_telegram', 'social_facebook', 'owner_message',
    'announcement_message', 'max_referral_per_year', 'request_reward_etb',
    'announcement_close_delay_seconds', 'announcement_display_seconds',
];

async function loadSettings() {
    const res = await apiFetch('/admin/settings');
    const data = await res.json();
    if (!data.success) throw new Error(data.error?.message);
    const s = data.settings;
    SETTING_FIELDS.forEach(k => {
        const el = document.getElementById(k);
        if (el) el.value = s[k] ?? '';
    });
    const activeEl = document.getElementById('announcement_active');
    if (activeEl) activeEl.checked = Boolean(s.announcement_active);
}

document.getElementById('settingsForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {};
    SETTING_FIELDS.forEach(k => {
        payload[k] = document.getElementById(k).value;
    });
    payload.announcement_active = document.getElementById('announcement_active')?.checked || false;

    const file = document.getElementById('ownerImageFile').files[0];
    if (file) {
        const fd = new FormData();
        fd.append('file', file);
        fd.append('folder', 'about');
        const upRes = await fetch(`${uploadBaseUrl()}/api/upload/image`, {
            method: 'POST',
            headers: { Authorization: `Bearer ${getToken()}` },
            body: fd,
        });
        const upData = await upRes.json();
        if (!upData.success) throw new Error(upData.error?.message || 'Upload failed');
        payload.owner_image_url = upData.url || upData.image_url;
    }

    const res = await apiFetch('/admin/settings', { method: 'PATCH', body: JSON.stringify(payload) });
    const data = await res.json();
    if (!data.success) throw new Error(data.error?.message);
    alert('Settings saved');
    await loadSettings();
});

document.addEventListener('DOMContentLoaded', () => loadSettings().catch(e => alert(e.message)));
