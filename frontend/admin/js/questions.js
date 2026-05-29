async function loadQuestions() {
    const status = document.getElementById('statusFilter').value;
    const list = document.getElementById('questionsList');
    try {
        const res = await apiFetch(`/admin/questions?status=${encodeURIComponent(status)}`);
        const data = await res.json();
        const items = data.questions || [];
        if (!items.length) {
            list.innerHTML = '<p>No questions found.</p>';
            return;
        }
        list.innerHTML = items.map(q => `
            <div class="cart-container" style="margin-bottom:1rem;">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                    <div>
                        <strong>#${q.id}</strong> · ${q.product_name || 'Product'} · ${q.user_name || ''} (${q.user_phone || ''})
                        <span class="status-badge status-${q.status === 'answered' ? 'confirmed' : 'pending'}">${q.status}</span>
                    </div>
                    <small>${new Date(q.created_at).toLocaleString()}</small>
                </div>
                <p style="margin:0.75rem 0;"><strong>Q:</strong> ${escapeHtml(q.question)}</p>
                ${q.answer ? `<p style="color:#27ae60;"><strong>A:</strong> ${escapeHtml(q.answer)}</p>` : `
                    <textarea id="ans-${q.id}" rows="3" style="width:100%;margin:0.5rem 0;" placeholder="Type your answer..."></textarea>
                    <button class="btn btn-primary" onclick="submitAnswer(${q.id})">Send answer</button>
                `}
            </div>
        `).join('');
    } catch (e) {
        list.innerHTML = `<p style="color:red;">${e.message}</p>`;
    }
}

function escapeHtml(s) {
    return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

async function submitAnswer(id) {
    const ta = document.getElementById(`ans-${id}`);
    const answer = (ta?.value || '').trim();
    if (!answer) return alert('Enter an answer');
    try {
        const res = await apiFetch(`/admin/questions/${id}/answer`, {
            method: 'POST',
            body: JSON.stringify({ answer }),
        });
        const data = await res.json();
        if (!data.success) throw new Error(data.error?.message || 'Failed');
        loadQuestions();
    } catch (e) {
        alert(e.message);
    }
}

document.addEventListener('DOMContentLoaded', loadQuestions);
