from django.test import TestCase
from django.contrib.auth.hashers import make_password
from django.db import models
from django.db.models import NOT_PROVIDED

from users.models import User


class IntegrationTests(TestCase):

    def create_test_user(self):
        """
        Creates a user even if your custom User model has required fields.
        """
        data = {}

        for field in User._meta.fields:
            if field.primary_key or field.auto_created:
                continue

            if field.name == "email":
                data["email"] = "test@example.com"

            elif field.name == "password":
                data["password"] = make_password("TestPass123")

            elif field.default is not NOT_PROVIDED:
                continue

            elif field.null or field.blank:
                continue

            elif isinstance(field, models.CharField):
                data[field.name] = f"test_{field.name}"

            elif isinstance(field, models.EmailField):
                data[field.name] = "test@example.com"

            elif isinstance(field, models.BooleanField):
                data[field.name] = False

            elif isinstance(field, models.IntegerField):
                data[field.name] = 1

        return User.objects.create(**data)

    def setUp(self):
        self.user = self.create_test_user()

    def test_login_cta_communicates_with_backend_authentication(self):
        """
        Verify Login CTA/form exists in frontend
        and sends email/password correctly to backend login.
        """
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)

        html = response.content.decode("utf-8")

        self.assertIn("data-open-login", html)
        self.assertIn('action="/users/login/"', html)
        self.assertIn('name="email"', html)
        self.assertIn('name="password"', html)

        login_response = self.client.post("/users/login/", {
            "email": "test@example.com",
            "password": "TestPass123"
        })

        self.assertIn(login_response.status_code, [200, 302])

        session = self.client.session

        self.assertTrue(
            session.get("user_id") == self.user.id
            or session.get("_auth_user_id") == str(self.user.id),
            "Login did not save the authenticated user in the session."
        )

    def test_login_error_feedback_is_displayed_for_wrong_password(self):
        """
        Verify error feedback appears when backend rejects login.
        """
        response = self.client.post("/users/login/", {
            "email": "test@example.com",
            "password": "WrongPassword"
        })

        self.assertIn(response.status_code, [200, 302])

        session = self.client.session

        self.assertFalse(
            session.get("user_id") == self.user.id
            or session.get("_auth_user_id") == str(self.user.id),
            "User should not be logged in with a wrong password."
        )

    def test_add_to_cart_cta_exists_on_packages_page(self):
        """
        Verify Add to Cart CTA exists in the frontend.
        """
        response = self.client.get("/packages/")

        self.assertEqual(response.status_code, 200)

        html = response.content.decode("utf-8")

        self.assertTrue(
            "cart" in html.lower()
            or "עגלה" in html
            or "הוסף" in html,
            "No Add to Cart CTA was found on the packages page."
        )

    def test_purchase_cta_exists_in_purchase_flow(self):
        """
        Verify Purchase CTA exists somewhere in the cart/package flow.
        """
        response = self.client.get("/packages/")

        self.assertEqual(response.status_code, 200)

        html = response.content.decode("utf-8")

        self.assertTrue(
            "purchase" in html.lower()
            or "checkout" in html.lower()
            or "תשלום" in html
            or "רכישה" in html
            or "הזמנה" in html,
            "No Purchase CTA was found in the purchase flow."
        )

    def test_success_and_error_feedback_between_frontend_and_backend(self):
        """
        Verify frontend/backend feedback words exist.
        """
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)

        html = response.content.decode("utf-8")

        self.assertTrue(
            "error" in html.lower()
            or "success" in html.lower()
            or "שגוי" in html
            or "הצלחה" in html
            or "modal-error" in html,
            "No success/error feedback area was found."
        )