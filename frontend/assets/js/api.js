// API utility functions

async function apiCall(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error?.message || 'Request failed');
        }

        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

const ProductAPI = {
    getAll: (category = null) => {
        const url = category
            ? `${API_ENDPOINTS.products}?category=${encodeURIComponent(category)}`
            : API_ENDPOINTS.products;
        return apiCall(url);
    },
    getById: (id) => apiCall(`${API_ENDPOINTS.products}/${id}`),
    getRecentSales: () => apiCall(`${API_ENDPOINTS.products}/recent-sales`),
};

const UserAPI = {
    getByPhone: (phone) => apiCall(`${API_ENDPOINTS.users}/${encodeURIComponent(phone)}`),
    create: (userData) => apiCall(API_ENDPOINTS.users, { method: 'POST', body: JSON.stringify(userData) }),
    getOrders: (phone) => apiCall(`${API_ENDPOINTS.users}/${encodeURIComponent(phone)}/orders`),
    getRequests: (phone) => apiCall(`${API_ENDPOINTS.users}/${encodeURIComponent(phone)}/requests`),
    getRefunds: (phone) => apiCall(`${API_ENDPOINTS.users}/${encodeURIComponent(phone)}/refunds`),
    getQuestions: (phone) => apiCall(`${API_ENDPOINTS.users}/${encodeURIComponent(phone)}/questions`),
};

const QuestionAPI = {
    ask: (productId, payload) => apiCall(`${API_BASE_URL}/api/products/${productId}/ask`, {
        method: 'POST',
        body: JSON.stringify(payload),
    }),
};

const RequestAPI = {
    getById: (id) => apiCall(`${API_ENDPOINTS.requests}/${id}`),
    convert: (id, payload) => apiCall(`${API_ENDPOINTS.requests}/${id}/convert`, {
        method: 'POST',
        body: JSON.stringify(payload),
    }),
};

const OrderAPI = {
    create: (orderData) => apiCall(API_ENDPOINTS.orders, { method: 'POST', body: JSON.stringify(orderData) }),
    getById: (id) => apiCall(`${API_ENDPOINTS.orders}/${id}`),
    uploadPaymentProof: (id, payload) => apiCall(`${API_ENDPOINTS.orders}/${id}/payment-proof`, {
        method: 'PATCH',
        body: JSON.stringify(payload),
    }),
    payRemaining: (id, payload) => apiCall(`${API_ENDPOINTS.orders}/${id}/pay-remaining`, {
        method: 'POST',
        body: JSON.stringify(payload),
    }),
    confirmDelivery: (id, payload) => apiCall(`${API_ENDPOINTS.orders}/${id}/confirm-delivery`, {
        method: 'POST',
        body: JSON.stringify(payload),
    }),
    submitReviews: (id, payload) => apiCall(`${API_ENDPOINTS.orders}/${id}/reviews`, {
        method: 'POST',
        body: JSON.stringify(payload),
    }),
};

const RefundAPI = {
    uploadEvidence: (id, payload) => apiCall(`${API_ENDPOINTS.refunds}/${id}/upload-evidence`, {
        method: 'PATCH',
        body: JSON.stringify(payload),
    }),
};

const AdminAPI = {
    login: (username, password) => apiCall(`${API_ENDPOINTS.admin}/login`, {
        method: 'POST',
        body: JSON.stringify({ username, password }),
    }),
};
