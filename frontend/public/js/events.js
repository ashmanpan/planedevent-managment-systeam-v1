// Events page functionality

let currentPage = 1;
let currentFilters = {};

// Load events list
async function loadEvents(page = 1, filters = {}) {
    const tableBody = document.getElementById('events-table-body');
    if (!tableBody) return;

    // Show loading spinner in tbody only
    tableBody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 40px;"><div class="spinner"></div></td></tr>';

    try {
        const params = {
            page,
            limit: 20,
            ...filters
        };

        // Remove empty params
        Object.keys(params).forEach(key => {
            if (!params[key]) delete params[key];
        });

        const response = await api.getEvents(params);

        if (response.items.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 40px; color: #666;"><h3>No events found</h3><p>Try adjusting your filters or create a new event.</p></td></tr>';
            updatePagination(1, 0, 0);
            return;
        }

        tableBody.innerHTML = response.items.map(event => `
            <tr onclick="window.location.href='/pages/event-detail.html?id=${event.id}'">
                <td><strong>${escapeHtml(event.title)}</strong></td>
                <td>${formatDate(event.scheduled_date)}</td>
                <td>${formatTime(event.start_time)} - ${formatTime(event.end_time)}</td>
                <td>${getStatusBadge(event.status)}</td>
                <td>${event.devices ? event.devices.length : 0} devices</td>
                <td>${event.creator ? (event.creator.full_name || event.creator.username) : '-'}</td>
                <td>${formatDateTime(event.created_at)}</td>
            </tr>
        `).join('');

        // Update pagination
        updatePagination(response.page, response.pages, response.total);

        currentPage = page;
        currentFilters = filters;

    } catch (error) {
        showAlert(error.message, 'error');
        tableBody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 40px; color: #d32f2f;"><h3>Error loading events</h3><p>' + error.message + '</p></td></tr>';
    }
}

function updatePagination(currentPage, totalPages, totalItems) {
    const pagination = document.getElementById('pagination');
    if (!pagination) return;

    let html = '';

    html += `<button onclick="loadEvents(${currentPage - 1}, currentFilters)" ${currentPage <= 1 ? 'disabled' : ''}>Prev</button>`;

    for (let i = 1; i <= totalPages; i++) {
        if (i === 1 || i === totalPages || (i >= currentPage - 2 && i <= currentPage + 2)) {
            html += `<button onclick="loadEvents(${i}, currentFilters)" class="${i === currentPage ? 'active' : ''}">${i}</button>`;
        } else if (i === currentPage - 3 || i === currentPage + 3) {
            html += '<span>...</span>';
        }
    }

    html += `<button onclick="loadEvents(${currentPage + 1}, currentFilters)" ${currentPage >= totalPages ? 'disabled' : ''}>Next</button>`;

    pagination.innerHTML = html;
}

// Apply filters
function applyFilters() {
    const filters = {
        status: document.getElementById('filter-status')?.value || '',
        start_date: document.getElementById('filter-start-date')?.value || '',
        end_date: document.getElementById('filter-end-date')?.value || '',
        device_name: document.getElementById('filter-device')?.value || '',
    };

    loadEvents(1, filters);
}

// Clear filters
function clearFilters() {
    document.getElementById('filter-status').value = '';
    document.getElementById('filter-start-date').value = '';
    document.getElementById('filter-end-date').value = '';
    document.getElementById('filter-device').value = '';

    loadEvents(1, {});
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize events page
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('events-table-body')) {
        if (!requireAuth()) return;
        loadEvents();
    }
});
