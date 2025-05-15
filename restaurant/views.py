from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login
from datetime import datetime, date
time_package = datetime.now()
from .models import UserInfo, UserProfile, Order, MenuItem
from dateutil.parser import parse
from django.contrib.auth.models import User, auth
from .models import Admin, MenuItem, Category, Payment,RestaurantSettings, Notification, OrderItem, Order, PasswordReset
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
import secrets



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

            # Create or Update UserProfile
            user_profile, created = UserProfile.objects.get_or_create(user=user)
            user_profile.name = get_name # Store the full name in UserProfile
            user_profile.save()

            # Create UserInfo with all fields
            user_info, created = UserInfo.objects.get_or_create(user=user)
            user_info.name = get_name
            user_info.email = get_email
            user_info.username = get_username
            user_info.is_superuser = '0'  # Since it's a regular user
            user_info.is_staff = '0'      # Since it's a regular user
            user_info.status = 'active'   # Set initial status
            user_info.set_password(get_password)  # Hash and save the password
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


def about_page(request):
    return render(request, 'about_page.html')




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
        # Check if it's an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                # Update user profile
                user_profile.phone = request.POST.get('phone', user_profile.phone)
                user_profile.address = request.POST.get('address', user_profile.address)
                user_profile.location = request.POST.get('location', user_profile.location)
                
                # Handle profile image
                if 'profile_image' in request.FILES:
                    user_profile.profile_image = request.FILES['profile_image']
                
                user_profile.save()
                
                response_data = {
                    'status': 'success',
                    'message': 'Profile updated successfully!'
                }
                
                if user_profile.profile_image:
                    response_data['profile_image_url'] = user_profile.profile_image.url
                
                return JsonResponse(response_data)
                
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Failed to update profile: {str(e)}'
                })
        else:
            # Handle regular form submission
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
    settings, created = RestaurantSettings.objects.get_or_create(id=1)

    # Handle tab selection
    tab = request.POST.get('tab', request.GET.get('tab', 'dashboard'))

    if request.method == 'POST':
        if tab == 'notifications' and request.POST.get('action') == 'mark_read':
            Notification.objects.filter(admin=admin, is_read=False).update(is_read=True)
            messages.success(request, "All notifications marked as read.")
            return redirect(f"{request.path}?tab=notifications")
        elif tab == 'orders':
            order_id = request.POST.get('order_id')
            status = request.POST.get('status')
            
            logger.info(f"Attempting to update order {order_id} to status {status}")
            
            if not order_id or not status:
                messages.error(request, "Order ID and status are required!")
                return redirect(f"{request.path}?tab=orders")
            
            if status not in ['Pending', 'Confirmed', 'Completed', 'Cancelled']:
                messages.error(request, "Invalid status value!")
                return redirect(f"{request.path}?tab=orders")
            
            try:
                order = Order.objects.get(id=order_id)
                old_status = order.status
                
                # Only update if status has changed
                if old_status != status:
                    order.status = status
                    order.save()
                    logger.info(f"Order {order_id} status updated from {old_status} to {status}")
                    
                    # Send notification to user
                    request.session.setdefault('notifications', [])
                    request.session['notifications'].append({
                        'user_id': order.user_id,
                        'message': f"Your order #{order.order_id} status has been updated to {status}."
                    })
                    request.session.modified = True
                    
                    # Send email notification if user has email
                    if order.user.email:
                        try:
                            send_mail(
                                f'Order #{order.order_id} Status Update',
                                f'Your order status has been updated to {status}.',
                                settings.DEFAULT_FROM_EMAIL,
                                [order.user.email],
                                fail_silently=True,
                            )
                            logger.info(f"Email notification sent for order {order_id}")
                        except Exception as e:
                            logger.error(f"Failed to send email notification: {str(e)}")
                    
                    messages.success(request, f"Order #{order.order_id} status updated to {status}!")
                else:
                    messages.info(request, f"Order #{order.order_id} is already {status}")
                    
            except Order.DoesNotExist:
                logger.error(f"Order not found: {order_id}")
                messages.error(request, "Order not found!")
            except Exception as e:
                logger.error(f"Error updating order {order_id}: {str(e)}")
                messages.error(request, f"Error updating order: {str(e)}")
            
            return redirect(f"{request.path}?tab=orders")
        elif tab == 'menu':
            action = request.POST.get('action')
            
            if action == 'add':
                try:
                    # Create new menu item
                    menu_item = MenuItem(
                        name=request.POST.get('name'),
                        Category=Category.objects.get(name=request.POST.get('category')),
                        price=request.POST.get('price'),
                        description=request.POST.get('description', ''),
                        available=True if request.POST.get('available') == 'on' else False,
                        is_special=True if request.POST.get('is_special') == 'on' else False
                    )
                    
                    # Handle image upload if provided
                    if 'image' in request.FILES:
                        menu_item.image = request.FILES['image']
                    
                    menu_item.save()
                    messages.success(request, f"Menu item '{menu_item.name}' added successfully!")
                except Exception as e:
                    messages.error(request, "Error adding menu item. Please try again.")
                
            elif action == 'edit':
                try:
                    item_id = request.POST.get('item_id')
                    menu_item = MenuItem.objects.get(id=item_id)
                    menu_item.description = request.POST.get('description')
                    menu_item.price = request.POST.get('price')
                    menu_item.save()
                    messages.success(request, f"Menu item '{menu_item.name}' updated successfully!")
                except:
                    messages.error(request, "Error updating menu item. Please try again.")
                
            elif action == 'delete':
                try:
                    item_id = request.POST.get('item_id')
                    menu_item = MenuItem.objects.get(id=item_id)
                    menu_item.delete()
                    messages.success(request, f"Menu item deleted successfully!")
                except:
                    messages.error(request, "Error deleting menu item. Please try again.")
            
            return redirect(f"{request.path}?tab=menu")

    # Fetch all data
    total_orders = Order.objects.count()
    total_revenue = Order.objects.aggregate(total=Sum('total_price'))['total'] or 0
    total_customers = Order.objects.values('user_id').distinct().count()
    total_menu_items = MenuItem.objects.count()
    recent_orders = Order.objects.order_by('-order_date')[:5]
    popular_items = MenuItem.objects.annotate(num_orders=Count('orderitem')).order_by('-num_orders')[:4]
    notification_count = Order.objects.filter(status='Pending').count()
    menu_items = list(MenuItem.objects.all().order_by('name'))
    categories = Category.objects.all()
    
    # Get orders with their items
    orders = Order.objects.all().order_by('-order_date')
    for order in orders:
        order.items_list = order.items.all()  # Add items to each order
    
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
        'settings': settings,
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
            cart_items = data.get('cart', [])
            
            if not cart_items:
                return JsonResponse({'error': 'Cart is empty'}, status=400)
            
            # Validate required fields
            if not data.get('reference'):
                return JsonResponse({'error': 'Reference is required'}, status=400)
            
            # Calculate total amount
            total_amount = sum(item['price'] * item['quantity'] for item in cart_items)
            
            # Get product names for the order
            product_names = []
            for item in cart_items:
                menu_item = MenuItem.objects.get(id=item['id'])
                product_names.append(f"{menu_item.name} (x{item['quantity']})")
            
            # Create order first with product names
            order = Order.objects.create(
                user=user,
                total_price=total_amount,
                status='Pending',  # Set initial status as Pending
                product_name=', '.join(product_names)  # Store product names
            )
            
            # Create order items
            for item in cart_items:
                menu_item = MenuItem.objects.get(id=item['id'])
                OrderItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    quantity=item['quantity'],
                    price=item['price']
                )
            
            # Create payment record with exact model fields
            payment = Payment.objects.create(
                order=order,
                user=user,
                amount=total_amount,
                reference=data['reference'],
                status='pending'
            )
            
            # Store cart data in session
            request.session['pending_payment'] = {
                'reference': payment.reference,
                'cart': cart_items
            }
            request.session.modified = True
            
            # Initialize Paystack payment
            paystack = PaystackAPI()
            response = paystack.initialize_payment(
                email=user.email if user else data.get('email', ''),
                amount=int(total_amount * 100),  # Convert to kobo
                reference=payment.reference,
                callback_url=request.build_absolute_uri(reverse('payment_verification_callback'))
            )
            
            if response.get('status'):
                return JsonResponse({
                    'success': True,
                    'redirect_url': response['data']['authorization_url']
                })
            
            # If we get here, the payment initialization failed
            error_message = response.get('message', 'Payment initialization failed')
            logger.error(f"Payment initialization failed: {error_message}")
            return JsonResponse({'error': error_message}, status=400)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            logger.error(f"Unexpected error in initiate_payment: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

def payment_verification_callback(request):
    reference = request.GET.get('reference')
    logger.info(f"Payment verification callback received with reference: {reference}")
    
    if not reference:
        logger.error("No reference provided in callback")
        return redirect('homepage')

    try:
        # Verify payment with Paystack
        headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
        verify_url = f"https://api.paystack.co/transaction/verify/{reference}"
        logger.info(f"Verifying payment with Paystack: {verify_url}")
        
        response = requests.get(verify_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        logger.info(f"Paystack verification response: {data}")

        # Check if payment exists
        try:
            payment = Payment.objects.get(reference=reference)
            logger.info(f"Found payment record: {payment.reference}")
        except Payment.DoesNotExist:
            logger.error(f"Payment not found for reference: {reference}")
            return redirect('homepage')

        # Process payment based on Paystack response
        if data.get('status') and data.get('data', {}).get('status') == 'success':
            logger.info("Payment verified as successful by Paystack")
            
            # Update payment status and amount
            payment.status = 'successful'
            payment.amount = float(data['data']['amount'])/100  # Convert from kobo to naira
            payment.save()
            logger.info(f"Updated payment status to successful: {payment.reference}")

            # Update order status to Pending
            order = payment.order
            order.status = 'Pending'
            order.save()
            logger.info(f"Updated order status to Pending: {order.id}")
            

            # Clear session data
            if 'pending_payment' in request.session:
                del request.session['pending_payment']
            if 'cart' in request.session:
                del request.session['cart']
            request.session.modified = True
            logger.info("Cleared session data")

            # Get order items for the success page
            order_items = OrderItem.objects.filter(order=order)
            
            # Render success page directly instead of redirecting
            context = {
                'order': order,
                'payment': payment,
                'order_items': order_items,
                'reference': reference
            }
            
            logger.info(f"Rendering success page for order {order.id}")
            return render(request, 'payment_success.html', context)
        
        # If payment is not successful
        logger.warning(f"Payment not successful for reference {reference}")
        return redirect('homepage')

    except requests.exceptions.RequestException as e:
        logger.error(f"Paystack API error: {str(e)}")
        return redirect('homepage')
    except Exception as e:
        logger.error(f"Unexpected error in payment verification: {str(e)}")
        return redirect('homepage')







def forgot_password(request):
    if request.method == 'POST':
        get_email = request.POST.get('get_email')
        
        if not get_email:
            messages.info(request, 'Email field is required')
            return redirect('forgot_password')
        
        try:
            # First check if user exists
            user = User.objects.get(email=get_email)
            user_info = UserInfo.objects.get(user=user)
            
            # Generate a random token
            token = secrets.token_urlsafe(32)
            
            # Create password reset record
            password_reset = PasswordReset.objects.create(
                reset_id=token,
                user=user
            )
            
            # Create reset link
            reset_link = f"{request.scheme}://{request.get_host()}/reset-password/{token}"
            
            # Send email (will be printed to console in testing mode)
            subject = 'Password Reset Request'
            message = f'''
            Hello {user_info.name},

            You have requested to reset your password. Click the link below to reset your password:

            {reset_link}

            If you did not request this password reset, please ignore this message.

            This link will expire in 24 hours.

            Best regards,
            Your Restaurant Team
            '''
            
            from_email = 'noreply@restaurant.com'
            recipient_list = [get_email]
            
            send_mail(subject, message, from_email, recipient_list)
            
            messages.success(request, 'Password reset link has been sent to your email. Please check your console for the reset link.')
            return redirect('login')
                
        except User.DoesNotExist:
            messages.error(request, 'No user found with this email address.')
            return redirect('forgot_password')
        except UserInfo.DoesNotExist:
            messages.error(request, 'User profile not found.')
            return redirect('forgot_password')
    
    return render(request, 'forgot_password.html')





def reset_password(request, token):
    try:
        # Get the password reset record
        password_reset = PasswordReset.objects.get(reset_id=token, is_used=False)
        
        # Check if the reset link is expired (24 hours)
        if (datetime.now() - password_reset.created_at).total_seconds() > 86400:  # 24 hours in seconds
            messages.error(request, 'Password reset link has expired.')
            return redirect('login')
        
        if request.method == 'POST':
            get_password = request.POST.get('get_password')
            confirm_password = request.POST.get('confirm_password')
            
            if not all([get_password, confirm_password]):
                messages.info(request, 'All fields are required')
                return render(request, 'reset_password.html', {'token': token})
            
            if get_password != confirm_password:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'reset_password.html', {'token': token})
            
            # Update the user's password in both User and UserInfo models
            user = password_reset.user
            logger.info(f"Resetting password for user: {user.username}")
            
            # Update Django User model password
            user.set_password(get_password)
            user.save()
            logger.info("Django User model password updated successfully")
            
            # Update UserInfo password
            user_info = UserInfo.objects.get(user=user)
            user_info.set_password(get_password)
            user_info.save()
            logger.info("UserInfo model password updated successfully")
            
            # Mark the reset token as used
            password_reset.is_used = True
            password_reset.save()
            logger.info("Password reset token marked as used")
            
            messages.success(request, 'Your password has been reset successfully. You can now login with your new password.')
            return redirect('login')
            
        return render(request, 'reset_password.html', {'token': token})
    except PasswordReset.DoesNotExist:
        messages.error(request, 'Invalid or expired reset token.')
        return redirect('login')
    except Exception as e:
        logger.error(f"Error during password reset: {str(e)}")
        messages.error(request, 'An error occurred while resetting your password. Please try again.')
        return redirect('login')

