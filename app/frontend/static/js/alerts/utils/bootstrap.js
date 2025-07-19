// frontend/static/js/alerts/utils/bootstrap.js

/**
 * Bootstrap compatibility helper
 */
export const BootstrapHelper = {
    isAvailable() {
        return typeof bootstrap !== 'undefined' || typeof $ !== 'undefined';
    },
    
    showModal(modalElement) {
        if (typeof bootstrap !== 'undefined') {
            // Bootstrap 5
            const modal = new bootstrap.Modal(modalElement);
            modal.show();
            return modal;
        } else if (typeof $ !== 'undefined' && $.fn.modal) {
            // Bootstrap 4 with jQuery
            $(modalElement).modal('show');
            return {
                hide: function() { $(modalElement).modal('hide'); }
            };
        } else {
            // Fallback: simple show/hide
            modalElement.style.display = 'block';
            modalElement.classList.add('show');
            document.body.classList.add('modal-open');
            
            // Add backdrop
            const backdrop = document.createElement('div');
            backdrop.className = 'modal-backdrop fade show';
            backdrop.id = 'fallback-backdrop';
            document.body.appendChild(backdrop);
            
            return {
                hide: function() {
                    modalElement.style.display = 'none';
                    modalElement.classList.remove('show');
                    document.body.classList.remove('modal-open');
                    const backdrop = document.getElementById('fallback-backdrop');
                    if (backdrop) backdrop.remove();
                }
            };
        }
    },
    
    hideModal(modalElement) {
        if (typeof bootstrap !== 'undefined') {
            const modal = bootstrap.Modal.getInstance(modalElement);
            if (modal) modal.hide();
        } else if (typeof $ !== 'undefined' && $.fn.modal) {
            $(modalElement).modal('hide');
        } else {
            // Fallback
            modalElement.style.display = 'none';
            modalElement.classList.remove('show');
            document.body.classList.remove('modal-open');
            const backdrop = document.getElementById('fallback-backdrop');
            if (backdrop) backdrop.remove();
        }
    },
    
    showToast(toastElement, options = {}) {
        if (typeof bootstrap !== 'undefined') {
            const toast = new bootstrap.Toast(toastElement, options);
            toast.show();
            return toast;
        } else {
            // Fallback: simple show with timeout
            toastElement.style.display = 'block';
            toastElement.classList.add('show');
            
            setTimeout(() => {
                toastElement.style.display = 'none';
                toastElement.classList.remove('show');
                toastElement.remove();
            }, options.delay || 5000);
            
            return {
                hide: function() {
                    toastElement.style.display = 'none';
                    toastElement.classList.remove('show');
                    toastElement.remove();
                }
            };
        }
    }
};