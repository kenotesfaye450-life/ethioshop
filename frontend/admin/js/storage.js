async function scanOrphans(doDelete) {
    try {
        const res = await apiFetch('/admin/storage/cleanup', {
            method: 'POST',
            body: JSON.stringify({ delete: doDelete, prefix: '' }),
        });
        const data = await res.json();
        if (!data.success) throw new Error(data.error?.message);
        renderStorageData(data);
        alert(doDelete ? 'Cleanup completed' : 'Scan completed');
    } catch (e) {
        alert(e.message);
    }
}

function renderStorageData(data) {
    const usage = data.usage || {};
    document.getElementById('storageUsage').innerHTML = `
        <p><strong>Referenced assets:</strong> ${data.referenced_count}</p>
        <p><strong>Orphans found:</strong> ${data.orphans_count}</p>
        <p><strong>Cloudinary storage:</strong> ${(usage.storage?.used_bytes || 0)} bytes used</p>
    `;
    const rows = (data.orphans || []).map(o => `
        <tr>
            <td>${o.public_id}</td>
            <td>${o.bytes || 0}</td>
            <td>${o.url ? `<a href="${o.url}" target="_blank" rel="noopener noreferrer">View</a>` : '-'}</td>
        </tr>
    `).join('');
    document.getElementById('orphansTable').innerHTML = rows ? `
        <table class="products-table">
            <thead><tr><th>Public ID</th><th>Bytes</th><th>URL</th></tr></thead>
            <tbody>${rows}</tbody>
        </table>
    ` : '<p>No orphaned images found.</p>';
}
