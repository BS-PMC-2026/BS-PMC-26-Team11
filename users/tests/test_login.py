from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.hashers import make_password, check_password
from users.models import User


class LoginTests(TestCase):

    def setUp(self):
        self.user = User.objects.create(
            full_name="Test User",
            email="test@example.com",
            phone="0501234567",
            password=make_password("StrongPass1!"),
            role="user"
        )

    # 1️⃣ בדיקה שפונקציית אימות סיסמה מחזירה true עבור סיסמה נכונה
    def test_check_password_returns_true_for_correct_password(self):
        self.assertTrue(check_password("StrongPass1!", self.user.password))

    # 2️⃣ בדיקה שמחזירה false עבור סיסמה שגויה
    def test_check_password_returns_false_for_wrong_password(self):
        self.assertFalse(check_password("WrongPass1!", self.user.password))

    # 3️⃣ בדיקה שפונקציה שמחפשת משתמש מחזירה None / לא קיים אם המשתמש לא קיים
    def test_find_user_returns_none_if_not_exists(self):
        user = User.objects.filter(email="notexists@example.com").first()
        self.assertIsNone(user)

    # 4️⃣ בדיקה שפונקציה שמייצרת Session פועלת נכון
    def test_login_creates_session_correctly(self):
        response = self.client.post(reverse('login'), {
            'email': 'test@example.com',
            'password': 'StrongPass1!'
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session['user_id'], self.user.id)
        self.assertEqual(self.client.session['role'], self.user.role)

    # בונוס: התחברות נכשלת עם סיסמה שגויה
    def test_login_fails_with_wrong_password(self):
        response = self.client.post(reverse('login'), {
            'email': 'test@example.com',
            'password': 'WrongPass1!'
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'שגויים')

    # בונוס: התחברות נכשלת אם המשתמש לא קיים
    def test_login_fails_when_user_not_found(self):
        response = self.client.post(reverse('login'), {
            'email': 'notexists@example.com',
            'password': 'StrongPass1!'
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'שגויים')