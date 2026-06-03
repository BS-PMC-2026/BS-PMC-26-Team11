from datetime import timedelta
import re
from decimal import Decimal, InvalidOperation
from django.db import transaction
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
from .email import send_package_cancellation_email, send_order_success_email
from django.contrib import messages

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
        form_data = {
            'full_name': full_name,
            'email': email,
            'phone': phone,
        }
        field_errors = {}

        if not full_name:
            field_errors['full_name'] = 'יש להזין שם מלא.'
        if not email:
            field_errors['email'] = 'יש להזין אימייל.'
        if not phone:
            field_errors['phone'] = 'יש להזין מספר טלפון.'
        if not password:
            field_errors['password'] = 'יש להזין סיסמה.'
        if not confirm_password:
            field_errors['confirm_password'] = 'יש להזין אימות סיסמה.'

        if field_errors:
            return render(request, 'users/signup.html', {
                'error': 'יש למלא את כל שדות החובה.',
                'field_errors': field_errors,
                **form_data,
            })

        # בדיקת טלפון
        if not re.fullmatch(r'05\d{8}', phone):
            return render(request, 'users/signup.html', {
                'error': 'מספר טלפון חייב להכיל 10 ספרות ולהתחיל ב-05.',
                'field_errors': {'phone': 'מספר טלפון חייב להכיל 10 ספרות ולהתחיל ב-05.'},
                **form_data,
            })


        try:
            validate_email(email)
        except ValidationError:
            return render(request, 'users/signup.html', {
                'error': 'פורמט האימייל אינו תקין.',
                'field_errors': {'email': 'יש להזין אימייל בפורמט תקין.'},
                **form_data,
            })

        if User.objects.filter(email=email).exists():
            return render(request, 'users/signup.html', {
                'error': 'האימייל כבר קיים במערכת.',
                'field_errors': {'email': 'האימייל כבר קיים במערכת.'},
                **form_data,
            })

        if password != confirm_password:
            return render(request, 'users/signup.html', {
                'error': 'הסיסמאות אינן תואמות.',
                'field_errors': {'confirm_password': 'הסיסמאות אינן תואמות.'},
                **form_data,
            })

        is_valid, message = is_strong_password(password)
        if not is_valid:
            return render(request, 'users/signup.html', {
                'error': message,
                'field_errors': {'password': message},
                **form_data,
            })

        role = 'admin' if User.objects.count() == 0 else 'user'

        User.objects.create(
            full_name=full_name,
            email=email,
            password=make_password(password),
            phone=phone,
            role=role
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
    user = _get_logged_in_user(request)
    user_role = user.role if user else 'user'
    cart_context = _build_cart_context(user)
    response = render(request, 'home.html', {
        'user_role': user_role,
        'is_authenticated': user is not None,
        **cart_context,
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


def _build_cart_context(user):
    if not user:
        return {
            'cart_items': [],
            'cart_count': 0,
            'cart_total': 0,
        }

    release_expired_reservations()
    now = timezone.now()
    active_items = CartItem.objects.filter(
        user=user,
        status='Reserved',
        expires_at__gt=now,
    ).select_related('package')
    cart_items = []
    total = 0
    for item in active_items:
        price = item.package.get_discounted_price() or item.package.price
        total += price
        cart_items.append({
            'item': item,
            'price': price,
            'quantity': 1,
        })
    return {
        'cart_items': cart_items,
        'cart_count': len(cart_items),
        'cart_total': total,
    }


def package_list(request):
    user = _get_logged_in_user(request)
    packages = Package.objects.all().order_by('id')
    success_message = request.GET.get('success')
    error_message = request.GET.get('error')
    reserved_minutes = request.GET.get('minutes')
    cart_context = _build_cart_context(user)

    return render(request, 'users/packages.html', {
        'packages': packages,
        'full_name': user.full_name if user else '',
        'user_role': user.role if user else 'guest',
        'is_authenticated': user is not None,
        'success_message': success_message,
        'error_message': error_message,
        'reserved_minutes': reserved_minutes,
        **cart_context,
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

    is_admin = _is_admin(user)
    now = timezone.now()
    orders = []

    if is_admin:
        all_items = CartItem.objects.select_related('package', 'user').filter(user__role='user')
        orders_by_user = {}
        for item in all_items:
            user_key = item.user.full_name
            if user_key not in orders_by_user:
                orders_by_user[user_key] = []
            orders_by_user[user_key].append({
                'item': item,
                'user': item.user,
                'cancelable': is_cancellation_window_open(item.reserved_at, now=now),
                'cancel_until': cancellation_deadline(item.reserved_at),
            })
        orders = orders_by_user
        cart_context = {
            'cart_items': [],
            'cart_total': Decimal('0.00'),
            'cart_count': 0,
            'user_role': 'admin',
        }
    else:
        cart_context = _build_cart_context(user)
        for item_data in cart_context['cart_items']:
            item = item_data['item']
            orders.append({
                'item': item,
                'cancelable': is_cancellation_window_open(item.reserved_at, now=now),
                'cancel_until': cancellation_deadline(item.reserved_at),
            })

    path = request.path.rstrip('/')
    page_heading = 'הזמנות של משתמשים' if is_admin else ('ההזמנה שלי' if path.endswith('my-orders') else 'עגלתי')

    return render(request, 'users/cart.html', {
        'orders': orders,
        'full_name': user.full_name,
        'page_heading': page_heading,
        'is_admin': is_admin,
        **cart_context,
    })

def edit_package(request, package_id):
    user = _get_logged_in_user(request)
    if not _is_admin(user):
        return redirect('home')

    package = get_object_or_404(Package, id=package_id)
    error_message = None
    success_message = request.GET.get('success')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        price = request.POST.get('price', '').strip()
        package_type = request.POST.get('package_type', '').strip()
        farm_area = request.POST.get('farm_area', '').strip()
        image = request.FILES.get('image')
        capacity = request.POST.get('capacity', '0').strip()
        reservation_minutes = request.POST.get('reservation_minutes', '15').strip()
        tour_datetime = request.POST.get('tour_datetime') or None
        cancellation_hours = request.POST.get('cancellation_hours', '24').strip()

        if not name:
            error_message = 'שם החבילה חובה.'
        elif not price:
            error_message = 'מחיר חובה.'
        else:
            try:
                price_value = Decimal(price)
                capacity_value = int(capacity) if capacity else 0
                reservation_value = int(reservation_minutes) if reservation_minutes else 15
                cancellation_value = int(cancellation_hours) if cancellation_hours else 24

                if reservation_value < 1 or reservation_value > 10080:
                    error_message = 'זמן שמירה חייב להיות בין 1 ל-10080 דקות.'
                elif cancellation_value < 1:
                    error_message = 'זמן הביטול חייב להיות לפחות שעה אחת.'
                else:
                    package.name = name
                    package.description = description
                    package.price = price_value
                    package.package_type = package_type
                    package.farm_area = farm_area
                    package.capacity = capacity_value
                    package.reservation_minutes = reservation_value
                    package.tour_datetime = tour_datetime
                    package.cancellation_hours = cancellation_value

                    if image:
                        package.image = image

                    package.save()

                    return redirect(
                        f"{reverse('edit_package', kwargs={'package_id': package_id})}?success=updated"
                    )

            except (InvalidOperation, ValueError):
                error_message = 'ערכים לא תקינים.'

    active_discount = package.get_active_discount()

    return render(request, 'users/edit_package.html', {
        'package': package,
        'full_name': user.full_name,
        'error_message': error_message,
        'success_message': success_message,
        'active_discount': active_discount,
    })

def admin_packages(request):
    user = _get_logged_in_user(request)
    if not _is_admin(user):
        return redirect('home')

    packages = Package.objects.all().order_by('id')
    error_message = None
    success_message = request.GET.get('success')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        price = request.POST.get('price', '').strip()
        package_type = request.POST.get('package_type', '').strip()
        farm_area = request.POST.get('farm_area', '').strip()
        image = request.FILES.get('image')
        capacity = request.POST.get('capacity', '0').strip()
        tour_datetime = request.POST.get('tour_datetime') or None
        cancellation_hours = request.POST.get('cancellation_hours', '24').strip()

        if not name:
            error_message = 'שם החבילה חובה.'
        elif not price:
            error_message = 'מחיר חובה.'
        else:
            try:
                price_value = Decimal(price)
                capacity_value = int(capacity) if capacity else 0
                cancellation_value = int(cancellation_hours) if cancellation_hours else 24

                if cancellation_value < 1:
                    error_message = 'זמן הביטול חייב להיות לפחות שעה אחת.'
                else:
                    Package.objects.create(
                        name=name,
                        description=description,
                        price=price_value,
                        package_type=package_type,
                        farm_area=farm_area,
                        image=image,
                        capacity=capacity_value,
                        tour_datetime=tour_datetime,
                        cancellation_hours=cancellation_value,
                    )

                    return redirect(f"{reverse('admin_packages_view')}?success=added")

            except (InvalidOperation, ValueError):
                error_message = 'ערכים לא תקינים.'

    return render(request, 'users/admin_packages.html', {
        'packages': packages,
        'full_name': user.full_name,
        'error_message': error_message,
        'success_message': success_message,
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
        order = CartItem.objects.select_related('package', 'user').get(id=order_id)
    except CartItem.DoesNotExist:
        return JsonResponse({'error': 'not_found'}, status=404)

    is_admin = user.role == 'admin'

    # משתמש רגיל יכול לבטל רק הזמנה שלו.
    # אדמין יכול לבטל כל הזמנה.
    if not is_admin and order.user_id != user.id:
        return JsonResponse({'error': 'forbidden'}, status=403)

    # אפשר לבטל רק הזמנות פעילות או ששולמו.
    if order.status not in ['Reserved', 'Paid']:
        return JsonResponse({'error': 'already_cancelled'}, status=400)

    # אדמין יכול לבטל בלי מגבלת זמן.
    if not is_admin:
        package = order.package

        # אם אין תאריך סיור, אי אפשר לבדוק חלון ביטול.
        if not package.tour_datetime:
            return JsonResponse({'error': 'missing_tour_datetime'}, status=400)

        cancel_deadline = package.tour_datetime - timedelta(hours=package.cancellation_hours)

        if timezone.now() > cancel_deadline:
            return JsonResponse({'error': 'TimeExpired'}, status=400)

    order.status = 'Cancelled'
    order.save()

    try:
        send_package_cancellation_email(order.user, order.package_name)
    except Exception:
        pass

    cart_context = _build_cart_context(user)

    return JsonResponse({
        'status': 'cancelled',
        'id': order.id,
        'cart_total': float(cart_context['cart_total']),
        'cart_count': cart_context['cart_count'],
    })







def login_view(request):
    if request.method == 'GET':
        return render(request, 'users/login.html')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        field_errors = {}

        if not email:
            field_errors['email'] = 'יש להזין אימייל.'
        else:
            try:
                validate_email(email)
            except ValidationError:
                field_errors['email'] = 'יש להזין אימייל בפורמט תקין.'
        if not password:
            field_errors['password'] = 'יש להזין סיסמה.'

        if field_errors:
            return render(request, 'users/login.html', {
                'error': 'יש לתקן את השדות המסומנים.',
                'field_errors': field_errors,
                'email': email,
            })

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return render(request, 'users/login.html', {
                'error': 'אימייל או סיסמה שגויים.',
                'field_errors': {'email': 'פרטי ההתחברות אינם נכונים.'},
                'email': email,
            })

        if not check_password(password, user.password):
            return render(request, 'users/login.html', {
                'error': 'אימייל או סיסמה שגויים.',
                'field_errors': {'password': 'פרטי ההתחברות אינם נכונים.'},
                'email': email,
            })

        request.session['user_id'] = user.id
        request.session['role'] = user.role
        request.session['full_name'] = user.full_name

        if user.role == 'admin':
            return redirect('admin_dashboard')
        return redirect('packages')


def admin_dashboard(request):
    user = _get_logged_in_user(request)
    if not user or user.role != 'admin':
        return redirect('home')

    total_orders = CartItem.objects.filter(status='Reserved').count()
    total_users = User.objects.filter(role='user').count()
    total_packages = Package.objects.count()
    users = User.objects.all().order_by('-id')

    return render(request, 'users/admin_dashboard.html', {
        'full_name': user.full_name,
        'total_orders': total_orders,
        'total_users': total_users,
        'total_packages': total_packages,
        'users': users,
    })

    return render(request, 'users/login.html')
from django.http import JsonResponse

def delete_package(request, package_id):
    user = _get_logged_in_user(request)

    if not user or user.role != 'admin':
        if request.method == 'DELETE':
            return JsonResponse({'error': 'forbidden'}, status=403)
        return redirect('login')

    if request.method not in ['POST', 'DELETE']:
        return redirect('/admin/packages/')

    package = get_object_or_404(Package, id=package_id)

    with transaction.atomic():
        if hasattr(package, 'image') and package.image:
            package.image.delete(save=False)

        package.delete()

    messages.success(request, 'החבילה נמחקה בהצלחה.')

    if request.method == 'DELETE':
        return JsonResponse({'status': 'deleted', 'id': package_id})

    return redirect('/admin/packages/')


#תשלום וביצוע ההזמנה!!

def payment_page(request):
    user = _get_logged_in_user(request)

    if not user:
        return redirect('home')

    cart_items = CartItem.objects.filter(
        user=user,
        status='Reserved'
    ).select_related('package')

    total_price = sum(item.package.price for item in cart_items)

    return render(request, 'users/payment.html', {
        'cart_items': cart_items,
        'full_name': user.full_name,
        'total_price': total_price,
    })



import re
from datetime import datetime
from django.contrib import messages


def complete_payment(request):
    user = _get_logged_in_user(request)

    if not user:
        return redirect('home')

    if request.method == 'POST':

        card_number = request.POST.get('card_number', '').replace(' ', '')
        expiry = request.POST.get('expiry', '').strip()
        cvv = request.POST.get('cvv', '').strip()

        # בדיקת מספר כרטיס
        if not re.fullmatch(r'\d{16}', card_number):
            messages.error(request, 'מספר כרטיס חייב להכיל 16 ספרות')
            return redirect('payment_page')

        # בדיקת CVV
        if not re.fullmatch(r'\d{3}', cvv):
            messages.error(request, 'CVV חייב להכיל 3 ספרות')
            return redirect('payment_page')

        # בדיקת תוקף
        if not re.fullmatch(r'(0[1-9]|1[0-2])\/\d{2}', expiry):
            messages.error(request, 'תוקף הכרטיס לא תקין')
            return redirect('payment_page')

        # בדיקה שהתוקף לא עבר
        try:
            month, year = expiry.split('/')
            month = int(month)
            year = int('20' + year)

            now = datetime.now()

            if year < now.year or (year == now.year and month < now.month):
                messages.error(request, 'הכרטיס פג תוקף')
                return redirect('payment_page')

        except:
            messages.error(request, 'תוקף הכרטיס לא תקין')
            return redirect('payment_page')

        # בדיקת שכל השדות מלאים
        if not card_number or not expiry or not cvv:
            messages.error(request, 'יש למלא את כל פרטי האשראי')
            return redirect('payment_page')

        # עדכון ההזמנות
        cart_items = CartItem.objects.filter(
            user=user,
            status='Reserved'
        )

        for item in cart_items:
            item.status = 'Paid'
            item.save()

        # שליחת מייל
        try:
           send_order_success_email(user)
           messages.success(request, 'התשלום בוצע בהצלחה ונשלח מייל אישור.')
        except Exception as e:
            messages.warning(request, f'התשלום בוצע, אבל שליחת המייל נכשלה: {e}')

        return redirect('paid_orders')

    return redirect('payment_page')


#דף מציג ההזמנות ששולמו
def paid_orders_view(request):
    user = _get_logged_in_user(request)

    if not user:
        return redirect('home')

    paid_orders = CartItem.objects.filter(
        user=user,
        status='Paid'
    ).select_related('package').order_by('-reserved_at')

    return render(request, 'users/paid_orders.html', {
        'paid_orders': paid_orders,
        'full_name': user.full_name,
        'user_role': user.role,
        'is_authenticated': True,
    })


def admin_users_list(request):
    user = _get_logged_in_user(request)
    if not user or user.role != 'admin':
        return render(request, 'error.html', {'status_code': 403}, status=403)

    users = User.objects.all().order_by('-id')
    return render(request, 'users/admin_users_list.html', {
        'users': users,
        'full_name': user.full_name,
        'user_role': user.role,
    })


@csrf_exempt
def admin_delete_user(request, user_id):
    user = _get_logged_in_user(request)
    if not user or user.role != 'admin':
        return JsonResponse({'error': 'forbidden'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'error': 'method_not_allowed'}, status=405)

    try:
        target_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'error': 'not_found'}, status=404)

    target_user.delete()
    return JsonResponse({'status': 'deleted'}, status=200)