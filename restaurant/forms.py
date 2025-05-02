from django import forms
from .models import UserProfile, Order, MenuItem
from django.contrib.auth.models import User




class SignupForm(forms.ModelForm):
    name = forms.CharField(max_length=100, required=True, label="Full Name")
    password = forms.CharField(widget=forms.PasswordInput, required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Split full name into first & last name
        full_name = self.cleaned_data.get("get_name")
        name_parts = full_name.split(" ", 1)
        user.first_name = name_parts[0]
        user.last_name = name_parts[1] if len(name_parts) > 1 else ""
        
        user.set_password(self.cleaned_data["get_password"])  # Hash password
        
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['name', 'phone', 'address',  'location', 'profile_image']



class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ['name', 'Category', 'price', 'description', 'image', 'available', 'is_special']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'available': forms.CheckboxInput(),
            'is_special': forms.CheckboxInput(),
        }
        labels = {
            'Category': 'Category',
        }