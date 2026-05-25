from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.hashers import make_password

from users.models import User, Package, CartItem


class CancelPackageIntegrationTests(TestCase):

    def setUp(self):
        self.normal_user = User.objects.create(
            full_name="Normal User",
            email="user@test.com",
            password=make_password("User12345"),
            phone="0500000001",
            role="user",
        )

        self.other_user = User.objects.create(
            full_name="Other User",
            email="other@test.com",
            password=make_password("Other12345"),
            phone="0500000002",
            role="user",
        )

        self.package = Package.objects.create(
            name="Test Package",
            description="Test package description",
            package_type="סיור מודרך",
            farm_area="חווה ראשית",
            price=100,
            capacity=10,
        )

        now = timezone.now()

        self.order = CartItem.objects.create(
            user=self.other_user,
            package=self.package,
            package_name=self.package.name,
            reserved_at=now,
            expires_at=now + timedelta(minutes=15),
            status="Reserved",
        )

    def login_custom_user(self, user):
        session = self.client.session
        session["user_id"] = user.id
        session["role"] = user.role
        session["full_name"] = user.full_name
        session.save()

    def test_regular_user_cannot_cancel_another_users_order(self):
        self.login_custom_user(self.normal_user)

        url = reverse("cancel_user_package", args=[self.order.id])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 403)

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "Reserved")