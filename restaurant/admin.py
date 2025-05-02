from django.contrib import admin
from .models import UserProfile,  Category, MenuItem, Order

# Register your models here.
admin.site.register(UserProfile)
admin.site.register(Order)
admin.site.register(Category)
admin.site.register(MenuItem)