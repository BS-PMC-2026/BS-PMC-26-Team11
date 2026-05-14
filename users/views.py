
import re
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.hashers import make_password, check_password
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.http import JsonResponse, HttpResponseNotAllowed
from django.utils import timezone
from django.utils.dateparse import parse_date
from .models import User, Package, CartItem, Discount
from .cancellation import assert_cancellation_window_open, cancellation_deadline, is_cancellation_window_open
from .exceptions import TimeExpired
from .reservations import release_expired_reservations


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


def package_reservation_admin(request):
    user = _get_logged_in_user(request)
    if not _is_admin(user):
        return redirect('home')

    packages = Package.objects.all().order_by('id')
    error_message = None
    success_message = request.GET.get('success')

    if request.method == 'POST':
        for key, raw in request.POST.items():
            if not key.startswith('reservation_minutes_'):
                continue
            pk = key.replace('reservation_minutes_', '')
            if not pk.isdigit():
                continue
            raw = (raw or '').strip()
            try:
                val = int(raw)
                if val < 1 or val > 10080:
                    raise ValueError
            except (ValueError, TypeError):
                error_message = 'זמן שמירה לא חוקי (1–10080 דקות).'
                break
            Package.objects.filter(id=int(pk)).update(reservation_minutes=val)
        if not error_message:
            return redirect(f"{reverse('package_reservation_admin')}?success=saved")

    return render(request, 'users/admin_package_reservations.html', {
        'packages': packages,
        'full_name': user.full_name,
        'user_role': user.role,
        'error_message': error_message,
        'success_message': success_message,
    })


@never_cache
def home_page(request):
    if not request.session.get('user_id'):
        return redirect('home')

    user = _get_logged_in_user(request)
    full_name = request.session.get('full_name', 'User')
    user_role = user.role if user else 'user'
    response = render(request, 'home.html', {
        'full_name': full_name,
        'user_role': user_role,
    })
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


def _is_admin(user):
    return user is not None and user.role == 'admin'


def package_list(request):
    user = _get_logged_in_user(request)
    if not user:
        return redirect('home')

    release_expired_reservations()
    packages = Package.objects.filter(is_available=True)
    success_message = request.GET.get('success')
    error_message = request.GET.get('error')
    reserved_minutes = request.GET.get('minutes')

    return render(request, 'users/packages.html', {
        'packages': packages,
        'full_name': user.full_name,
        'user_role': user.role,
        'success_message': success_message,
        'error_message': error_message,
        'reserved_minutes': reserved_minutes,
    })


def package_detail(request, package_id):
    user = _get_logged_in_user(request)
    if not user:
        return redirect('home')

    release_expired_reservations()
    package = get_object_or_404(Package, id=package_id)
    return render(request, 'users/package_detail.html', {
        'package': package,
        'full_name': user.full_name,
        'user_role': user.role,
    })


def add_to_cart(request, package_id):
    user = _get_logged_in_user(request)
    if not user:
        return redirect('home')

    package = get_object_or_404(Package, id=package_id)
    if not package.is_available:
        return redirect(f"{reverse('packages')}?error=not_available")

    release_expired_reservations()
    if package.available_capacity() <= 0:
        return redirect(f"{reverse('packages')}?error=capacity_full")

    now = timezone.now()
    minutes = int(package.reservation_minutes)
    CartItem.objects.create(
        user=user,
        package=package,
        package_name=package.name,
        reserved_at=now,
        expires_at=now + timedelta(minutes=minutes),
    )

    return redirect(f"{reverse('packages')}?success=reserved&minutes={minutes}")


def cart_view(request):
    user = _get_logged_in_user(request)
    if not user:
        return redirect('home')

    release_expired_reservations()
    now = timezone.now()
    reserved_items = CartItem.objects.filter(user=user, status='Reserved', expires_at__gt=now).select_related('package')
    orders = []
    for item in reserved_items:
        orders.append({
            'item': item,
            'cancelable': is_cancellation_window_open(item.reserved_at, now=now),
            'cancel_until': cancellation_deadline(item.reserved_at),
        })

    path = request.path.rstrip('/')
    page_heading = 'ההזמנות שלי' if path.endswith('my-orders') else 'עגלתי'

    return render(request, 'users/cart.html', {
        'orders': orders,
        'full_name': user.full_name,
        'cart_count': len(orders),
        'page_heading': page_heading,
    })


def promotion_management(request):
    user = _get_logged_in_user(request)
    if not _is_admin(user):
        return redirect('home')

    packages = Package.objects.all()
    promotions = Discount.objects.select_related('package').order_by('-start_date')
    error_message = None
    success_message = request.GET.get('success')

    preselected_package_id = request.GET.get('package_id', '')

    if request.method == 'POST':
        form_data = {
            'package_id': request.POST.get('package_id', ''),
            'promotion_mode': request.POST.get('promotion_mode', Discount.PromotionMode.PERCENTAGE),
            'discount_percentage': request.POST.get('discount_percentage', '').strip(),
            'sale_price': request.POST.get('sale_price', '').strip(),
            'start_date': request.POST.get('start_date', ''),
            'end_date': request.POST.get('end_date', ''),
        }
    else:
        form_data = {
            'package_id': preselected_package_id,
            'promotion_mode': Discount.PromotionMode.PERCENTAGE,
            'discount_percentage': '',
            'sale_price': '',
            'start_date': '',
            'end_date': '',
        }

    if request.method == 'POST':
        package_id = form_data['package_id']
        promotion_mode = form_data['promotion_mode']
        if promotion_mode not in (Discount.PromotionMode.PERCENTAGE, Discount.PromotionMode.SALE_PRICE):
            promotion_mode = Discount.PromotionMode.PERCENTAGE

        discount_percentage = form_data['discount_percentage']
        sale_price_raw = form_data['sale_price']
        start_date_value = form_data['start_date']
        end_date_value = form_data['end_date']

        package = None
        if not package_id:
            error_message = 'בחר חבילה תקינה.'
        else:
            package = get_object_or_404(Package, id=package_id)

        discount_value = None
        sale_price_value = None

        if not error_message and promotion_mode == Discount.PromotionMode.SALE_PRICE:
            if not sale_price_raw:
                error_message = 'יש להזין מחיר מבצע.'
            else:
                try:
                    sale_price_value = Decimal(sale_price_raw.replace(',', '.'))
                except (InvalidOperation, ValueError, TypeError):
                    error_message = 'מחיר המבצע אינו מספר חוקי.'
            if not error_message and package is not None:
                if sale_price_value <= 0:
                    error_message = 'מחיר המבצע חייב להיות חיובי.'
                elif sale_price_value >= package.price:
                    error_message = 'מחיר המבצע חייב להיות נמוך ממחיר החבילה המקורי.'

        elif not error_message:
            promotion_mode = Discount.PromotionMode.PERCENTAGE
            try:
                discount_value = int(discount_percentage)
                if discount_value < 1 or discount_value > 100:
                    raise ValueError
            except (TypeError, ValueError):
                error_message = 'יש להזין אחוז הנחה חוקי בין 1 ל-100.'

        start_date = parse_date(start_date_value)
        end_date = parse_date(end_date_value)
        if not error_message:
            if not start_date or not end_date:
                error_message = 'יש להזין תאריכים חוקיים לתחילת ונקודת הסיום.'
            elif start_date > end_date:
                error_message = 'תאריך ההתחלה חייב להיות לפני או שווה לתאריך הסיום.'

        if not error_message:
            create_kwargs = {
                'package': package,
                'promotion_mode': promotion_mode,
                'start_date': start_date,
                'end_date': end_date,
            }
            if promotion_mode == Discount.PromotionMode.SALE_PRICE:
                create_kwargs['sale_price'] = sale_price_value
                create_kwargs['discount_percentage'] = None
            else:
                create_kwargs['discount_percentage'] = discount_value
                create_kwargs['sale_price'] = None
            Discount.objects.create(**create_kwargs)
            return redirect(f"{reverse('promotions')}?success=created")

    return render(request, 'users/promotions.html', {
        'packages': packages,
        'promotions': promotions,
        'full_name': user.full_name,
        'error_message': error_message,
        'success_message': success_message,
        'form_data': form_data,
    })


@csrf_exempt
def cancel_user_package(request, order_id):
    if request.method != 'DELETE':
        return HttpResponseNotAllowed(['DELETE'])

    user = _get_logged_in_user(request)
    if not user:
        return JsonResponse({'error': 'authentication_required'}, status=403)

    try:
        order = CartItem.objects.get(id=order_id)
    except CartItem.DoesNotExist:
        return JsonResponse({'error': 'not_found'}, status=404)

    if order.user_id != user.id:
        return JsonResponse({'error': 'forbidden'}, status=403)

    if order.status != 'Reserved':
        return JsonResponse({'error': 'already_cancelled'}, status=400)

    try:
        assert_cancellation_window_open(order.reserved_at)
    except TimeExpired:
        return JsonResponse({'error': 'TimeExpired'}, status=400)

    order.status = 'Cancelled'
    order.save()
    return JsonResponse({'status': 'cancelled', 'id': order.id})


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