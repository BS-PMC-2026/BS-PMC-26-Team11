from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.hashers import make_password

from users.models import User, Package


class DeletePackageIntegrationTests(TestCase):
    def setUp(self):
        self.normal_user = User.objects.create(
            full_name="Normal User",
            email="user@test.com",
            password=make_password("User12345"),
            phone="0500000001",
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

    def login_custom_user(self, user):
        session = self.client.session
        session["user_id"] = user.id
        session["role"] = user.role
        session["full_name"] = user.full_name
        session.save()

    def test_regular_user_delete_package_api_returns_403(self):
        self.login_custom_user(self.normal_user)

        url = reverse("delete_package", args=[self.package.id])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 403)

        self.assertTrue(
            Package.objects.filter(id=self.package.id).exists()
        )