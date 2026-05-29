// Checkout functionality

let currentUser = null;

function getStoredReferralCode() {
    return (
        sessionStorage.getItem('referral_code')
        || sessionStorage.getItem('referralCode')
        || null
    );
}

(function captureReferralFromUrl() {
    const ref = new URLSearchParams(window.location.search).get('ref');
    if (ref) {
        const cleaned = ref.trim();
        sessionStorage.setItem('referral_code', cleaned);
        sessionStorage.setItem('referralCode', cleaned);
    }
})();

async function initCheckout() {
    // Check if cart has items
    if (cart.items.length === 0) {
        alert('Your cart is empty');
        window.location.href = 'shop.html';
        return;
    }
    
    // Check minimum order
    const subtotal = cart.getSubtotal();
    if (subtotal < 500) {
        alert('Minimum order is 500 ETB');
        window.location.href = 'cart.html';
        return;
    }
    
    // Display cart summary
    displayCartSummary();
    
    // Load user if phone is stored
    const storedPhone = sessionStorage.getItem('userPhone');
    const storedName = sessionStorage.getItem('userName');
    if (storedName) {
        document.getElementById('fullName').value = storedName;
    }
    if (storedPhone) {
        document.getElementById('phone').value = storedPhone;
        await loadUserData(storedPhone);
    }
}

function displayCartSummary() {
    const summaryEl = document.getElementById('orderSummary');
    const subtotal = cart.getSubtotal();
    
    const itemsHtml = cart.items.map(item => `
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
            <span>${item.name} x ${item.quantity}</span>
            <span>${(item.price * item.quantity).toFixed(2)} ETB</span>
        </div>
    `).join('');
    
    summaryEl.innerHTML = `
        <h3>Order Summary</h3>
        ${itemsHtml}
        <hr style="margin: 1rem 0;">
        <div style="display: flex; justify-content: space-between; font-weight: bold; font-size: 1.2rem;">
            <span>Subtotal:</span>
            <span id="subtotalAmount">${subtotal.toFixed(2)} ETB</span>
        </div>
        <div id="creditSection" style="display: none; margin-top: 1rem;">
            <div style="display: flex; justify-content: space-between; color: #27ae60;">
                <span>Credit Applied:</span>
                <span id="creditAmount">0 ETB</span>
            </div>
            <div style="display: flex; justify-content: space-between; font-weight: bold; font-size: 1.3rem; margin-top: 0.5rem;">
                <span>Final Total:</span>
                <span id="finalTotal">${subtotal.toFixed(2)} ETB</span>
            </div>
        </div>
    `;
}

async function loadUserData(phone) {
    try {
        const response = await UserAPI.getByPhone(phone);
        currentUser = response.user;
        
        // Show credit info if user has credit
        if (currentUser.credit_balance > 0) {
            const creditInfo = document.getElementById('creditInfo');
            creditInfo.style.display = 'block';
            creditInfo.innerHTML = `
                <p>Available Credit: <strong>${currentUser.credit_balance} ETB</strong></p>
                <label>
                    <input type="checkbox" id="useCredit" onchange="toggleCredit()">
                    Use available credit (max 50% of order or 500 ETB)
                </label>
            `;
        }
    } catch (error) {
        console.log('User not found, will create new user');
    }
}

function toggleCredit() {
    const useCredit = document.getElementById('useCredit').checked;
    const creditSection = document.getElementById('creditSection');
    const subtotal = cart.getSubtotal();
    
    if (useCredit && currentUser) {
        const maxCredit = Math.min(
            subtotal * 0.5,
            500,
            currentUser.credit_balance
        );
        
        const finalTotal = subtotal - maxCredit;
        
        document.getElementById('creditAmount').textContent = `${maxCredit.toFixed(2)} ETB`;
        document.getElementById('finalTotal').textContent = `${finalTotal.toFixed(2)} ETB`;
        creditSection.style.display = 'block';
    } else {
        creditSection.style.display = 'none';
    }
}

async function submitOrder(event) {
    event.preventDefault();
    
    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Processing...';
    
    try {
        const phone = document.getElementById('phone').value.trim();
        const fullName = document.getElementById('fullName').value.trim();
        const paymentMethod = document.getElementById('paymentMethod').value;
        const paymentPlan = document.querySelector('input[name="paymentPlan"]:checked')?.value || 'half';
        const address = document.getElementById('address').value;

        if (fullName.length < 2) {
            throw new Error('Please enter your full name.');
        }
        
        // Create or get user
        if (!currentUser) {
            const payload = { phone, name: fullName };
            const ref = getStoredReferralCode();
            if (ref) payload.referral_code = ref;
            const userResponse = await UserAPI.create(payload);
            currentUser = userResponse.user;
            sessionStorage.setItem('userPhone', phone);
            sessionStorage.setItem('userName', currentUser.name || fullName);
        }
        
        // Calculate credit usage
        let creditUsed = 0;
        const useCredit = document.getElementById('useCredit');
        if (useCredit && useCredit.checked) {
            const subtotal = cart.getSubtotal();
            creditUsed = Math.min(
                subtotal * 0.5,
                500,
                currentUser.credit_balance
            );
        }
        
        // Prepare order data
        const localName = document.getElementById('localPersonName')?.value.trim();
        const localPhone = document.getElementById('localPersonPhone')?.value.trim();
        const localNotes = document.getElementById('localPersonNotes')?.value.trim();

        const orderData = {
            phone: phone,
            items: cart.items.map(item => ({
                product_id: item.product_id,
                quantity: item.quantity
            })),
            payment_method: paymentMethod,
            payment_plan: paymentPlan,
            credit_used: creditUsed,
            delivery_location: {
                type: 'manual',
                address: address
            }
        };
        if (localName) orderData.local_person_name = localName;
        if (localPhone) orderData.local_person_phone = localPhone;
        if (localNotes) orderData.local_person_notes = localNotes;
        
        // Create order
        const response = await OrderAPI.create(orderData);
        
        // Clear cart
        cart.clear();
        
        // Show success
        sessionStorage.setItem('userPhone', phone);
        alert(`Order #${response.order.id} created successfully! Please upload payment proof.`);
        window.location.href = `order-success.html?id=${response.order.id}`;
        
    } catch (error) {
        alert(`Error creating order: ${error.message}`);
        submitBtn.disabled = false;
        submitBtn.textContent = 'Place Order';
    }
}

function updateEscrowMessage() {
    const box = document.getElementById('escrowMessage');
    if (!box) return;
    const half = document.querySelector('input[name="paymentPlan"]:checked')?.value === 'half';
    box.style.display = half ? 'block' : 'none';
}

async function useCurrentLocation() {
    const statusEl = document.getElementById('locationStatus');
    const addressEl = document.getElementById('address');
    if (!navigator.geolocation) {
        if (statusEl) statusEl.textContent = 'Geolocation is not supported on this device.';
        return;
    }
    if (statusEl) statusEl.textContent = 'Getting your location…';
    navigator.geolocation.getCurrentPosition(async (pos) => {
        try {
            const { latitude, longitude } = pos.coords;
            const url = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}`;
            const res = await fetch(url, { headers: { 'Accept-Language': 'en' } });
            const data = await res.json();
            const addr = data.display_name || '';
            if (addressEl && addr) {
                addressEl.value = addr;
                sessionStorage.setItem('delivery_location', JSON.stringify({
                    address: addr,
                    city: data.address?.city || data.address?.town || data.address?.state || '',
                    lat: latitude,
                    lon: longitude,
                }));
            }
            if (statusEl) statusEl.textContent = 'Location applied. You can edit the address if needed.';
        } catch (e) {
            if (statusEl) statusEl.textContent = 'Could not resolve address. Please type it manually.';
        }
    }, () => {
        if (statusEl) statusEl.textContent = 'Location denied. Please enter your address manually.';
    }, { enableHighAccuracy: true, timeout: 15000 });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initCheckout();
    updateEscrowMessage();
});
window.updateEscrowMessage = updateEscrowMessage;
window.useCurrentLocation = useCurrentLocation;
