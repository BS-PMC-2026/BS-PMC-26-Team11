from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.hashers import make_password

from users.models import User, Package, Order


class PackageBookingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            full_name='Package User',
            email='packageuser@example.com',
            phone='0501234567',
            password=make_password('StrongPass1!'),
            role='user'
        )
        self.package = Package.objects.create(
            name='Farm Discovery',
            description='ביקור מודרך בחווה עם פעילויות חקלאיות.',
            price='199.00',
            package_type='ביקור משפחות',
            farm_area='החווה הירוקה',
            capacity=1,
            is_available=True
        )

    def _login_session(self):
        session = self.client.session
        session['user_id'] = self.user.id
        session['full_name'] = self.user.full_name
        session.save()

    def test_add_to_cart_requires_authentication(self):
        response = self.client.post(reverse('add_to_cart', args=[self.package.id]))
        self.assertRedirects(response, reverse('home'))
        self.assertEqual(Order.objects.count(), 0)

    def test_add_to_cart_checks_package_availability(self):
        self.package.is_available = False
        self.package.save()
        self._login_session()

        response = self.client.post(reverse('add_to_cart', args=[self.package.id]))

        self.assertRedirects(response, reverse('packages') + '?error=not_available')
        self.assertEqual(Order.objects.count(), 0)

    def test_add_to_cart_checks_available_capacity(self):
        self._login_session()
        Order.objects.create(
            user=self.user,
            package=self.package,
            reserved_until=timezone.now() + timedelta(minutes=20)
        )

        response = self.client.post(reverse('add_to_cart', args=[self.package.id]))

        self.assertRedirects(response, reverse('packages') + '?error=capacity_full')
        self.assertEqual(Order.objects.count(), 1)

    def test_add_to_cart_allows_when_previous_reservation_expired(self):
        self._login_session()
        Order.objects.create(
            user=self.user,
            package=self.package,
            reserved_until=timezone.now() - timedelta(minutes=5)
        )

        response = self.client.post(reverse('add_to_cart', args=[self.package.id]))

        self.assertRedirects(response, reverse('packages') + '?success=reserved')
        self.assertEqual(Order.objects.count(), 2)
        active_items = Order.objects.filter(package=self.package, reserved_until__gt=timezone.now())
        self.assertEqual(active_items.count(), 1)
        self.assertTrue(active_items.first().reserved_until > timezone.now())

    def test_cancel_order_within_allowed_window(self):
        self._login_session()
        order = Order.objects.create(
            user=self.user,
            package=self.package,
            package_name=self.package.name,
            reserved_until=timezone.now() + timedelta(minutes=10),
        )

        response = self.client.delete(reverse('cancel_user_package', args=[order.id]))
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, 'Cancelled')

    def test_cancel_order_after_allowed_window_returns_400_time_expired(self):
        self._login_session()
        order = Order.objects.create(
            user=self.user,
            package=self.package,
            package_name=self.package.name,
            reserved_until=timezone.now() + timedelta(minutes=10),
        )
        Order.objects.filter(id=order.id).update(created_at=timezone.now() - timedelta(minutes=16))
        order.refresh_from_db()

        response = self.client.delete(reverse('cancel_user_package', args=[order.id]))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json().get('error'), 'TimeExpired')
        order.refresh_from_db()
        self.assertEqual(order.status, 'Reserved')

    def test_cancel_order_one_month_old_returns_400_no_db_change(self):
        self._login_session()
        order = Order.objects.create(
            user=self.user,
            package=self.package,
            package_name=self.package.name,
            reserved_until=timezone.now() + timedelta(minutes=10),
        )
        Order.objects.filter(id=order.id).update(created_at=timezone.now() - timedelta(days=35))
        order.refresh_from_db()

        response = self.client.delete(reverse('cancel_user_package', args=[order.id]))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json().get('error'), 'TimeExpired')
        order.refresh_from_db()
        self.assertEqual(order.status, 'Reserved')

    def test_cancel_order_belongs_to_logged_in_user_returns_403(self):
        other_user = User.objects.create(
            full_name='Other User',
            email='other@example.com',
            phone='0509999999',
            password=make_password('StrongPass1!'),
            role='user'
        )
        order = Order.objects.create(
            user=other_user,
            package=self.package,
            package_name=self.package.name,
            reserved_until=timezone.now() + timedelta(minutes=10),
        )
        self._login_session()

        response = self.client.delete(reverse('cancel_user_package', args=[order.id]))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json().get('error'), 'forbidden')
        order.refresh_from_db()
        self.assertEqual(order.status, 'Reserved')
