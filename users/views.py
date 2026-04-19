
import re
from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password, check_password
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .models import User


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
from django.http import HttpResponse

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

        return redirect('home')

    return render(request, 'users/login.html')