from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from users.views import (
    login_view,
    logout_view,
    home_page,
    package_list,
    package_detail,
    add_to_cart,
    cart_view,
    promotion_management,
    cancel_user_package,
    package_reservation_admin,
    admin_dashboard,
    admin_packages,
    edit_package,
    delete_package,
)

def signup_success(request):
    return render(request, 'signup_success.html')

urlpatterns = [
    path('', login_view, name='home'),
    path('home/', home_page, name='home_page'),
    path('packages/', package_list, name='packages'),
    path('packages/<int:package_id>/', package_detail, name='package_detail'),
    path('packages/<int:package_id>/add/', add_to_cart, name='add_to_cart'),
    path('my-orders/', cart_view, name='my_orders'),
    path('cart/', cart_view, name='cart'),
    path('admin/dashboard/', admin_dashboard, name='admin_dashboard'),
    path('admin/packages/', admin_packages, name='admin_packages_view'),
    path('admin/packages/<int:package_id>/edit/', edit_package, name='edit_package'),
    path('admin/packages/<int:package_id>/delete/', delete_package, name='delete_package'),
    path('admin/package-reservations/', package_reservation_admin, name='package_reservation_admin'),
    path('admin/promotions/', promotion_management, name='promotions'),
    path('admin/', admin.site.urls),
    path('api/user/packages/<int:order_id>/', cancel_user_package, name='cancel_user_package'),
    path('users/', include('users.urls')),
    path('logout/', logout_view, name='logout'),
    path('signup-success/', signup_success, name='signup_success'),
]