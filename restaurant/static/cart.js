// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the payment success page
    if (window.location.pathname.includes('payment/success')) {
        // Clear cart from localStorage
        localStorage.removeItem('cart');
        updateHeaderCartCount(0);
    } else {
        // Set initial header count (number of distinct items)
        const initialCart = JSON.parse(localStorage.getItem('cart')) || [];
        updateHeaderCartCount(initialCart.length);
    }
    
    // Initialize cart display
    updateCart();

    // Handle cross-tab synchronization
    window.addEventListener('storage', function(e) {
        if (e.key === 'cart') {
            const cart = JSON.parse(e.newValue) || [];
            updateHeaderCartCount(cart.length);
            updateCart();
        }
    });

    // Setup Paystack checkout
    setupPaystackCheckout();
});

// Update header cart count (number of distinct items only)
function updateHeaderCartCount(itemCount) {
    const headerCount = document.getElementById('header-cart-count');
    if (headerCount) {
        headerCount.textContent = itemCount;
        headerCount.style.display = itemCount > 0 ? 'block' : 'none';
    }
}

// Update cart display and totals
function updateCart() {
    const cart = JSON.parse(localStorage.getItem('cart')) || [];
    const validCart = cart.filter(item => item.id && item.quantity > 0);
    
    // Save filtered cart
    localStorage.setItem('cart', JSON.stringify(validCart));

    // Render cart items
    document.getElementById('cart-items').innerHTML = validCart.map((item, index) => `
        <tr>
            <td><img src="${item.image || 'https://via.placeholder.com/50'}" width="50"></td>
            <td>${item.name}</td>
            <td>₦${item.price.toFixed(2)}</td>
            <td>
                <div class="quantity-controls">
                    <button class="btn btn-sm btn-secondary" onclick="adjustQuantity(${index}, -1)"
                    ${item.quantity <= 1 ? 'disabled' : ''}>–</button>

                    <span>${item.quantity}</span>
                    <button class="btn btn-sm btn-secondary" onclick="adjustQuantity(${index}, 1)">+</button>
                </div>
            </td>
            <td>₦${(item.price * item.quantity).toFixed(2)}</td>
            <td><button class="btn btn-sm btn-danger" onclick="removeItem(${index})">Remove</button></td>
        </tr>
    `).join('');

    // Update totals
    updateCartTotals(validCart);
}

// Update cart totals and checkout button state
function updateCartTotals(cart) {
    const grandTotal = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    document.getElementById('grand-total').textContent = `₦${grandTotal.toFixed(2)}`;
    document.getElementById('checkout-link').classList.toggle('disabled', cart.length === 0);
}

// Adjust quantity without affecting header count
function adjustQuantity(index, delta) {
    const cart = JSON.parse(localStorage.getItem('cart')) || [];
//    return console.log(cart)
    if (cart[index]) {
        cart[index].quantity += delta;
        
        // Remove item if quantity reaches 0
        if (cart[index].quantity <= 0) {
            cart.splice(index, 1);
            updateHeaderCartCount(cart.length); // Only update count when item is removed
        }
        
        localStorage.setItem('cart', JSON.stringify(cart));
        updateCart();
    }
}

// Remove item completely
function removeItem(index) {
    const cart = JSON.parse(localStorage.getItem('cart')) || [];
    cart.splice(index, 1);
    localStorage.setItem('cart', JSON.stringify(cart));
    updateHeaderCartCount(cart.length); // Update header count
    updateCart();
}

// Paystack Checkout Integration
function setupPaystackCheckout() {
    document.getElementById('checkout-link').addEventListener('click', async function(e) {
        e.preventDefault();
        const checkoutBtn = this;
        
        // Validate cart
        const cart = JSON.parse(localStorage.getItem('cart')) || [];
        if (cart.length === 0 || checkoutBtn.classList.contains('disabled')) {
            return;
        }

        // Set loading state
        checkoutBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Processing...';
        checkoutBtn.classList.add('disabled');

        try {
            // Prepare payment data
            const paymentData = {
                email: document.getElementById('user-email').value,
                amount: cart.reduce((sum, item) => sum + (item.price * item.quantity), 0) * 100, // Convert to kobo
                reference: 'PYT_' + Date.now() + '_' + Math.floor(Math.random() * 1000),
                cart: cart
            };

            // Initiate payment
            const response = await initiatePayment(paymentData);
            
            if (response.redirect_url) {
                // Clear cart from localStorage before redirecting
                localStorage.removeItem('cart');
                updateHeaderCartCount(0);
                window.location.href = response.redirect_url;
            } else {
                throw new Error('No redirect URL received');
            }
        } catch (error) {
            console.error('Payment Error:', error);
            alert('Payment Error: ' + error.message);
            checkoutBtn.innerHTML = 'Checkout';
            checkoutBtn.classList.remove('disabled');
        }
    });
}

// Make payment request to backend
async function initiatePayment(paymentData) {
    const response = await fetch('/initiate_payment/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(paymentData)
    });

    const data = await response.json();
    if (!response.ok || !data.success) {
        throw new Error(data.message || 'Payment initiation failed');
    }
    return data;
}

// Helper function to get CSRF token
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}