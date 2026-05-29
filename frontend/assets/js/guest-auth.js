/** Prompt for phone when guest tries a protected action; auto-register minimal user. */
async function ensureUserPhone(promptMessage) {
    let phone = sessionStorage.getItem('userPhone');
    if (phone) return phone;

    const entered = window.prompt(promptMessage || 'Enter your Ethiopian phone number to continue (e.g. 0912345678):');
    if (!entered) return null;

    const normalized = typeof normalizeEthiopianPhone === 'function'
        ? normalizeEthiopianPhone(entered)
        : null;
    if (!normalized) {
        alert('Invalid Ethiopian phone number. Use 09xxxxxxxx or 07xxxxxxxx.');
        return null;
    }
    const name = window.prompt('Your full name (for delivery):', sessionStorage.getItem('userName') || '') || 'Customer';

    try {
        const ref = new URLSearchParams(window.location.search).get('ref');
        const payload = { phone: normalized, name, referral_code: ref || undefined };
        const res = await fetch(`${API_BASE_URL}/api/users`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        const data = await res.json();
        if (!data.success && data.error?.code !== 'VALIDATION_ERROR') {
            throw new Error(data.error?.message || 'Registration failed');
        }
        sessionStorage.setItem('userPhone', normalized);
        sessionStorage.setItem('userName', name);
        return normalized;
    } catch (e) {
        alert(e.message || 'Could not save your phone. Try again from the home page.');
        return null;
    }
}

function requireLoginForAction(action) {
    return ensureUserPhone(`Please enter your phone number to ${action}:`);
}
