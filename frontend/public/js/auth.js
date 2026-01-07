// Authentication utilities

function isAuthenticated() {
    return !!localStorage.getItem('access_token');
}

function getCurrentUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
}

function setCurrentUser(user) {
    localStorage.setItem('user', JSON.stringify(user));
}

function logout() {
    api.clearToken();
    window.location.href = '/pages/login.html';
}

function requireAuth() {
    if (!isAuthenticated()) {
        window.location.href = '/pages/login.html';
        return false;
    }
    return true;
}

function requireRole(...roles) {
    const user = getCurrentUser();
    if (!user || !roles.includes(user.role)) {
        return false;
    }
    return true;
}

// Update header with user info
function updateHeader() {
    const user = getCurrentUser();
    const userMenu = document.querySelector('.user-menu');
    const navLinks = document.querySelector('nav');

    if (userMenu && user) {
        userMenu.innerHTML = `
            <span class="user-name">${user.full_name || user.username}</span>
            <span class="badge badge-${user.role}">${formatRole(user.role)}</span>
            <button class="btn btn-outline btn-sm" onclick="logout()">Logout</button>
        `;
    }

    // Show/hide nav links based on role
    if (navLinks && user) {
        const approvalsLink = navLinks.querySelector('a[href*="approvals"]');
        const usersLink = navLinks.querySelector('a[href*="users"]');

        if (approvalsLink) {
            if (['approver_l1', 'approver_l2', 'admin'].includes(user.role)) {
                approvalsLink.classList.remove('hidden');
            } else {
                approvalsLink.classList.add('hidden');
            }
        }

        if (usersLink) {
            if (user.role === 'admin') {
                usersLink.classList.remove('hidden');
            } else {
                usersLink.classList.add('hidden');
            }
        }
    }
}

function formatRole(role) {
    const roles = {
        'user': 'User',
        'approver_l1': 'Approver L1',
        'approver_l2': 'Approver L2',
        'admin': 'Admin'
    };
    return roles[role] || role;
}

// Initialize auth on page load
document.addEventListener('DOMContentLoaded', async () => {
    const isLoginPage = window.location.pathname.includes('login.html');

    if (!isLoginPage && isAuthenticated()) {
        try {
            const user = await api.getCurrentUser();
            setCurrentUser(user);
            updateHeader();
        } catch (error) {
            console.error('Failed to get user info:', error);
            logout();
        }
    }
});
