
import re
from datetime import timedelta

from django.views.decorators.cache import never_cache
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.hashers import make_password, check_password
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import User, Package, CartItem


def is_strong_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."

    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."

    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."

    if not re.search(r"\d", password):
        return False, "Password must contain at least one number."

    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
        return False, "Password must contain at least one special character."

    return True, ""






def signup_view(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not full_name or not email or not phone or not password or not confirm_password:
            return render(request, 'users/signup.html', {
                'error': 'All fields are required.',
                'full_name': full_name,
                'email': email,
                'phone': phone,
            })



# בדיקת טלפון
        if not re.fullmatch(r'05\d{8}', phone):
           return render(request, 'users/signup.html', {
        'error': 'מספר טלפון חייב להכיל 10 ספרות ולהתחיל ב- 05 ',
        'full_name': full_name,
        'email': email,
        'phone': phone,
           })


        try:
            validate_email(email)
        except ValidationError:
            return render(request, 'users/signup.html', {
                'error': 'Invalid email format.',
                'full_name': full_name,
                'email': email,
                'phone': phone,
            })

        if User.objects.filter(email=email).exists():
            return render(request, 'users/signup.html', {
                'error': 'Email already exists.',
                'full_name': full_name,
                'email': email,
                'phone': phone,
            })

        if password != confirm_password:
            return render(request, 'users/signup.html', {
                'error': 'Passwords do not match.',
                'full_name': full_name,
                'email': email,
                'phone': phone,
            })

        is_valid, message = is_strong_password(password)
        if not is_valid:
            return render(request, 'users/signup.html', {
                'error': message,
                'full_name': full_name,
                'email': email,
                'phone': phone,
            })

        role = 'admin' if User.objects.count() == 0 else 'user'

        User.objects.create(
            full_name=full_name,
            email=email,
            password=make_password(password),
            phone=phone,
            role='user'
        )

        return redirect('signup_success')

    return render(request, 'users/signup.html')




def logout_view(request):
    request.session.flush()
    response = redirect('home')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


@never_cache
def home_page(request):
    if not request.session.get('user_id'):
        return redirect('home')

    full_name = request.session.get('full_name', 'User')
    response = render(request, 'home.html', {'full_name': full_name})
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def _get_logged_in_user(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return None
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return None


def package_list(request):
    user = _get_logged_in_user(request)
    if not user:
        return redirect('home')

    packages = Package.objects.filter(is_available=True)
    success_message = request.GET.get('success')
    error_message = request.GET.get('error')

    return render(request, 'users/packages.html', {
        'packages': packages,
        'full_name': user.full_name,
        'success_message': success_message,
        'error_message': error_message,
    })


def package_detail(request, package_id):
    user = _get_logged_in_user(request)
    if not user:
        return redirect('home')

    package = get_object_or_404(Package, id=package_id)
    return render(request, 'users/package_detail.html', {
        'package': package,
        'full_name': user.full_name,
    })


def add_to_cart(request, package_id):
    user = _get_logged_in_user(request)
    if not user:
        return redirect('home')

    package = get_object_or_404(Package, id=package_id)
    if not package.is_available:
        return redirect(f"{reverse('packages')}?error=not_available")

    if package.available_capacity() <= 0:
        return redirect(f"{reverse('packages')}?error=capacity_full")

    CartItem.objects.create(
        user=user,
        package=package,
        package_name=package.name,
        reserved_until=timezone.now() + timedelta(minutes=15)
    )

    return redirect(f"{reverse('packages')}?success=reserved")


def cart_view(request):
    user = _get_logged_in_user(request)
    if not user:
        return redirect('home')

    cart_items = CartItem.objects.filter(user=user, reserved_until__gt=timezone.now()).select_related('package')
    expired_items = CartItem.objects.filter(user=user, reserved_until__lte=timezone.now())
    
    return render(request, 'users/cart.html', {
        'cart_items': cart_items,
        'full_name': user.full_name,
        'cart_count': cart_items.count(),
    })


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return render(request, 'users/login.html', {
                'error': 'אימייל או סיסמה שגויים.',
                'email': email,
            })

        if not check_password(password, user.password):
            return render(request, 'users/login.html', {
                'error': 'אימייל או סיסמה שגויים.',
                'email': email,
            })

        request.session['user_id'] = user.id
        request.session['role'] = user.role
        request.session['full_name'] = user.full_name

        return redirect('home_page')

    return render(request, 'users/login.html')