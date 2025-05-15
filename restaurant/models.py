from django.db import models
from django.contrib.auth.models import User, auth
from django.contrib.auth.hashers import make_password, check_password  # Import check_password
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.
class UserInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE) # Links to django User Model
    name = models.CharField(max_length=500, null=True, blank=True)
    is_superuser = models.CharField(max_length=500, null=True, blank=True)
    is_staff = models.CharField(max_length=500, null=True, blank=True)
    email = models.EmailField(max_length=500, null=True, blank=True)
    phone = models.CharField(max_length=500, null=True, blank=True)
    gender = models.CharField(max_length=500, null=True, blank=True)
    username = models.CharField(max_length=500, null=True, blank=True)
    password = models.CharField(max_length=500, null=True, blank=True)  # Add password field
    dob =  models.DateField(null=True, blank=True)
    status = models.CharField(max_length=500, null=True, blank=True)
    payments = models.IntegerField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        # If password is provided and not already hashed, hash it
        if self.password and not self.password.startswith('pbkdf2_sha256$'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def set_password(self, raw_password):
        """Hash and set the password."""
        self.password = make_password(raw_password)
        self.save()

    def check_password(self, raw_password):
        """Check if the provided password matches the stored hash."""
        return check_password(raw_password, self.password)

    class Meta:
        managed = True
        db_table = 'userinfo'


class Admin(models.Model):
    full_name = models.CharField(max_length=500, null=True, blank=True)  # Full name of the admin
    username = models.CharField(max_length=500, unique=True, null=True, blank=True)
    email = models.EmailField(max_length=500, null=True, blank=True)  # Email address
    password = models.CharField(max_length=225, null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_image = models.ImageField(upload_to='admin_profiles/', blank=True, null=True)
    is_superuser = models.BooleanField(max_length=500, null=True, blank=True, default=False)  # Superuser status
    is_staff = models.BooleanField(max_length=500, null=True, blank=True, default=True)  # Staff status
    

    def set_password(self, raw_password):
        """Hash and set the password."""
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        """Check if the provided password matches the stored hash."""
        return check_password(raw_password, self.password)

    def __str__(self):
        return f'{self.user.username} Admin Profile'  # Display username in admin panel

    class Meta:
        managed = True
        db_table = 'admin'




class Category(models.Model):
    name = models.CharField(
        max_length=50,
        choices=[
            ('Appetizers', 'Appetizers'),
            ('Desserts', 'Desserts'),
            ('Main Course', 'Main Course'),
            ('Beverages', 'Beverages'),
        ],
        unique=True
    )

    def __str__(self):
        return self.name

    class Meta:
            managed = True
            db_table = 'category'


class MenuItem(models.Model):
    id = models.AutoField(primary_key=True) # Adding an id field
    Category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="items", default=1)
    name = models.CharField(max_length=500, unique=True)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='menu_images/', blank=True, null=True)
    available = models.BooleanField(default=True)
    is_special = models.BooleanField(default=False)  # For special items
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    @property
    def order_count(self):
        return OrderItem.objects.filter(menu_item=self).count()
    
    class Meta:
        managed = True
        db_table = 'menuitem'

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=500, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)

    def __str__(self):
        return f'{self.user.username} UserProfile' # Show username in admin panel


    
    class Meta:
        managed= True
        db_table = 'userprofile'

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_id = models.CharField(max_length=10, unique=True, editable=False, blank=True)
    product_name = models.CharField(max_length=500, blank=True, null=True)
    order_date = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=50, choices=[
        ('Completed', 'Completed'),
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Cancelled', 'Cancelled'),
    ], default='pending')
   
    menu_items = models.ManyToManyField(MenuItem, related_name='orders')

    @property
    def status_class(self):
        return {
            'Completed': 'success',
            'Pending': 'warning',
            'Confirmed': 'info',
            'Cancelled': 'danger',
        }.get(self.status, 'secondary')

    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = self.generate_order_id()
        super().save(*args, **kwargs)
    
    def generate_order_id(self):
        last_order = Order.objects.order_by('-order_date').first()
        if last_order and last_order.order_id.startswith('ORD-'):
            last_number = int(last_order.order_id.split('-')[1])
            new_number = last_number + 1
        else:
            new_number = 1
        return f"ORD-{new_number:04d}"

    def __str__(self):
        return self.order_id
    
    class Meta:
        managed = True
        db_table = 'Order'
#t332f4ib

class OrderItem(models.Model):
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.menu_item.name} in Order #{self.order.id}"

    class Meta:
        managed =True
        db_table = 'Order Item'
        


class RestaurantSettings(models.Model):
    name = models.CharField(max_length=255, default="My Restaurant")
    logo = models.ImageField(upload_to='restaurant_logos/', blank=True, null=True)
    contact_email = models.EmailField(max_length=254, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    default_order_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('confirmed', 'Confirmed'),
        ],
        default='pending'
    )
    currency_symbol = models.CharField(max_length=5, default='₦')
    enable_notifications = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        managed =True
        db_table = 'Restaurant Settings'


class Payment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=100, unique=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('successful', 'Successful'),
            ('failed', 'Failed'),
            ('cancelled', 'Cancelled'),
        ],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment for Order #{self.order.id} - {self.status}"
    
    class Meta:
        managed =True
        db_table = 'Payment'


class Notification(models.Model):
    admin = models.ForeignKey('Admin', on_delete=models.CASCADE)
    order = models.ForeignKey('Order', on_delete=models.CASCADE, null=True, blank=True)  # Link to order
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    notification_type = models.CharField(max_length=20, choices=[
        ('new_order', 'New Order'),
        ('status_update', 'Status Update'),
    ], default='new_order')

    def __str__(self):
        return f"{self.get_notification_type_display()}: {self.message}"
    
    class Meta:
        managed = True
        db_table = 'Notification'
        ordering = ['-created_at']
    

class PasswordReset(models.Model):
    reset_id = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    class Meta:
        managed = True
        db_table = 'password_reset'
    
