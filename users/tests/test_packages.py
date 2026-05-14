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
        CartItem.objects.create(
            user=self.user,
            package=self.package,
            reserved_until=timezone.now() + timedelta(minutes=20)
        )

        response = self.client.post(reverse('add_to_cart', args=[self.package.id]))

        self.assertRedirects(response, reverse('packages') + '?error=capacity_full')
        self.assertEqual(CartItem.objects.count(), 1)

    def test_add_to_cart_allows_when_previous_reservation_expired(self):
        self._login_session()
        expired_item = CartItem.objects.create(
            user=self.user,
            package=self.package,
            reserved_until=timezone.now() - timedelta(minutes=5)
        )

        response = self.client.post(reverse('add_to_cart', args=[self.package.id]))

        self.assertRedirects(response, reverse('packages') + '?success=reserved')
        self.assertEqual(CartItem.objects.count(), 2)
        active_items = CartItem.objects.filter(package=self.package, reserved_until__gt=timezone.now())
        self.assertEqual(active_items.count(), 1)
        self.assertTrue(active_items.first().reserved_until > timezone.now())
