// static/cart_utils.js

// Get current cart from localStorage
function getCart() {
    return JSON.parse(localStorage.getItem('cart')) || [];
}

// Save cart to localStorage
function saveCart(cart) {
    localStorage.setItem('cart', JSON.stringify(cart));
    window.dispatchEvent(new Event('cartUpdated'));
}

// Update cart count in header and offcanvas
function updateCartCount() {
    const cart = getCart();
    const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
    
    // Update header cart count
    const headerCount = document.getElementById('header-cart-count');
    if (headerCount) {
        headerCount.textContent = totalItems;
        headerCount.style.display = totalItems > 0 ? 'block' : 'none';
    }
    
    // Update offcanvas cart count
    const offcanvasCount = document.getElementById('offcanvas-cart-count');
    if (offcanvasCount) {
        offcanvasCount.textContent = totalItems;
        offcanvasCount.style.display = totalItems > 0 ? 'block' : 'none';
    }
}

// Listen for cart updates
window.addEventListener('cartUpdated', updateCartCount);
window.addEventListener('storage', (event) => {
    if (event.key === 'cart') {
        updateCartCount();
    }
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', updateCartCount);