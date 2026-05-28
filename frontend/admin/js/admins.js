// Admin user management logic

async function loadAdmins() {
    const container = document.getElementById('adminsContainer');
    container.innerHTML = '<p style="color:#999;padding:1rem;">Loading...</p>';

    try {
        const res  = await apiFetch('/admin/users');
        const data = await res.json();
        if (!data.success) throw new Error(data.error?.message);

        const admins = data.admins || [];
        if (!admins.length) {
            container.innerHTML = '<p style="color:#999;padding:1rem;">No admins found.</p>';
            return;
        }

        container.innerHTML = `
            <table class="orders-table">
                <thead><tr>
                    <th>ID</th><th>Username</th><th>Phone</th><th>Role</th><th>Created</th>
                </tr></thead>
                <tbody>
                    ${admins.map(a => `
                        <tr>
                            <td>#${a.id}</td>
                            <td>${a.username}</td>
                            <td>${a.phone}</td>
                            <td><span class="status-badge">${a.role.replace(/_/g,' ')}</span></td>
                            <td>${new Date(a.created_at).toLocaleDateString()}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    } catch (err) {
        container.innerHTML = `<p style="color:red;">Error: ${err.message}</p>`;
    }
}

function showCreateModal() {
    document.getElementById('createModal').style.display = 'block';
}

function closeCreateModal() {
    document.getElementById('createModal').style.display = 'none';
    document.getElementById('createForm').reset();
}

async function createAdmin(event) {
    event.preventDefault();
    const payload = {
        username: document.getElementById('newUsername').value,
        phone:    document.getElementById('newPhone').value,
        password: document.getElementById('newPassword').value,
        role:     document.getElementById('newRole').value
    };

    try {
        const res  = await apiFetch('/admin/users', { method: 'POST', body: JSON.stringify(payload) });
        const data = await res.json();
        if (!data.success) throw new Error(data.error?.message);
        alert('Admin created successfully');
        closeCreateModal();
        loadAdmins();
    } catch (err) { alert('Error: ' + err.message); }
}

document.addEventListener('DOMContentLoaded', () => {
    loadAdmins();
    window.onclick = e => {
        if (e.target === document.getElementById('createModal')) closeCreateModal();
    };
});
