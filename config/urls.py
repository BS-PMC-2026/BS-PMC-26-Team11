from django.urls import path, include
from django.http import HttpResponse

def home(request):
    return HttpResponse("Project is running")

def signup_success(request):
    return HttpResponse("Signup completed successfully")

urlpatterns = [
    path('', home, name='home'),
    path('', include('users.urls')),
    path('signup-success/', signup_success, name='signup_success'),
]