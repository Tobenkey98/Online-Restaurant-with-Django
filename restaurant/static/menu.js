document.addEventListener('DOMContentLoaded', () => {
    // Display all menu items initially
    displayMenuItems('all');

    // Handle category button clicks
    document.querySelectorAll('#category-list button').forEach(button => {
        button.addEventListener('click', () => {
            document.querySelectorAll('#category-list button').forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            displayMenuItems(button.dataset.category);
        });
    });

    // Handle Add to Cart clicks
    document.getElementById('menu-items').addEventListener('click', (event) => {
        if (event.target.classList.contains('add-to-cart-btn')) {
            const itemId = parseInt(event.target.dataset.id);
            const menuItem = menuItems.find(item => item.id === itemId);
            if (menuItem && menuItem.available) {
                // Update cart in localStorage
                let cart = JSON.parse(localStorage.getItem('cart')) || [];
                const existingItem = cart.find(cartItem => cartItem.id === itemId);
                if (existingItem) {
                    existingItem.quantity += 1;
                } else {
                    cart.push({
                        id: menuItem.id,
                        name: menuItem.name,
                        price: menuItem.price,
                        quantity: 1,
                        image: menuItem.image
                    });
                }
                localStorage.setItem('cart', JSON.stringify(cart));

                // Update cart count and show toast
                updateCartCount();
                showToast(`${menuItem.name} successfully picked`);
            }
        }
    });

    // Sync cart count with Cart Page changes
    window.addEventListener('storage', (event) => {
        if (event.key === 'cart') {
            updateCartCount();
        }
    });

    // Set initial cart count
    updateCartCount();
});

// Update cart count badge
function updateCartCount() {
    const cart = JSON.parse(localStorage.getItem('cart')) || [];
    const cartCountElement = document.getElementById('header-cart-count');
    if (cartCountElement) {
        const totalItems = cart.length; // Count unique items
        cartCountElement.textContent = totalItems;
    }
}

// Show green toast notification
function showToast(message) {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = 'toast-notification';
    toast.textContent = message;
    
    // Add toast styles
    toast.style.position = 'fixed';
    toast.style.bottom = '20px';
    toast.style.right = '20px';
    toast.style.backgroundColor = '#28a745';
    toast.style.color = 'white';
    toast.style.padding = '10px 20px';
    toast.style.borderRadius = '4px';
    toast.style.boxShadow = '0 4px 8px rgba(0,0,0,0.1)';
    toast.style.zIndex = '1000';
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s ease-in-out';
    
    // Add to document
    document.body.appendChild(toast);
    
    // Show toast
    setTimeout(() => {
        toast.style.opacity = '1';
    }, 10);
    
    // Hide and remove toast after 3 seconds
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 3000);
}

// Display menu items by category
function displayMenuItems(category) {
    const menuItemsContainer = document.getElementById('menu-items');
    menuItemsContainer.innerHTML = '';
    const itemsToShow = category === 'all' ? menuItems : menuItems.filter(item => item.category === category);
    itemsToShow.forEach(item => {
        menuItemsContainer.appendChild(createMenuItemElement(item));
    });
}

// Create menu item HTML
function createMenuItemElement(item) {
    const colDiv = document.createElement('div');
    colDiv.className = 'col-md-6 col-lg-4';
    const cardDiv = document.createElement('div');
    cardDiv.className = 'card menu-item mb-3';
    cardDiv.innerHTML = `
        <div class="overflow-hidden image">
            <img src="${item.image}" class="card-img-top" alt="${item.name}" onerror="this.src='https://via.placeholder.com/300x200';">
        </div>
        <div class="card-body">
            <span class="category-pill">${capitalizeFirstLetter(item.category.replace('-', ' '))}</span>
            <h5 class="card-title">
                ${item.name}
                ${item.is_special ? '<span class="badge bg-warning ms-2">Special</span>' : ''}
            </h5>
            <p class="card-text">${item.description}</p>
            <div class="d-flex justify-content-between align-items-center">
                <span class="price">₦${item.price.toFixed(2)}</span>
                <button class="btn btn-warning text-light add-to-cart-btn" data-id="${item.id}" ${!item.available ? 'disabled' : ''}>
                    ${item.available ? 'Add to Cart' : 'Unavailable'}
                </button>
            </div>
        </div>
        ${item.available ? '' : '<span class="badge bg-danger availability-badge">Out of Stock</span>'}
    `;
    colDiv.appendChild(cardDiv);
    return colDiv;
}

// Capitalize category names
function capitalizeFirstLetter(string) {
    return string.split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
}