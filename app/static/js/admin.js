// Admin Dashboard Common JavaScript Functions

class AdminDashboard {
    constructor() {
        this.currentPage = 1;
        this.itemsPerPage = 10;
        this.filteredData = [];
        this.currentItemId = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeData();
    }

    setupEventListeners() {
        // Search functionality
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.addEventListener('input', () => this.filterData());
        }

        // Status filter
        const statusFilter = document.getElementById('statusFilter');
        if (statusFilter) {
            statusFilter.addEventListener('change', () => this.filterData());
        }

        // Modal close on outside click
        window.addEventListener('click', (event) => {
            const modals = document.querySelectorAll('.modal');
            modals.forEach(modal => {
                if (event.target === modal) {
                    this.closeModal(modal.id);
                }
            });
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                this.closeAllModals();
            }
        });
    }

    initializeData() {
        const tableRows = document.querySelectorAll('#dataTable tr');
        this.filteredData = Array.from(tableRows);
        this.updatePagination();
    }

    filterData() {
        const searchTerm = document.getElementById('searchInput')?.value.toLowerCase() || '';
        const statusFilter = document.getElementById('statusFilter')?.value || '';

        const rows = document.querySelectorAll('#dataTable tr');
        this.filteredData = Array.from(rows).filter(row => {
            const cells = Array.from(row.cells);
            const searchableText = cells.map(cell => cell.textContent.toLowerCase()).join(' ');
            const status = cells[5]?.textContent.toLowerCase() || '';

            const matchesSearch = searchableText.includes(searchTerm);
            const matchesStatus = !statusFilter || status.includes(statusFilter);

            return matchesSearch && matchesStatus;
        });

        this.currentPage = 1;
        this.displayCurrentPage();
        this.updatePagination();
    }

    displayCurrentPage() {
        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = startIndex + this.itemsPerPage;
        const pageData = this.filteredData.slice(startIndex, endIndex);

        const tbody = document.getElementById('dataTable');
        if (!tbody) return;

        tbody.innerHTML = '';
        pageData.forEach(row => {
            tbody.appendChild(row.cloneNode(true));
        });
    }

    updatePagination() {
        const totalCount = this.filteredData.length;
        const startIndex = (this.currentPage - 1) * this.itemsPerPage + 1;
        const endIndex = Math.min(this.currentPage * this.itemsPerPage, totalCount);

        const startElement = document.getElementById('startIndex');
        const endElement = document.getElementById('endIndex');
        const totalElement = document.getElementById('totalCount');

        if (startElement) startElement.textContent = startIndex;
        if (endElement) endElement.textContent = endIndex;
        if (totalElement) totalElement.textContent = totalCount;
    }

    previousPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            this.displayCurrentPage();
            this.updatePagination();
        }
    }

    nextPage() {
        const maxPage = Math.ceil(this.filteredData.length / this.itemsPerPage);
        if (this.currentPage < maxPage) {
            this.currentPage++;
            this.displayCurrentPage();
            this.updatePagination();
        }
    }

    async viewDetails(itemId, endpoint) {
        try {
            const response = await fetch(`/api/${endpoint}/${itemId}`);
            if (!response.ok) throw new Error('Failed to fetch details');

            const data = await response.json();
            this.showDetailsModal(data, endpoint);
        } catch (error) {
            console.error('Error fetching details:', error);
            this.showNotification('Error loading details', 'error');
        }
    }

    showDetailsModal(data, type) {
        const modal = document.getElementById('detailsModal');
        const content = document.getElementById('modalContent');

        if (!modal || !content) return;

        let html = '<div class="space-y-4">';

        // Generate content based on type
        switch (type) {
            case 'export-inquiry':
                html += this.generateExportInquiryContent(data);
                break;
            case 'import-inquiry':
                html += this.generateImportInquiryContent(data);
                break;
            case 'business-opportunity':
                html += this.generateBusinessOpportunityContent(data);
                break;
            case 'suggestion':
                html += this.generateSuggestionContent(data);
                break;
            case 'complaint':
                html += this.generateComplaintContent(data);
                break;
            default:
                html += this.generateGenericContent(data);
        }

        html += '</div>';
        content.innerHTML = html;
        modal.style.display = 'block';
    }

    generateExportInquiryContent(data) {
        return `
            <div><strong>Full Name:</strong> ${data.full_name}</div>
            <div><strong>Company:</strong> ${data.company_name}</div>
            <div><strong>Email:</strong> ${data.email}</div>
            <div><strong>Phone:</strong> ${data.phone_number}</div>
            <div><strong>Country:</strong> ${data.country}</div>
            <div><strong>Product Quantity:</strong> ${data.product_quantity}</div>
            <div><strong>Product Details:</strong> ${data.product_details}</div>
            <div><strong>Export Requirements:</strong> ${data.export_requirements}</div>
            <div><strong>Submitted:</strong> ${data.submitted_at}</div>
        `;
    }

    generateImportInquiryContent(data) {
        return `
            <div><strong>Full Name:</strong> ${data.full_name}</div>
            <div><strong>Company:</strong> ${data.company_name}</div>
            <div><strong>Email:</strong> ${data.email}</div>
            <div><strong>Phone:</strong> ${data.phone_number}</div>
            <div><strong>Country:</strong> ${data.country}</div>
            <div><strong>Product Quantity:</strong> ${data.product_quantity}</div>
            <div><strong>Product Details:</strong> ${data.product_details}</div>
            <div><strong>Sender Details:</strong> ${data.sender_details}</div>
            <div><strong>Submitted:</strong> ${data.submitted_at}</div>
        `;
    }

    generateBusinessOpportunityContent(data) {
        return `
            <div><strong>Full Name:</strong> ${data.full_name}</div>
            <div><strong>Email:</strong> ${data.email}</div>
            <div><strong>Phone:</strong> ${data.phone_number}</div>
            <div><strong>Business Opportunity:</strong>
                <div class="mt-2 p-3 bg-gray-50 rounded-md">
                    ${data.business_opportunity}
                </div>
            </div>
            <div><strong>Submitted:</strong> ${data.submitted_at}</div>
        `;
    }

    generateSuggestionContent(data) {
        return `
            <div><strong>Full Name:</strong> ${data.full_name}</div>
            <div><strong>Email:</strong> ${data.email}</div>
            <div><strong>Phone:</strong> ${data.phone_number}</div>
            <div><strong>Suggestion:</strong>
                <div class="mt-2 p-3 bg-gray-50 rounded-md">
                    ${data.suggestions}
                </div>
            </div>
            <div><strong>Submitted:</strong> ${data.submitted_at}</div>
        `;
    }

    generateComplaintContent(data) {
        return `
            <div><strong>Full Name:</strong> ${data.full_name}</div>
            <div><strong>Email:</strong> ${data.email}</div>
            <div><strong>Phone:</strong> ${data.phone_number}</div>
            <div><strong>Complaint:</strong>
                <div class="mt-2 p-3 bg-gray-50 rounded-md">
                    ${data.complaints}
                </div>
            </div>
            <div><strong>Submitted:</strong> ${data.submitted_at}</div>
        `;
    }

    generateGenericContent(data) {
        return Object.entries(data).map(([key, value]) =>
            `<div><strong>${key.replace(/_/g, ' ').toUpperCase()}:</strong> ${value}</div>`
        ).join('');
    }

    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
        }
    }

    closeAllModals() {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            modal.style.display = 'none';
        });
    }

    async deleteItem(itemId, endpoint, itemName) {
        if (!confirm(`Are you sure you want to delete this ${itemName}?`)) {
            return;
        }

        try {
            const response = await fetch(`/api/${endpoint}/${itemId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (!response.ok) throw new Error('Failed to delete item');

            const data = await response.json();
            if (data.success) {
                this.showNotification(`${itemName} deleted successfully`, 'success');
                location.reload();
            } else {
                throw new Error('Delete operation failed');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showNotification(`Error deleting ${itemName}`, 'error');
        }
    }

    async updateStatus(itemId, endpoint, itemName) {
        this.currentItemId = itemId;
        const modal = document.getElementById('statusModal');
        if (modal) {
            modal.style.display = 'block';
        }
    }

    async saveStatus() {
        if (!this.currentItemId) return;

        const status = document.getElementById('statusSelect')?.value;
        const notes = document.getElementById('statusNotes')?.value;

        try {
            const response = await fetch(`/api/${this.currentItemId}/status`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    status: status,
                    notes: notes
                })
            });

            if (!response.ok) throw new Error('Failed to update status');

            const data = await response.json();
            if (data.success) {
                this.showNotification('Status updated successfully', 'success');
                this.closeModal('statusModal');
                location.reload();
            } else {
                throw new Error('Status update failed');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showNotification('Error updating status', 'error');
        }
    }

    exportToCSV(headers, filename) {
        const csvContent = [
            headers.join(','),
            ...this.filteredData.map(row => {
                const cells = row.cells;
                return Array.from(cells).map(cell =>
                    `"${cell.textContent.replace(/"/g, '""')}"`
                ).join(',');
            })
        ].join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        window.URL.revokeObjectURL(url);

        this.showNotification('CSV exported successfully', 'success');
    }

    refreshData() {
        location.reload();
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-md shadow-lg z-50 ${type === 'success' ? 'bg-green-500 text-white' :
                type === 'error' ? 'bg-red-500 text-white' :
                    'bg-blue-500 text-white'
            }`;
        notification.textContent = message;

        // Add to page
        document.body.appendChild(notification);

        // Remove after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }

    // Utility functions
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    }

    truncateText(text, maxLength = 100) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    debounce(func, wait) {
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
}

// Initialize admin dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    window.adminDashboard = new AdminDashboard();
});

// Global functions for HTML onclick handlers
function viewDetails(itemId) {
    const endpoint = getCurrentEndpoint();
    window.adminDashboard.viewDetails(itemId, endpoint);
}

function deleteItem(itemId) {
    const endpoint = getCurrentEndpoint();
    const itemName = getCurrentItemName();
    window.adminDashboard.deleteItem(itemId, endpoint, itemName);
}

function updateStatus(itemId) {
    const endpoint = getCurrentEndpoint();
    const itemName = getCurrentItemName();
    window.adminDashboard.updateStatus(itemId, endpoint, itemName);
}

function saveStatus() {
    window.adminDashboard.saveStatus();
}

function closeModal(modalId) {
    window.adminDashboard.closeModal(modalId);
}

function previousPage() {
    window.adminDashboard.previousPage();
}

function nextPage() {
    window.adminDashboard.nextPage();
}

function exportToCSV() {
    const headers = getCurrentHeaders();
    const filename = getCurrentFilename();
    window.adminDashboard.exportToCSV(headers, filename);
}

function refreshData() {
    window.adminDashboard.refreshData();
}

function filterData() {
    window.adminDashboard.filterData();
}

// Helper functions to determine current page context
function getCurrentEndpoint() {
    const path = window.location.pathname;
    if (path.includes('export-inquiry')) return 'export-inquiry';
    if (path.includes('import-inquiry')) return 'import-inquiry';
    if (path.includes('business-opportunity')) return 'business-opportunity';
    if (path.includes('suggestions')) return 'suggestion';
    if (path.includes('complaints')) return 'complaint';
    return 'item';
}

function getCurrentItemName() {
    const path = window.location.pathname;
    if (path.includes('export-inquiry')) return 'export inquiry';
    if (path.includes('import-inquiry')) return 'import inquiry';
    if (path.includes('business-opportunity')) return 'business opportunity';
    if (path.includes('suggestions')) return 'suggestion';
    if (path.includes('complaints')) return 'complaint';
    return 'item';
}

function getCurrentHeaders() {
    const path = window.location.pathname;
    if (path.includes('export-inquiry')) {
        return ['Name', 'Company', 'Email', 'Phone', 'Country', 'Product Quantity', 'Product Details', 'Export Requirements', 'Submitted'];
    }
    if (path.includes('import-inquiry')) {
        return ['Name', 'Company', 'Email', 'Phone', 'Country', 'Product Quantity', 'Product Details', 'Sender Details', 'Submitted'];
    }
    if (path.includes('business-opportunity')) {
        return ['Name', 'Email', 'Phone', 'Business Opportunity', 'Submitted'];
    }
    if (path.includes('suggestions')) {
        return ['Name', 'Email', 'Phone', 'Suggestion', 'Submitted'];
    }
    if (path.includes('complaints')) {
        return ['Name', 'Email', 'Phone', 'Complaint', 'Submitted'];
    }
    return ['Name', 'Email', 'Submitted'];
}

function getCurrentFilename() {
    const path = window.location.pathname;
    if (path.includes('export-inquiry')) return 'export_inquiries.csv';
    if (path.includes('import-inquiry')) return 'import_inquiries.csv';
    if (path.includes('business-opportunity')) return 'business_opportunities.csv';
    if (path.includes('suggestions')) return 'suggestions.csv';
    if (path.includes('complaints')) return 'complaints.csv';
    return 'data.csv';
} 