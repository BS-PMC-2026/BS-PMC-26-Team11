from django.test import TestCase
from django.contrib.auth.hashers import make_password, check_password
from django.db import IntegrityError
from django.urls import reverse
from users.models import User


class UserModelTests(TestCase):

    # 1️⃣ בדיקה: יצירת משתמש תקין
    def test_create_user_success(self):
        user = User.objects.create(
            full_name="Test User",
            email="test@example.com",
            phone="0501234567",
            password=make_password("StrongPass1!"),
            role="user"
        )

        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.full_name, "Test User")

    # 2️⃣ בדיקה: לא ניתן ליצור משתמש בלי אימייל
    def test_create_user_without_email(self):
        with self.assertRaises(Exception):
            User.objects.create(
                full_name="No Email",
                email=None,
                phone="0501234567",
                password=make_password("StrongPass1!"),
                role="user"
            )

    # 3️⃣ בדיקה: אימייל חייב להיות ייחודי
    def test_email_must_be_unique(self):
        User.objects.create(
            full_name="User One",
            email="test@example.com",
            phone="0501234567",
            password=make_password("StrongPass1!"),
            role="user"
        )

        with self.assertRaises(IntegrityError):
            User.objects.create(
                full_name="User Two",
                email="test@example.com",
                phone="0509999999",
                password=make_password("StrongPass1!"),
                role="user"
            )

    # 4️⃣ בדיקה: גיבוב סיסמה עובד
    def test_password_hashing(self):
        password = "StrongPass1!"
        hashed = make_password(password)

        self.assertNotEqual(password, hashed)
        self.assertTrue(check_password(password, hashed))

    # 5️⃣ בדיקה: ברירת מחדל role = user
    def test_default_role_is_user(self):
        user = User.objects.create(
            full_name="Default Role",
            email="default@example.com",
            phone="0501234567",
            password=make_password("StrongPass1!")
        )

        self.assertEqual(user.role, "user")

    # 6️⃣ טלפון לא תקין
    def test_signup_invalid_phone(self):
        response = self.client.post(reverse('signup'), {
            'full_name': 'Test User',
            'email': 'test_phone@example.com',
            'phone': '12345',
            'password': 'StrongPass1!',
            'confirm_password': 'StrongPass1!'
        })

        self.assertContains(response, 'טלפון')
        self.assertEqual(User.objects.count(), 0)

    # 7️⃣ סיסמאות לא תואמות
    def test_signup_password_mismatch(self):
        response = self.client.post(reverse('signup'), {
            'full_name': 'Test User',
            'email': 'test_pass@example.com',
            'phone': '0501234567',
            'password': 'StrongPass1!',
            'confirm_password': 'DifferentPass1!'
        })

        self.assertContains(response, 'סיסמה')
        self.assertEqual(User.objects.count(), 0)

    # 8️⃣ אימייל לא תקין
    def test_signup_invalid_email(self):
        response = self.client.post(reverse('signup'), {
            'full_name': 'Test User',
            'email': 'invalid-email',
            'phone': '0501234567',
            'password': 'StrongPass1!',
            'confirm_password': 'StrongPass1!'
        })

        self.assertContains(response, 'אימייל')
        self.assertEqual(User.objects.count(), 0)