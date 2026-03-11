// Main application utilities

// Show alert message
function showAlert(message, type = 'success') {
    const alertsContainer = document.getElementById('alerts') || createAlertsContainer();

    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.textContent = message;

    alertsContainer.appendChild(alert);

    setTimeout(() => {
        alert.remove();
    }, 5000);
}

function createAlertsContainer() {
    const container = document.createElement('div');
    container.id = 'alerts';
    container.style.cssText = 'position: fixed; top: 80px; right: 20px; z-index: 1001; width: 300px;';
    document.body.appendChild(container);
    return container;
}

// Format date for display
function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// Format time for display
function formatTime(timeStr) {
    if (!timeStr) return '-';
    return timeStr.substring(0, 5);
}

// Format datetime
function formatDateTime(dateTimeStr) {
    if (!dateTimeStr) return '-';
    const date = new Date(dateTimeStr);
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Get status badge HTML
function getStatusBadge(status) {
    const labels = {
        'draft': 'Draft',
        'submitted': 'Submitted',
        'approved_l1': 'Approved L1',
        'approved_l2': 'Approved L2',
        'in_progress': 'In Progress',
        'completed': 'Completed',
        'rejected': 'Rejected',
        'reverted': 'Reverted',
        'postponed': 'Postponed',
        'deferred': 'Deferred'
    };
    return `<span class="badge badge-${status}">${labels[status] || status}</span>`;
}

// Show loading spinner
function showLoading(container) {
    container.innerHTML = `
        <div class="loading-container">
            <div class="spinner"></div>
        </div>
    `;
}

// Show empty state
function showEmptyState(container, message = 'No data found') {
    container.innerHTML = `
        <div class="empty-state">
            <h3>${message}</h3>
            <p>Try adjusting your filters or create a new item.</p>
        </div>
    `;
}

// Modal utilities
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
    }
}

// Close modal when clicking outside
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay')) {
        e.target.classList.remove('active');
    }
});

// Parse CSV text to array of objects
function parseCSV(text) {
    const lines = text.trim().split('\n');
    if (lines.length < 2) return [];

    const headers = lines[0].split(',').map(h => h.trim().toLowerCase());
    const data = [];

    for (let i = 1; i < lines.length; i++) {
        const values = lines[i].split(',').map(v => v.trim());
        const obj = {};
        headers.forEach((header, index) => {
            obj[header] = values[index] || '';
        });
        data.push(obj);
    }

    return data;
}

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// URL query params helper
function getQueryParams() {
    const params = new URLSearchParams(window.location.search);
    const result = {};
    for (const [key, value] of params) {
        result[key] = value;
    }
    return result;
}

function setQueryParams(params) {
    const url = new URL(window.location);
    Object.keys(params).forEach(key => {
        if (params[key]) {
            url.searchParams.set(key, params[key]);
        } else {
            url.searchParams.delete(key);
        }
    });
    window.history.pushState({}, '', url);
}
