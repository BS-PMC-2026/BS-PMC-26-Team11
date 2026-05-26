from django.test import TestCase
from django.contrib.auth.hashers import make_password

from users.models import User


class BackendAuthenticationTests(TestCase):

    def setUp(self):
        self.user = User.objects.create(
            email="test@example.com",
            password=make_password("TestPass123")
        )

    def test_login_page_opens(self):
        response = self.client.get("/users/login/")

        self.assertIn(response.status_code, [200, 302])

    def test_login_with_correct_credentials(self):
        response = self.client.post("/users/login/", {
            "email": "test@example.com",
            "password": "TestPass123"
        })

        self.assertIn(response.status_code, [200, 302])

        session = self.client.session
        self.assertEqual(session.get("user_id"), self.user.id)

    def test_login_with_wrong_password_fails(self):
        response = self.client.post("/users/login/", {
            "email": "test@example.com",
            "password": "WrongPassword"
        })

        self.assertIn(response.status_code, [200, 302])

        session = self.client.session
        self.assertIsNone(session.get("user_id"))

    def test_login_with_unknown_email_fails(self):
        response = self.client.post("/users/login/", {
            "email": "notfound@example.com",
            "password": "TestPass123"
        })

        self.assertIn(response.status_code, [200, 302])

        session = self.client.session
        self.assertIsNone(session.get("user_id"))