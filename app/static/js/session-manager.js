// Session Manager for TransChamber Website
// This script helps manage multiple concurrent sessions

class SessionManager {
    constructor() {
        this.sessionCheckInterval = null;
        this.init();
    }

    init() {
        // Check session status every 30 seconds
        this.sessionCheckInterval = setInterval(() => {
            this.checkSessionStatus();
        }, 30000);

        // Check session on page load
        this.checkSessionStatus();

        // Add event listener for beforeunload to handle tab closing
        window.addEventListener('beforeunload', () => {
            this.handleTabClose();
        });
    }

    async checkSessionStatus() {
        try {
            const response = await fetch('/session-info');
            if (response.ok) {
                const sessionData = await response.json();
                this.updateSessionDisplay(sessionData);
            } else {
                // Session expired or invalid
                this.handleSessionExpired();
            }
        } catch (error) {
            console.error('Session check failed:', error);
            this.handleSessionExpired();
        }
    }

    updateSessionDisplay(sessionData) {
        // Update UI to show current session info
        const sessionInfo = document.getElementById('session-info');
        if (sessionInfo) {
            sessionInfo.innerHTML = `
                <small class="text-muted">
                    Logged in as: ${sessionData.current_user_username} (${sessionData.current_user_role})
                    <br>
                    Session ID: ${sessionData.session_id.substring(0, 8)}...
                </small>
            `;
        }

        // Update page title to show user role
        if (sessionData.current_user_role) {
            document.title = `TransChamber - ${sessionData.current_user_role.charAt(0).toUpperCase() + sessionData.current_user_role.slice(1)} Dashboard`;
        }
    }

    handleSessionExpired() {
        clearInterval(this.sessionCheckInterval);
        alert('Your session has expired. You will be redirected to the login page.');
        window.location.href = '/login';
    }

    handleTabClose() {
        // Clear the session check interval when tab is closed
        if (this.sessionCheckInterval) {
            clearInterval(this.sessionCheckInterval);
        }
    }

    // Method to logout from current session
    async logout() {
        try {
            const response = await fetch('/logout', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (response.ok) {
                window.location.href = '/login';
            }
        } catch (error) {
            console.error('Logout failed:', error);
            window.location.href = '/login';
        }
    }

    // Method to logout from all sessions
    async logoutAll() {
        if (confirm('Are you sure you want to logout from all sessions?')) {
            try {
                const response = await fetch('/logout-all', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });

                if (response.ok) {
                    window.location.href = '/login';
                }
            } catch (error) {
                console.error('Logout all failed:', error);
                window.location.href = '/login';
            }
        }
    }
}

// Initialize session manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize on protected pages (dashboard, admin pages)
    if (window.location.pathname.includes('/dashboard') ||
        window.location.pathname.includes('/admin') ||
        window.location.pathname.includes('/api/')) {
        window.sessionManager = new SessionManager();
    }
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SessionManager;
} 