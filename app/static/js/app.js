/**
 * Boston AI Life Sciences ERP - Frontend JavaScript
 */

// Check authentication on page load
document.addEventListener('DOMContentLoaded', () => {
    const user = localStorage.getItem('user');
    if (!user && !window.location.pathname.includes('/auth/')) {
        window.location.href = '/auth/login';
    }
});

/**
 * API Helper
 */
class APIHelper {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        const token = localStorage.getItem('auth_token');
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        try {
            const response = await fetch(url, {
                ...options,
                headers
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Request failed');
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }

    post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }
}

const api = new APIHelper();

/**
 * Utility Functions
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function formatDate(dateString) {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem;
        border-radius: 4px;
        z-index: 1000;
        background-color: ${type === 'error' ? '#fee2e2' : type === 'success' ? '#d1fae5' : '#dbeafe'};
        color: ${type === 'error' ? '#991b1b' : type === 'success' ? '#065f46' : '#1e40af'};
    `;
    document.body.appendChild(notification);

    setTimeout(() => notification.remove(), 3000);
}

function handleApiError(error) {
    showNotification(error.message || 'An error occurred', 'error');
    console.error('Error:', error);
}

/**
 * Navigation Helper
 */
function navigateTo(module) {
    window.location.href = `/${module}`;
}

/**
 * Authentication
 */
async function login(username, password) {
    try {
        const response = await fetch('/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok) {
            localStorage.setItem('user', JSON.stringify(data.user));
            window.location.href = '/dashboard';
        } else {
            throw new Error(data.error || 'Login failed');
        }
    } catch (error) {
        throw error;
    }
}

function logout() {
    localStorage.removeItem('user');
    localStorage.removeItem('auth_token');
    window.location.href = '/auth/login';
}

/**
 * Form Validation
 */
function validateForm(formElement) {
    const requiredFields = formElement.querySelectorAll('[required]');
    let isValid = true;

    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('error');
            isValid = false;
        } else {
            field.classList.remove('error');
        }
    });

    return isValid;
}

/**
 * Data Tables Helper
 */
function initDataTable(tableId, options = {}) {
    const table = document.getElementById(tableId);
    if (!table) return;

    // Basic sorting could be added here
    // For production, consider using a library like DataTables.js
}

/**
 * Module Specific Functions
 */
const ProcurementModule = {
    async loadSuppliers() {
        return api.get('/procurement/suppliers');
    },

    async loadPurchaseOrders() {
        return api.get('/procurement/purchase-orders');
    },

    async loadMaterials() {
        return api.get('/procurement/materials');
    }
};

const SalesModule = {
    async loadCustomers() {
        return api.get('/sales/customers');
    },

    async loadSalesOrders() {
        return api.get('/sales/sales-orders');
    }
};

const FinancialModule = {
    async loadInvoices() {
        return api.get('/financial/invoices');
    },

    async loadPayments() {
        return api.get('/financial/payments');
    },

    async loadJournalEntries() {
        return api.get('/financial/journal-entries');
    }
};

const ReportingModule = {
    async loadDashboard() {
        return api.get('/reporting/dashboard');
    },

    async loadInventoryReport(warehouseId) {
        const endpoint = warehouseId
            ? `/reporting/reports/inventory?warehouse_id=${warehouseId}`
            : '/reporting/reports/inventory';
        return api.get(endpoint);
    }
};

// Export for use in other modules
window.APIHelper = APIHelper;
window.api = api;
window.navigateTo = navigateTo;
window.formatCurrency = formatCurrency;
window.formatDate = formatDate;
window.showNotification = showNotification;
window.handleApiError = handleApiError;
window.validateForm = validateForm;
