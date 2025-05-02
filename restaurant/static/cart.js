document.addEventListener('DOMContentLoaded', function() {
    updateHeaderCartCount(); // Initialize header count on page load
    updateCart(); // Your existing cart update

    // Cross-tab cart sync
    window.addEventListener('storage', function(e) {
        if (e.key === 'cart') {
            updateHeaderCartCount();
            updateCart();
        }
    });

    // Paystack Checkout Handler (unchanged)
    document.getElementById('checkout-link').addEventListener('click', async function(e) {
        e.preventDefault();
        if (this.classList.contains('disabled')) return;
    
        const cart = JSON.parse(localStorage.getItem('cart')) || [];
        if (cart.length === 0) return;
    
        // UI Loading State
        const checkoutBtn = this;
        checkoutBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Processing...';
        checkoutBtn.classList.add('disabled');
    
        try {
            // Generate unique reference
            const reference = 'PYT_' + Date.now() + '_' + Math.floor(Math.random() * 1000);
            
            // Prepare payment data
            const paymentData = {
                email: document.getElementById('user-email').value,
                amount: cart.reduce((sum, item) => sum + (item.price * item.quantity), 0),
                reference: reference,
                cart: cart
            };
    
            // Send AJAX request to Django
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
                throw new Error(data.message || 'Payment failed');
            }
    
            // Redirect to Paystack if successful
            if (data.redirect_url) {
                window.location.href = data.redirect_url;
            } else {
                throw new Error('No redirect URL received');
            }
    
        } catch (error) {
            console.error('Payment Error:', error);
            alert('Error: ' + error.message);
            checkoutBtn.innerHTML = 'Checkout';
            checkoutBtn.classList.remove('disabled');
        }
    });
});

// NEW FUNCTION: Handles ONLY the header cart count updates
function updateHeaderCartCount() {
    const cart = JSON.parse(localStorage.getItem('cart')) || [];
    const totalItems = cart.reduce((sum, item) => sum + (item.quantity || 0), 0);
    const headerCount = document.getElementById('header-cart-count');
    
    if (headerCount) {
        headerCount.textContent = totalItems;
        headerCount.style.display = totalItems > 0 ? 'block' : 'none';
    }
}

// MODIFIED Cart Management Functions
function updateCart() {
    const cart = JSON.parse(localStorage.getItem('cart')) || [];
    const validCart = cart.filter(item => item.id && item.quantity > 0);
    localStorage.setItem('cart', JSON.stringify(validCart));

    // Render cart items
    document.getElementById('cart-items').innerHTML = validCart.map((item, index) => `
        <tr>
            <td><img src="${item.image || 'https://via.placeholder.com/50'}" width="50"></td>
            <td>${item.name}</td>
            <td>₦${item.price.toFixed(2)}</td>
            <td>
                <div class="quantity-controls">
                    <button class="btn btn-sm btn-secondary" onclick="changeQuantity(${index}, -1)">–</button>
                    <span>${item.quantity}</span>
                    <button class="btn btn-sm btn-secondary" onclick="changeQuantity(${index}, 1)">+</button>
                </div>
            </td>
            <td>₦${(item.price * item.quantity).toFixed(2)}</td>
            <td><button class="btn btn-sm btn-danger" onclick="removeItem(${index})">Remove</button></td>
        </tr>
    `).join('');

    // Update totals
    const grandTotal = validCart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    document.getElementById('grand-total').textContent = `₦${grandTotal.toFixed(2)}`;
    document.getElementById('checkout-link').classList.toggle('disabled', validCart.length === 0);
    
    // Ensure header count is updated
    updateHeaderCartCount();
}

// MODIFIED Quantity Functions
function changeQuantity(index, delta) {
    const cart = JSON.parse(localStorage.getItem('cart')) || [];
    if (cart[index]) {
        cart[index].quantity += delta;
        if (cart[index].quantity <= 0) cart.splice(index, 1);
        localStorage.setItem('cart', JSON.stringify(cart));
        updateCart(); // Updates both cart and header count
    }
}

function removeItem(index) {
    const cart = JSON.parse(localStorage.getItem('cart')) || [];
    cart.splice(index, 1);
    localStorage.setItem('cart', JSON.stringify(cart));
    updateCart(); // Updates both cart and header count
}

// CSRF Token Helper (unchanged)
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

const paymentData = {
    email: document.getElementById('user-email').value,
    amount: cart.reduce((sum, item) => sum + (item.price * item.quantity), 0),
    reference: 'PYT_' + Date.now() + '_' + Math.floor(Math.random() * 1000),
    cart: JSON.parse(localStorage.getItem('cart')) || []
};