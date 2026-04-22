from django.urls import path, include
from django.shortcuts import render
from users.views import login_view, logout_view, home_page

def signup_success(request):
    return render(request, 'signup_success.html')

urlpatterns = [
    path('', login_view, name='home'),
    path('home/', home_page, name='home_page'),
    path('users/', include('users.urls')),
    path('logout/', logout_view, name='logout'),
    path('signup-success/', signup_success, name='signup_success'),
]