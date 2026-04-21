from django.urls import path, include
from django.shortcuts import render
from users.views import login_view

def home_page(request):
    full_name = request.session.get('full_name', 'User')
    return render(request, 'home.html', {'full_name': full_name})

def signup_success(request):
    return render(request, 'signup_success.html')

urlpatterns = [
    path('', login_view, name='home'),
    path('home/', home_page, name='home_page'),
    path('users/', include('users.urls')),
    path('signup-success/', signup_success, name='signup_success'),
]