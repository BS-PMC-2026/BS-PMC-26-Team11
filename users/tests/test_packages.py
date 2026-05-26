from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.hashers import make_password

from users.models import User, Package, CartItem


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
            is_available=True,
            reservation_minutes=15,
        )

    def _login_session(self):
        session = self.client.session
        session['user_id'] = self.user.id
        session['full_name'] = self.user.full_name
        session.save()

    def test_add_to_cart_requires_authentication(self):
        response = self.client.post(reverse('add_to_cart', args=[self.package.id]))
        self.assertRedirects(response, reverse('home'))
        self.assertEqual(CartItem.objects.count(), 0)

    def test_add_to_cart_checks_package_availability(self):
        self.package.is_available = False
        self.package.save()
        self._login_session()

        response = self.client.post(reverse('add_to_cart', args=[self.package.id]))

        self.assertRedirects(response, reverse('packages') + '?error=not_available')
        self.assertEqual(CartItem.objects.count(), 0)

    def test_add_to_cart_checks_available_capacity(self):
        self._login_session()
        now = timezone.now()
        CartItem.objects.create(
            user=self.user,
            package=self.package,
            package_name=self.package.name,
            reserved_at=now,
            expires_at=now + timedelta(minutes=20),
        )

        response = self.client.post(reverse('add_to_cart', args=[self.package.id]))

        self.assertRedirects(response, reverse('packages') + '?error=capacity_full')
        self.assertEqual(CartItem.objects.count(), 1)

    def test_add_to_cart_allows_when_previous_reservation_expired(self):
        self._login_session()
        now = timezone.now()
        CartItem.objects.create(
            user=self.user,
            package=self.package,
            package_name=self.package.name,
            reserved_at=now - timedelta(hours=1),
            expires_at=now - timedelta(minutes=30),
            status='Reserved',
        )

        response = self.client.post(reverse('add_to_cart', args=[self.package.id]))

        self.assertRedirects(response, reverse('packages') + '?success=reserved&minutes=15')
        self.assertEqual(CartItem.objects.count(), 2)
        active_items = CartItem.objects.filter(package=self.package, expires_at__gt=timezone.now(), status='Reserved')
        self.assertEqual(active_items.count(), 1)

    def test_add_to_cart_sets_expires_from_reservation_minutes(self):
        self._login_session()
        self.package.reservation_minutes = 45
        self.package.save()
        before = timezone.now()
        response = self.client.post(reverse('add_to_cart', args=[self.package.id]))
        self.assertRedirects(response, reverse('packages') + '?success=reserved&minutes=45')
        row = CartItem.objects.get(package=self.package, status='Reserved')
        self.assertEqual((row.expires_at - row.reserved_at).total_seconds(), 45 * 60)
        self.assertGreaterEqual(row.reserved_at, before)
        self.assertLessEqual(row.reserved_at, timezone.now())




    def test_cancel_order_belongs_to_logged_in_user_returns_403(self):
        other_user = User.objects.create(
            full_name='Other User',
            email='other@example.com',
            phone='0509999999',
            password=make_password('StrongPass1!'),
            role='user'
        )
        now = timezone.now()
        order = CartItem.objects.create(
            user=other_user,
            package=self.package,
            package_name=self.package.name,
            reserved_at=now,
            expires_at=now + timedelta(minutes=10),
        )
        self._login_session()

        response = self.client.delete(reverse('cancel_user_package', args=[order.id]))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json().get('error'), 'forbidden')
        order.refresh_from_db()
        self.assertEqual(order.status, 'Reserved')

    def test_expired_reservation_marked_expired_releases_capacity_logic(self):
        now = timezone.now()
        row = CartItem.objects.create(
            user=self.user,
            package=self.package,
            package_name=self.package.name,
            reserved_at=now - timedelta(hours=2),
            expires_at=now - timedelta(minutes=1),
            status='Reserved',
        )
        self.assertEqual(self.package.available_capacity(), 1)
        from users.reservations import release_expired_reservations
        release_expired_reservations()
        row.refresh_from_db()
        self.assertEqual(row.status, 'Expired')

    def test_admin_can_save_package_reservation_minutes(self):
        admin = User.objects.create(
            full_name='Admin',
            email='adminres@example.com',
            phone='0501111112',
            password=make_password('StrongPass1!'),
            role='admin',
        )
        session = self.client.session
        session['user_id'] = admin.id
        session['full_name'] = admin.full_name
        session.save()

        response = self.client.post(
            reverse('package_reservation_admin'),
            {f'reservation_minutes_{self.package.id}': '42'},
        )
        self.assertRedirects(response, reverse('package_reservation_admin') + '?success=saved')
        self.package.refresh_from_db()
        self.assertEqual(self.package.reservation_minutes, 42)
