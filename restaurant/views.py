from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login
from datetime import datetime, date
time_package = datetime.now()
from .models import UserInfo, UserProfile, Order, MenuItem
from dateutil.parser import parse
from django.contrib.auth.models import User, auth
from .models import Admin, MenuItem, Category, Payment,RestaurantSettings, Notification, OrderItem, Order
from django.db.models import Count, Sum
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import pytz
from .forms import UserProfileForm, MenuItemForm
from django.views.decorators.csrf import csrf_protect, csrf_exempt
import uuid
import json
from django.http import HttpResponse, JsonResponse 
import requests
from django.core.mail import send_mail
from django.conf import settings
from restaurant.utils.paystack import PaystackAPI
from django.urls import reverse
import logging
logger = logging.getLogger(__name__)



# Time format 
nigeria_time = datetime.now(pytz.timezone("Africa/Lagos"))

from restaurant.models import *

from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Sum

 #API Modules
# from rest_framework.views import APIView
# from rest_framework.response import Response
#from .serializers import UserInfoSerializer




def welcome_page(request):
    return render(request, 'welcome.html')

def login_page(request):
    if request.method == 'POST':
        # Check if it's a sign-in attempt (sign-in form has only username and password)
        if 'get_name' not in request.POST:
            get_username = request.POST.get('get_username')
            get_password = request.POST.get('get_password')
            remember_me = request.POST.get('check')

            if not all([ get_username,  get_password,]):
                messages.info(request, 'All fields are required')
                return redirect('/login/')
            
            user = auth.authenticate(request, username=get_username, password=get_password)
            if user is not None:
                auth.login(request, user)

                # If remember is not checked, set session to expire when browser closes
                if not remember_me:
                    request.session.set_expiry(0)
                else:
                    # Keep the user logged in for 3 Days
                    request.session.set_expiry(259200)  # 3 days in seconds (3 * 24 * 60 *60)
                    
                
                return redirect('/home')  # Redirect to profile page after login
            else:
                messages.info(request, 'Invalid username or password')
                return redirect('/login')  # Ensure correct redirection
        
        # Handle sign-up
        else:
            get_name = request.POST.get('get_name')
            get_username = request.POST.get('get_username')
            get_email = request.POST.get('get_email')
            get_password = request.POST.get('get_password')
            confirm_password = request.POST.get('confirm_password')


            # Check all fields are filled
            if not all([get_name, get_username, get_email, get_password, confirm_password]):
                messages.info(request, 'All fields are required')
                return redirect('/login/')

            if get_password != confirm_password:
                messages.info(request, 'Passwords do not match')
                return redirect('/login/')

            if User.objects.filter(username=get_username).exists():
                messages.info(request, 'Username already exists')
                return redirect('/login/')  

            if User.objects.filter(email=get_email).exists():
                messages.info(request, 'Email already exists')
                return redirect('/login/')

            # Create user
            user = User.objects.create_user(
                first_name=get_name,
                username=get_username,  # Django's default User model does not have 'name' field
                email=get_email,
                password=get_password,
                is_superuser=0
            )
            user.save()

            # Create 0r Update UserProfile
            user_profile, created = UserProfile.objects.get_or_create(user=user)
            user_profile.name = get_name # Store the full name in UserProfile
            user_profile.save()

            # Create UserInfo (to avoid DoesNotExist later)
            user_info, created = UserInfo.objects.get_or_create(user=user)
            if created:
                user_info.name = get_name  # Optional: populate name
                user_info.save()

            # Log the user in after registration
            auth.login(request, user)
            messages.info(request, f"{get_username}, your account has been created successfully")
            return redirect('/login/')  # Redirect to profile page

    return render(request, 'login.html')


@login_required(login_url='/login')
def homepage(request):
    notifications = request.session.get('notifications', [])
    menu_items = MenuItem.objects.filter(available=True).order_by('name')
    return render(request, 'home_page.html', {
        'notifications': notifications,
        'menu_items': menu_items,
    })


@login_required(login_url='/login')
def contact_us_page(request):
    return render(request, 'contact_us.html')




def logout_page(request):
    auth.logout(request)
    return redirect('/login')


@login_required(login_url='/login')
def user_account_page(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    try:
        user_info = UserInfo.objects.get(user=request.user)
    except UserInfo.DoesNotExist:
        user_info = UserInfo.objects.create(user=request.user, name=request.user.username)

    orders = Order.objects.filter(user=request.user).order_by('-order_date')

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            user_info.name = request.POST.get('name', user_info.name)
            user_info.save()
            messages.info(request, "Profile updated successfully")
            return redirect('user_account')
    else:
        form = UserProfileForm(instance=user_profile)

    notifications = request.session.get('notifications', [])

    return render(request, 'user_account.html', {
        'form': form,
        'orders': orders,
        'user_profile': user_profile,
        'user_info': user_info,
        'notifications': notifications,
        'user': request.user,
    })






def admin_auth(request):
# Get the tab parameter from the URL (default to 'login')
    active_tab = request.GET.get('tab', 'login')
    if request.method == 'POST':
        # Determine which form was submitted
        if 'login_submit' in request.POST:
            # Handle Login
            get_username = request.POST.get('get_username')
            get_password = request.POST.get('get_password')
            remember_me = request.POST.get('rememberMe')


            try:
                admin = Admin.objects.get(username=get_username)
                if admin.check_password(get_password):
                    # Log the admin in using Django's session
                    request.session['admin_id'] = admin.id
                    if not remember_me:
                        request.session.set_expiry(0)  # Session expires when browser closes
                    return redirect('/adminsuper122')
                else:
                    messages.error(request, "Invalid password.")
            except Admin.DoesNotExist:
                messages.error(request, "Invalid username.")
            active_tab = 'login'

        elif 'register_submit' in request.POST:
            get_name = request.POST.get('get_name')
            get_username = request.POST.get('get_username')
            get_email = request.POST.get('get_email')
            get_password = request.POST.get('get_password')
            confirm_password = request.POST.get('confirm_password')

            if get_password != confirm_password:
                messages.error(request, "Passwords don't match.")
                active_tab = 'register'
            elif Admin.objects.filter(username=get_username).exists():
                messages.error(request, "Username already exists.")
                active_tab = 'register'
            elif Admin.objects.filter(email=get_email).exists():
                messages.error(request, "Email already exists.")
                active_tab = 'register'
            else:
                admin = Admin.objects.create(
                    full_name=get_name,
                    username=get_username,
                    email=get_email,
                    is_superuser=True,
                    is_staff=True
                )
                admin.set_password(get_password)
                admin.save()
                messages.success(request, "Registration successful. Please log in.")
                active_tab = 'login'

        return render(request, 'admin_login.html', {'active_tab': active_tab})

    return render(request, 'admin_login.html', {'active_tab': active_tab})
                
@csrf_protect
def adminsuper122(request):
    # Check if admin is logged in
    if 'admin_id' not in request.session:
        return redirect('admin_auth')
    try:
        admin = Admin.objects.get(id=request.session['admin_id'])
    except Admin.DoesNotExist:
        del request.session['admin_id']
        return redirect('admin_auth')

    # Get or create restaurant settings
    settings, created = RestaurantSettings.objects.get_or_create(id=1)  # Single instance for now

    # Handle tab selection
    tab = request.POST.get('tab', request.GET.get('tab', 'dashboard'))

    if request.method == 'POST':
        if tab == 'notifications' and request.POST.get('action') == 'mark_read':
            Notification.objects.filter(admin=admin, is_read=False).update(is_read=True)
            messages.success(request, "All notifications marked as read.")
            return redirect(f"{request.path}?tab=notifications")
    # Handle POST actions
    if request.method == 'POST':
        if tab == 'profile':
            # Update admin profile
            admin.full_name = request.POST.get('full_name', admin.full_name)
            admin.phone = request.POST.get('phone', admin.phone)
            admin.address = request.POST.get('address', admin.address)
            if request.FILES.get('profile_image'):
                admin.profile_image = request.FILES['profile_image']
            admin.save()
            messages.success(request, "Profile updated successfully!")
            return redirect(f"{request.path}?tab=profile")

        elif tab == 'menu':
            action = request.POST.get('action')
            item_id = request.POST.get('item_id')
            status_filter = request.GET.get('status', 'all')
            search_filter = request.GET.get('search', '')
            category_filter = request.GET.get('category', '')

            menu_items = MenuItem.objects.all().order_by('name')
            if status_filter != 'all':
                menu_items = menu_items.filter(available=(status_filter == 'available'))
            if search_filter:
                menu_items = menu_items.filter(name__icontains=search_filter)
            if category_filter:
                menu_items = menu_items.filter(Category__name=category_filter)

            if action == 'delete' and item_id:
                try:
                    MenuItem.objects.get(id=item_id).delete()
                    messages.success(request, "Item deleted successfully!")
                except MenuItem.DoesNotExist:
                    messages.error(request, "Item not found!")

            elif action == 'edit' and item_id:
                try:
                    item = MenuItem.objects.get(id=item_id)
                    description = request.POST.get('description', item.description)
                    price = request.POST.get('price', item.price)
                    item.description = description
                    item.price = float(price) if price else item.price
                    item.save()
                    messages.success(request, f"Updated '{item.name}' successfully!")
                except MenuItem.DoesNotExist:
                    messages.error(request, "Item not found!")
                except ValueError:
                    messages.error(request, "Invalid price!")

            elif action == 'add':
                name = request.POST.get('name')
                category_name = request.POST.get('category')
                price = request.POST.get('price')
                description = request.POST.get('description', '')
                available = 'available' in request.POST
                is_special = 'is_special' in request.POST
                image = request.FILES.get('image')

                if name and category_name and price:
                    try:
                        category, _ = Category.objects.get_or_create(name=category_name)
                        MenuItem.objects.create(
                            name=name,
                            Category=category,
                            price=float(price),
                            description=description,
                            available=available,
                            is_special=is_special,
                            image=image
                        )
                        messages.success(request, f"Added '{name}' successfully!")
                    except Category.DoesNotExist:
                        messages.error(request, "Category not found!")
                    except Exception as e:
                        messages.error(request, f"Error: {e}")
                else:
                    messages.error(request, "Please fill Name, Category, and Price!")

        elif tab == 'orders':
            order_id = request.POST.get('order_id')
            status = request.POST.get('status')
            # Match the exact status choices from your Order model
            if order_id and status in ['Pending', 'Confirmed', 'Completed', 'Cancelled']:
                try:
                    order = Order.objects.get(id=order_id)
                    order.status = status
                    order.save()
                    
                    messages.success(request, f"Order #{order_id} updated to {status}!")
            
            # Send notification to user
                    if status in ['Confirmed', 'Completed', 'Cancelled']:
                        request.session.setdefault('notifications', [])
                        request.session['notifications'].append({
                            'user_id': order.user_id,
                            'message': f"Your order #{order_id} has been {status}."
                        })
                        request.session.modified = True
                
                # Optional: Send email notification
                        if order.user.email:
                            from django.core.mail import send_mail
                            send_mail(
                            f'Order #{order_id} Update',
                            f'Your order status has been updated to {status}.',
                            settings.DEFAULT_FROM_EMAIL,
                            [order.user.email],
                            fail_silently=True,
                        )
                    
                except Order.DoesNotExist:
                    messages.error(request, "Order not found!")

        elif tab == 'settings':
            # Update restaurant settings
            settings.name = request.POST.get('name', settings.name)
            settings.contact_email = request.POST.get('contact_email', settings.contact_email)
            settings.phone_number = request.POST.get('phone_number', settings.phone_number)
            settings.address = request.POST.get('address', settings.address)
            settings.default_order_status = request.POST.get('default_order_status', settings.default_order_status)
            settings.currency_symbol = request.POST.get('currency_symbol', settings.currency_symbol)
            settings.enable_notifications = 'enable_notifications' in request.POST
            if request.FILES.get('logo'):
                settings.logo = request.FILES['logo']
            settings.save()
            messages.success(request, "Settings updated successfully!")
            return redirect(f"{request.path}?tab=settings")

    # Fetch all data
    total_orders = Order.objects.count()
    total_revenue = Order.objects.aggregate(total=Sum('total_price'))['total'] or 0
    total_customers = Order.objects.values('user_id').distinct().count()
    total_menu_items = MenuItem.objects.count()
    recent_orders = Order.objects.order_by('-order_date')[:5]
    popular_items = MenuItem.objects.annotate(num_orders=Count('orderitem')).order_by('-num_orders')[:4]
    notification_count = Order.objects.filter(status='pending').count()
    menu_items = list(MenuItem.objects.all().order_by('name'))
    categories = Category.objects.all()
    orders = list(Order.objects.all().order_by('-order_date'))
    notifications = request.session.get('notifications', [])
    payments = Payment.objects.all().order_by('-created_at')[:10]

    # Fetch user data for Users tab
    users = User.objects.select_related('userprofile').all()
    user_data = []
    for user in users:
        order_count = Order.objects.filter(user=user).count()
        profile = user.userprofile if hasattr(user, 'userprofile') else None
        user_data.append({
            'username': user.username,
            'email': user.email,
            'address': profile.address if profile else 'No address',
            'phone': profile.phone if profile else 'No phone',
            'profile_picture': profile.profile_image.url if profile and profile.profile_image else 'https://via.placeholder.com/50',
            'order_count': order_count,
        })
    

    return render(request, 'adminsuper122.html', {
        'active_tab': tab,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_customers': total_customers,
        'total_menu_items': total_menu_items,
        'recent_orders': recent_orders,
        'popular_items': popular_items,
        'notification_count': notification_count,
        'menu_items': menu_items,
        'categories': categories,
        'orders': orders,
        'notifications': notifications,
        'user': admin,
        'user_data': user_data,
        'settings': settings,  # Pass settings to template
        'payments': payments,
    })

def admin_logout(request):
    if 'admin_id' in request.session:
        del request.session['admin_id']
    return redirect('admin_auth')








@login_required(login_url='/login')
def menu_page(request):
    menu_items = MenuItem.objects.filter(available=True).order_by('name')
    categories = Category.objects.all()
    return render(request, 'menu.html', {
        'menu_items': menu_items,
        'categories': categories,
    })

def cart_page(request):
    return render(request, 'cart.html', {})




def initiate_payment(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user = request.user if request.user.is_authenticated else None
            cart_items = data['cart']
            
            # Prepare payment data without creating order yet
            payment_data = {
                'email': data['email'],
                'amount': sum(item['price'] * item['quantity'] for item in cart_items),
                'reference': data['reference'],
                'cart': cart_items,
                'user_id': user.id if user else None,
                'product_names': ", ".join([item['name'] for item in cart_items]),
                'total_quantity': sum(item['quantity'] for item in cart_items)
            }
            
            # Store temporary payment data in session
            request.session['pending_payment'] = payment_data
            request.session.modified = True
            
            # Initialize Paystack payment
            paystack = PaystackAPI()
            response = paystack.initialize_payment(
                email=payment_data['email'],
                amount=payment_data['amount'],
                reference=payment_data['reference'],
                callback_url=f"{settings.BASE_URL}/payment/verify/"
            )
            
            if response.get('status'):
                return JsonResponse({
                    'success': True,
                    'redirect_url': response['data']['authorization_url']
                })
            
            return JsonResponse({'error': 'Payment initialization failed'}, status=400)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)



def verify_payment(request, reference):
    try:
        payment = Payment.objects.get(reference=reference)
        
        # Skip if already verified
        if payment.status == 'verified':
            messages.info(request, f"Payment {reference} was already verified")
            return redirect('adminsuper122')
            
        # Verify with Paystack API (works in test mode)
        headers = {"Authorization": f"Bearer {settings.PAYSTACK_TEST_SECRET_KEY}"}  # Use test key
        response = requests.get(
            f"https://api.paystack.co/transaction/verify/{reference}",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data['status'] and data['data']['status'] == 'success':
                # Update payment record
                payment.status = 'verified'
                payment.amount = float(data['data']['amount'])/100  # Convert from kobo
                payment.gateway_response = data['data']['gateway_response']
                payment.verified_by = request.user if request.user.is_authenticated else None
                payment.verified_at = datetime.now()
                payment.save()
                
                # Update related order - SET TO PENDING
                if hasattr(payment, 'order'):
                    payment.order.payment_verified = True
                    payment.order.status = 'Pending'  # Changed to Pending for admin approval
                    payment.order.save()
                    
                    # Send admin notification
                    request.session.setdefault('admin_notifications', [])
                    request.session['admin_notifications'].append({
                        'order_id': payment.order.id,
                        'message': f"New order #{payment.order.id} requires approval"
                    })
                    request.session.modified = True
                
                messages.success(request, f"Payment {reference} verified successfully! Order is pending approval.")
            else:
                payment.status = 'failed'
                payment.gateway_response = data['data']['gateway_response']
                payment.save()
                messages.error(request, f"Payment failed: {data['data']['gateway_response']}")
        else:
            payment.status = 'failed'
            payment.save()
            messages.error(request, "Could not verify payment with Paystack")
            
    except Payment.DoesNotExist:
        messages.error(request, "Payment not found!")
    except Exception as e:
        messages.error(request, f"Error verifying payment: {str(e)}")
    
    return redirect('adminsuper122')

def payment_success(request):
    """Display success page for verified payments"""
    reference = request.GET.get('reference')
    try:
        payment = Payment.objects.get(reference=reference, status='success')
        return render(request, 'payment_success.html', {'payment': payment})
    except Payment.DoesNotExist:
        return redirect(reverse('payment_failed'))

def payment_failed(request):
    """Display failed payment page"""
    reference = request.GET.get('reference')
    context = {'payment': None}
    if reference:
        context['payment'] = Payment.objects.filter(reference=reference).first()
    return render(request, 'payment_failed.html', context)
    

def payment_verification_callback(request):
    """Paystack callback handler (for test mode)"""
    reference = request.GET.get('reference')
    
    if not reference:
        return redirect(reverse('payment_failed'))

    try:
        # Use test secret key
        headers = {"Authorization": f"Bearer {settings.PAYSTACK_TEST_SECRET_KEY}"}
        response = requests.get(
            f"https://api.paystack.co/transaction/verify/{reference}",
            headers=headers
        )
        response.raise_for_status()
        data = response.json()

        if data['status'] and data['data']['status'] == 'success':
            try:
                payment = Payment.objects.get(reference=reference)
                payment.status = 'verified'
                payment.amount = float(data['data']['amount'])/100
                payment.save()

                # Update order - set to Pending
                if hasattr(payment, 'order'):
                    payment.order.payment_status = 'completed'
                    payment.order.status = 'Pending'  # Initial status
                    payment.order.save()
                    
                    # Send email notification to admin
                    from django.core.mail import send_mail
                    send_mail(
                        'New Order Requires Approval',
                        f'Order #{payment.order.id} needs your review.',
                        settings.DEFAULT_FROM_EMAIL,
                        [settings.ADMIN_EMAIL],
                        fail_silently=True,
                    )

                return redirect(f"{reverse('payment_success')}?reference={reference}")
            except Payment.DoesNotExist:
                print(f"Payment {reference} not found")
                return redirect(reverse('payment_failed'))
        return redirect(f"{reverse('payment_failed')}?reference={reference}")

    except Exception as e:
        print(f"Error in callback: {str(e)}")
        return redirect(reverse('payment_failed'))