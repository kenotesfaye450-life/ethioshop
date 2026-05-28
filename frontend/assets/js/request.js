// Demand request — upload image + description, submit to /api/requests

document.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('submitRequestBtn');
    if (btn) btn.addEventListener('click', submitRequest);

    // Pre-fill phone if stored in session
    const storedPhone = sessionStorage.getItem('userPhone');
    const storedName = sessionStorage.getItem('userName');
    const phoneInput = document.getElementById('requestPhone');
    const nameInput = document.getElementById('requestName');
    if (storedPhone && phoneInput) phoneInput.value = storedPhone;
    if (storedName && nameInput) nameInput.value = storedName;
});

async function submitRequest() {
    const name        = (document.getElementById('requestName')?.value || '').trim();
    const phone       = (document.getElementById('requestPhone')?.value || '').trim();
    const description = (document.getElementById('requestDesc')?.value || '').trim();
    const fileInput   = document.getElementById('requestImage');
    const budget      = document.getElementById('requestBudget')?.value;
    const btn         = document.getElementById('submitRequestBtn');

    // Basic validation
    if (!name || name.length < 2) {
        alert('Please enter your full name.');
        return;
    }
    if (!phone || !description) {
        alert('Phone number and description are required.');
        return;
    }
    if (!fileInput || !fileInput.files.length) {
        alert('Please select an image of the product you want.');
        return;
    }
    if (!document.getElementById('requestTermsAgree')?.checked) {
        alert('Please agree to the request terms before submitting.');
        return;
    }

    const phoneRegex = /^(\+251|251|0)[97]\d{8}$/;
    if (!phoneRegex.test(phone)) {
        alert('Invalid Ethiopian phone number. Use format: 0912345678 or +251912345678');
        return;
    }

    btn.disabled = true;
    btn.textContent = 'Submitting...';

    try {
        // 1. Ensure user exists
        const userRes = await fetch(`${API_BASE_URL}/api/users`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone, name })
        });
        if (!userRes.ok) {
            const err = await userRes.json();
            throw new Error(err.error?.message || 'Failed to register user');
        }
        sessionStorage.setItem('userPhone', phone);
        sessionStorage.setItem('userName', name);

        // 2. Upload image to Cloudinary via backend
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        formData.append('folder', 'requests');

        const uploadRes = await fetch(`${API_BASE_URL}/api/upload/image`, {
            method: 'POST',
            body: formData
        });
        if (!uploadRes.ok) {
            const err = await uploadRes.json();
            throw new Error(err.error?.message || 'Image upload failed');
        }
        const uploadData = await uploadRes.json();
        const imageUrl = uploadData.url;

        // 3. Submit request
        const payload = {
            phone,
            description,
            image_url: imageUrl,
        };
        if (budget && parseFloat(budget) > 0) {
            payload.budget = parseFloat(budget);
        }

        const reqRes = await fetch(`${API_BASE_URL}/api/requests`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const reqData = await reqRes.json();

        if (!reqRes.ok) {
            throw new Error(reqData.error?.message || 'Failed to submit request');
        }

        alert(`✅ Request #${reqData.request.id} submitted! Admin will review and quote you a price.`);
        window.location.href = 'dashboard.html';

    } catch (error) {
        alert(`Error: ${error.message}`);
        btn.disabled = false;
        btn.textContent = 'Submit Request';
    }
}
