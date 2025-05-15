"""
URL configuration for restaurant_django project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from restaurant import views
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path('', views.welcome_page, name='welcome'),
    path('login/', views.login_page, name='login'),
    path('home/', views.homepage, name='homepage'),
    path('contact_us/', views.contact_us_page, name='contact_us'),
    path('about/', views.about_page, name='about'),
    path('menu/', views.menu_page, name='menu'),
    path('cart/', views.cart_page, name='cart'),
    path('initiate_payment/', views.initiate_payment, name='initiate-payment'),
    path('payment/verify/', views.payment_verification_callback, name='payment_verification_callback'),
    #path('payment/success/<str:reference>/', views.payment_success, name='payment-success'),
    # path('payment/failed/', views.payment_failed, name='payment_failed'),
    path('logout/', views.logout_page, name='logout'),
    path('user_account/', views.user_account_page, name='user_account'),
     path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),

    # path('review/<int:order_id>/', views.review_page, name='review'),
    # path('edit_order/<int:order_id>/', views.edit_order_page, name='edit_order'),


    
    path('admin/auth', views.admin_auth, name='admin_auth'),
    path('adminsuper122/', views.adminsuper122, name='adminsuper122'),  
    # Note: 'admin_orders'
    
    path('admin/logout/', views.admin_logout, name='admin_logout'),
    
    
    path('admin/', admin.site.urls),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
   
   # path('about/', views.about, name='about'),
    #path('contact/', views.contact, name='contact'),
    
