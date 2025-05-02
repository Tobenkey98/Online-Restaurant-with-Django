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
  
  // Update cart count in header
  function updateCartCount() {
    const cart = getCart();
    const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
    const cartCountElement = document.getElementById('header-cart-count');
    
    if (cartCountElement) {
      cartCountElement.textContent = totalItems;
      cartCountElement.style.display = totalItems > 0 ? 'block' : 'none';
    }
  }
  
  // Listen for cart updates
  window.addEventListener('cartUpdated', updateCartCount);
  
  // Initialize on page load
  document.addEventListener('DOMContentLoaded', updateCartCount);