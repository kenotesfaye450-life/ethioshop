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
        test_orders: 'abandoned pending_verification orders (no payment, no proof) older than 7 days',
        unconfirmed_users: 'users with no orders older than 30 days',
    };
    if (!confirm(`Permanently delete ${labels[action]}?`)) return;
    if (action === 'test_orders') {
        const typed = prompt('Type DELETE to confirm permanent deletion of test orders:');
        if (typed !== 'DELETE') {
            alert('Cleanup cancelled — you must type DELETE exactly.');
            return;
        }
    }
    runCleanup(action, true);
}
