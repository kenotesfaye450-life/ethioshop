async function runCleanup(action, execute) {
    const el = document.getElementById(`result-${action}`);
    el.textContent = 'Working...';
    try {
        const res = await apiFetch('/admin/cleanup', {
            method: 'POST',
            body: JSON.stringify({ action, execute }),
        });
        const data = await res.json();
        if (!data.success) throw new Error(data.error?.message || 'Failed');
        el.textContent = execute
            ? `Deleted ${data.count} record(s).`
            : `Preview: ${data.count} record(s) would be deleted.`;
    } catch (e) {
        el.textContent = `Error: ${e.message}`;
    }
}

function previewCleanup(action) {
    runCleanup(action, false);
}

function executeCleanup(action) {
    const labels = {
        test_orders: 'pending_verification orders older than 7 days',
        unconfirmed_users: 'users with no orders older than 30 days',
    };
    if (!confirm(`Permanently delete ${labels[action]}?`)) return;
    runCleanup(action, true);
}
