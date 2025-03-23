// Form validation
(function () {
    'use strict';
    
    // Fetch all forms we want to apply validation to
    const forms = document.querySelectorAll('.needs-validation');
    
    // Loop over them and prevent submission
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
})();

// Handle form submission
document.getElementById('uploadForm').addEventListener('submit', async (e) => {
    e.preventDefault(); // Prevent default form submission
    
    const form = e.target;
    if (!form.checkValidity()) {
        return; // Don't proceed if form is invalid
    }

    const bethaFile = document.getElementById('bethaFile').files[0];
    const tceFile = document.getElementById('tceFile').files[0];
    const mode = document.getElementById('mode').value;

    if (!bethaFile || !tceFile) {
        showNotification('Por favor, selecione ambos os arquivos.', 'warning');
        return;
    }

    // Show the processing indicator
    const processingIndicator = document.getElementById('processing');
    processingIndicator.classList.remove('d-none');
    
    // Hide any previous results
    const outputElement = document.getElementById('output');
    outputElement.innerHTML = '';

    try {
        // Submit the form directly for page reload approach
        form.submit();
    } catch (error) {
        console.error('Erro:', error);
        processingIndicator.classList.add('d-none');
        showNotification('Erro ao processar os arquivos: ' + error.message, 'danger');
    }
});

// Function to show notifications
function showNotification(message, type = 'info') {
    const notificationArea = document.createElement('div');
    notificationArea.className = `alert alert-${type} alert-dismissible fade show mt-3`;
    notificationArea.role = 'alert';
    
    notificationArea.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add to the page before the output area
    const outputArea = document.getElementById('output');
    outputArea.parentNode.insertBefore(notificationArea, outputArea);
    
    // Auto dismiss after 5 seconds
    setTimeout(() => {
        const alert = document.querySelector('.alert');
        if (alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }
    }, 5000);
}

// Apply Bootstrap table classes to dynamically loaded tables
document.addEventListener('DOMContentLoaded', function() {
    // Add Bootstrap classes to tables that may be loaded from Flask
    const tables = document.querySelectorAll('table');
    tables.forEach(table => {
        if (!table.classList.contains('table')) {
            table.classList.add('table', 'table-striped', 'table-hover', 'table-sm');
        }
    });
});