// NFC Handler for Sony PaSoRi Integration
// This provides frontend interface for NFC scanning

class NFCHandler {
    constructor() {
        this.isEnabled = false;
        this.scannerStatus = 'disconnected';
        this.init();
    }
    
    init() {
        // Check if NFC is enabled in settings
        this.checkNFCStatus();
        
        // Setup scan input field if exists
        const scanField = document.getElementById('nfc-scan-input');
        if (scanField) {
            scanField.addEventListener('input', (e) => this.handleScan(e));
        }
    }
    
    checkNFCStatus() {
        // Check backend NFC configuration
        fetch('/dashboard/api/nfc-status/')
            .then(response => response.json())
            .then(data => {
                this.isEnabled = data.enabled;
                this.updateStatusIndicator();
            })
            .catch(() => {
                this.isEnabled = false;
                this.updateStatusIndicator();
            });
    }
    
    updateStatusIndicator() {
        const indicator = document.getElementById('nfc-status-indicator');
        if (!indicator) return;
        
        if (this.isEnabled) {
            indicator.innerHTML = '<span style="color: green;">● NFC Ready</span>';
        } else {
            indicator.innerHTML = '<span style="color: gray;">○ NFC Disabled</span>';
        }
    }
    
    handleScan(event) {
        const uid = event.target.value.trim();
        
        if (uid.length >= 8) {
            this.processNFCScan(uid);
            event.target.value = ''; // Clear input
        }
    }
    
    processNFCScan(uid) {
        console.log('NFC UID scanned:', uid);
        
        // Send to backend for processing
        fetch('/dashboard/api/nfc-scan/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify({ uid: uid })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.handleSuccessfulScan(data);
            } else {
                this.handleFailedScan(data.message);
            }
        })
        .catch(error => {
            console.error('NFC scan error:', error);
            this.showNotification('NFC scan failed', 'error');
        });
    }
    
    handleSuccessfulScan(data) {
        // Show notification
        this.showNotification(`Welcome, ${data.employee_name}!`, 'success');
        
        // If this is for work order operation
        if (data.action === 'work_order_start') {
            this.showNotification(`Work Order ${data.wo_number} started`, 'info');
        } else if (data.action === 'work_order_stop') {
            this.showNotification(`Work Order ${data.wo_number} completed`, 'info');
        }
        
        // Optionally redirect or refresh
        if (data.redirect_url) {
            setTimeout(() => {
                window.location.href = data.redirect_url;
            }, 1500);
        }
    }
    
    handleFailedScan(message) {
        this.showNotification(message || 'NFC card not recognized', 'error');
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `nfc-notification nfc-notification-${type}`;
        notification.textContent = message;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    }
    
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }
    
    // Quick scan for work order operations
    scanForWorkOrder(woId, action) {
        const scanInput = document.getElementById('nfc-scan-input');
        if (!scanInput) {
            alert('NFC scanner not available');
            return;
        }
        
        // Store work order context
        scanInput.dataset.woId = woId;
        scanInput.dataset.action = action;
        
        // Focus scan input
        scanInput.focus();
        this.showNotification(`Please scan NFC card to ${action} work order`, 'info');
    }
}

// Initialize NFC handler when DOM is ready
let nfcHandler;
document.addEventListener('DOMContentLoaded', function() {
    nfcHandler = new NFCHandler();
});

// CSS for notifications (add to admin-custom.css)
const nfcStyles = `
.nfc-notification {
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 15px 20px;
    border-radius: 4px;
    color: white;
    font-weight: bold;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    opacity: 0;
    transform: translateX(100%);
    transition: all 0.3s ease;
    z-index: 10000;
}

.nfc-notification.show {
    opacity: 1;
    transform: translateX(0);
}

.nfc-notification-success {
    background-color: #4CAF50;
}

.nfc-notification-error {
    background-color: #F44336;
}

.nfc-notification-info {
    background-color: #2196F3;
}

.nfc-scan-field {
    position: fixed;
    bottom: 20px;
    right: 20px;
    padding: 10px;
    background: white;
    border: 2px solid #2196F3;
    border-radius: 4px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.nfc-scan-field input {
    border: none;
    outline: none;
    padding: 5px;
    font-size: 14px;
}

#nfc-status-indicator {
    position: fixed;
    bottom: 20px;
    left: 20px;
    padding: 8px 12px;
    background: white;
    border-radius: 4px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    font-size: 12px;
}
`;

// Inject styles
const styleSheet = document.createElement('style');
styleSheet.textContent = nfcStyles;
document.head.appendChild(styleSheet);