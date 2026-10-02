// Main custom JS for Expense Tracker (can contain global event handlers or validation helpers)

document.addEventListener('DOMContentLoaded', () => {
    console.log('Expense Tracker Application initialized successfully.');
    
    // Auto-dismiss Bootstrap alert messages after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
});
