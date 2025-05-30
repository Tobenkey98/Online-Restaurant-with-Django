document.addEventListener('DOMContentLoaded', function() {
    // Handle form submissions
    document.querySelectorAll('.status-update-form').forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const orderId = this.dataset.orderId;
            const status = this.querySelector('.status-select').value;
            const csrfToken = this.querySelector('[name=csrfmiddlewaretoken]').value;
            const submitButton = this.querySelector('button[type="submit"]');
            
            // Show loading state
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Updating...';
            
            // Send AJAX request
            fetch('/update_order_status/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    order_id: orderId,
                    status: status
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update the status badge in the table
                    const statusBadge = document.querySelector(`tr[data-order-id="${orderId}"] .badge`);
                    statusBadge.className = `badge ${getStatusClass(status)}`;
                    statusBadge.textContent = status;
                    
                    // Update the status badge in the modal
                    const modalStatusBadge = document.querySelector(`#orderModal${orderId} .badge`);
                    modalStatusBadge.className = `badge ${getStatusClass(status)}`;
                    modalStatusBadge.textContent = status;
                    
                    // Close the modal
                    const modal = bootstrap.Modal.getInstance(document.getElementById(`orderModal${orderId}`));
                    modal.hide();
                    
                    // Show success toast
                    showToast('Order status updated successfully');
                    // Reload the page after a short delay
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                } else {
                    showToast('Error updating order status', 'error');
                    // Reset button state
                    submitButton.disabled = false;
                    submitButton.innerHTML = 'Update Status';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('Error updating order status', 'error');
                // Reset button state
                submitButton.disabled = false;
                submitButton.innerHTML = 'Update Status';
            });
        });
    });
    
    // Helper function to get status badge class
    function getStatusClass(status) {
        switch(status) {
            case 'Pending': return 'bg-warning';
            case 'Confirmed': return 'bg-info';
            case 'Completed': return 'bg-success';
            case 'Cancelled': return 'bg-danger';
            default: return 'bg-secondary';
        }
    }
    
    // Helper function to show toast notifications
    function showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = 'toast-notification';
        toast.textContent = message;
        
        // Add toast styles
        toast.style.position = 'fixed';
        toast.style.bottom = '20px';
        toast.style.right = '20px';
        toast.style.backgroundColor = type === 'success' ? '#28a745' : '#dc3545';
        toast.style.color = 'white';
        toast.style.padding = '10px 20px';
        toast.style.borderRadius = '4px';
        toast.style.boxShadow = '0 4px 8px rgba(0,0,0,0.1)';
        toast.style.zIndex = '1000';
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s ease-in-out';
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.style.opacity = '1';
        }, 10);
        
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 300);
        }, 3000);
    }
});