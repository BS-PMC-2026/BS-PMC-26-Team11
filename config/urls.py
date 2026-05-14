from django.urls import path, include
from django.shortcuts import render
from users.views import login_view, logout_view, home_page, package_list, package_detail, add_to_cart, cart_view, cancel_user_package

def signup_success(request):
    return render(request, 'signup_success.html')

urlpatterns = [
    path('', login_view, name='home'),
    path('home/', home_page, name='home_page'),
    path('packages/', package_list, name='packages'),
    path('packages/<int:package_id>/', package_detail, name='package_detail'),
    path('packages/<int:package_id>/add/', add_to_cart, name='add_to_cart'),
    path('cart/', cart_view, name='cart'),
    path('api/user/packages/<int:package_id>/', cancel_user_package, name='cancel_user_package'),
    path('users/', include('users.urls')),
    path('logout/', logout_view, name='logout'),
    path('signup-success/', signup_success, name='signup_success'),
]