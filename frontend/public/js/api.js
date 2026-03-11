// API Client for Planned Event Management System

const API_BASE_URL = '/api/v1';

class ApiClient {
    constructor() {
        this.token = localStorage.getItem('access_token');
    }

    setToken(token) {
        this.token = token;
        localStorage.setItem('access_token', token);
    }

    clearToken() {
        this.token = null;
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
    }

    async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers,
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        try {
            const response = await fetch(url, {
                ...options,
                headers,
            });

            if (response.status === 401) {
                this.clearToken();
                window.location.href = '/pages/login.html';
                return null;
            }

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Request failed');
            }

            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // Auth endpoints
    async login(username, password) {
        const data = await this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password }),
        });
        if (data) {
            this.setToken(data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);
        }
        return data;
    }

    async register(userData) {
        return this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify(userData),
        });
    }

    async getCurrentUser() {
        return this.request('/auth/me');
    }

    // Event endpoints
    async getEvents(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return this.request(`/events?${queryString}`);
    }

    async getStats() {
        return this.request('/events/stats');
    }

    async getEvent(eventId) {
        return this.request(`/events/${eventId}`);
    }

    async createEvent(eventData) {
        return this.request('/events', {
            method: 'POST',
            body: JSON.stringify(eventData),
        });
    }

    async updateEvent(eventId, eventData) {
        return this.request(`/events/${eventId}`, {
            method: 'PUT',
            body: JSON.stringify(eventData),
        });
    }

    async deleteEvent(eventId) {
        return this.request(`/events/${eventId}`, {
            method: 'DELETE',
        });
    }

    async submitEvent(eventId) {
        return this.request(`/events/${eventId}/submit`, {
            method: 'POST',
        });
    }

    async startEvent(eventId) {
        return this.request(`/events/${eventId}/start`, {
            method: 'POST',
        });
    }

    async completeEvent(eventId, reason = null) {
        return this.request(`/events/${eventId}/complete`, {
            method: 'POST',
            body: JSON.stringify({ reason }),
        });
    }

    async revertEvent(eventId, reason = null) {
        return this.request(`/events/${eventId}/revert`, {
            method: 'POST',
            body: JSON.stringify({ reason }),
        });
    }

    async postponeEvent(eventId, reason = null) {
        return this.request(`/events/${eventId}/postpone`, {
            method: 'POST',
            body: JSON.stringify({ reason }),
        });
    }

    async deferEvent(eventId, reason = null) {
        return this.request(`/events/${eventId}/defer`, {
            method: 'POST',
            body: JSON.stringify({ reason }),
        });
    }

    async returnToDraftEvent(eventId, reason = null) {
        return this.request(`/events/${eventId}/return-to-draft`, {
            method: 'POST',
            body: JSON.stringify({ reason }),
        });
    }

    async getEventHistory(eventId) {
        return this.request(`/events/${eventId}/history`);
    }

    // Device endpoints
    async addDeviceToEvent(eventId, deviceData) {
        return this.request(`/events/${eventId}/devices`, {
            method: 'POST',
            body: JSON.stringify(deviceData),
        });
    }

    async addDevicesBulk(eventId, devices) {
        return this.request(`/events/${eventId}/devices/bulk`, {
            method: 'POST',
            body: JSON.stringify({ devices }),
        });
    }

    async removeDeviceFromEvent(eventId, deviceId) {
        return this.request(`/events/${eventId}/devices/${deviceId}`, {
            method: 'DELETE',
        });
    }

    async getExternalDevices(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return this.request(`/devices?${queryString}`);
    }

    async searchDevices(query) {
        return this.request(`/devices/search?q=${encodeURIComponent(query)}`);
    }

    // Approval endpoints
    async getPendingApprovals() {
        return this.request('/approvals/pending');
    }

    async approveEvent(eventId, comments = null) {
        return this.request(`/approvals/${eventId}/approve`, {
            method: 'POST',
            body: JSON.stringify({ comments }),
        });
    }

    async rejectEvent(eventId, comments = null) {
        return this.request(`/approvals/${eventId}/reject`, {
            method: 'POST',
            body: JSON.stringify({ comments }),
        });
    }

    // User endpoints
    async getUsers() {
        return this.request('/users');
    }

    async updateUserRole(userId, role) {
        return this.request(`/users/${userId}/role`, {
            method: 'PUT',
            body: JSON.stringify({ role }),
        });
    }

    // File upload helpers
    async uploadMOP(eventId, file) {
        const formData = new FormData();
        formData.append('file', file);

        const url = `${API_BASE_URL}/events/${eventId}/mop/upload`;
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`,
            },
            body: formData,
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || 'Upload failed');
        }

        return response.json();
    }

    async uploadDevicesCSV(eventId, file) {
        const formData = new FormData();
        formData.append('file', file);

        const url = `${API_BASE_URL}/events/${eventId}/devices/csv`;
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`,
            },
            body: formData,
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || 'Upload failed');
        }

        return response.json();
    }
}

// Export singleton instance
const api = new ApiClient();
