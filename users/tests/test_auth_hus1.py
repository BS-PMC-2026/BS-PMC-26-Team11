from django.contrib.auth.hashers import check_password, make_password
from django.test import TestCase
from django.urls import reverse

from users.models import User


class AuthFrontendUnitTests(TestCase):
    def test_login_required_fields_and_cta_render(self):
        response = self.client.get(reverse('login'))
        self.assertContains(response, 'aria-label="מסך התחברות"')
        self.assertContains(response, 'name="email"')
        self.assertContains(response, 'name="password"')
        self.assertContains(response, 'required')
        self.assertContains(response, 'data-testid="login-cta"')
        self.assertContains(response, 'Login')
        self.assertContains(response, 'auth-submit:hover')

    def test_signup_required_fields_and_cta_render(self):
        response = self.client.get(reverse('signup'))
        self.assertContains(response, 'aria-label="מסך הרשמה"')
        for field in ['full_name', 'email', 'phone', 'password', 'confirm_password']:
            self.assertContains(response, f'name="{field}"')
        self.assertContains(response, 'required')
        self.assertContains(response, 'data-testid="signup-cta"')
        self.assertContains(response, 'Sign Up')
        self.assertContains(response, 'auth-submit:hover')

    def test_invalid_login_input_has_visual_feedback(self):
        response = self.client.post(reverse('login'), {'email': 'bad-email', 'password': ''})
        self.assertContains(response, 'is-invalid')
        self.assertContains(response, 'יש להזין אימייל בפורמט תקין')
        self.assertContains(response, 'יש להזין סיסמה')

    def test_invalid_signup_email_has_visual_feedback(self):
        response = self.client.post(reverse('signup'), {
            'full_name': 'Test User',
            'email': 'invalid-email',
            'phone': '0501234567',
            'password': 'StrongPass1!',
            'confirm_password': 'StrongPass1!',
        })
        self.assertContains(response, 'is-invalid')
        self.assertContains(response, 'יש להזין אימייל בפורמט תקין')

    def test_password_confirmation_mismatch_has_visual_feedback(self):
        response = self.client.post(reverse('signup'), {
            'full_name': 'Test User',
            'email': 'match@example.com',
            'phone': '0501234567',
            'password': 'StrongPass1!',
            'confirm_password': 'DifferentPass1!',
        })
        self.assertContains(response, 'is-invalid')
        self.assertContains(response, 'הסיסמאות אינן תואמות')

    def test_switching_between_login_and_signup_is_clear(self):
        login_response = self.client.get(reverse('login'))
        signup_response = self.client.get(reverse('signup'))
        self.assertContains(login_response, reverse('signup'))
        self.assertContains(signup_response, reverse('login'))


class AuthBackendUnitTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            full_name='Regular User',
            email='user@example.com',
            phone='0501234567',
            password=make_password('StrongPass1!'),
            role='user',
        )

    def test_successful_login(self):
        response = self.client.post(reverse('login'), {
            'email': 'user@example.com',
            'password': 'StrongPass1!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session['user_id'], self.user.id)

    def test_failed_login_with_invalid_credentials(self):
        response = self.client.post(reverse('login'), {
            'email': 'user@example.com',
            'password': 'WrongPass1!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'אימייל או סיסמה שגויים')

    def test_duplicate_email_prevention(self):
        response = self.client.post(reverse('signup'), {
            'full_name': 'Duplicate User',
            'email': 'user@example.com',
            'phone': '0507654321',
            'password': 'StrongPass1!',
            'confirm_password': 'StrongPass1!',
        })
        self.assertEqual(User.objects.filter(email='user@example.com').count(), 1)
        self.assertContains(response, 'האימייל כבר קיים במערכת')

    def test_password_hashing_correctness(self):
        self.client.post(reverse('signup'), {
            'full_name': 'Hash User',
            'email': 'hash@example.com',
            'phone': '0501112222',
            'password': 'StrongPass1!',
            'confirm_password': 'StrongPass1!',
        })
        user = User.objects.get(email='hash@example.com')
        self.assertNotEqual(user.password, 'StrongPass1!')
        self.assertTrue(check_password('StrongPass1!', user.password))

    def test_user_role_assignment(self):
        self.assertEqual(self.user.role, 'user')
        User.objects.all().delete()
        self.client.post(reverse('signup'), {
            'full_name': 'First Admin',
            'email': 'first@example.com',
            'phone': '0502223333',
            'password': 'StrongPass1!',
            'confirm_password': 'StrongPass1!',
        })
        self.assertEqual(User.objects.get(email='first@example.com').role, 'admin')


class AuthIntegrationTests(TestCase):
    def test_full_signup_flow_from_ui_to_database(self):
        response = self.client.post(reverse('signup'), {
            'full_name': 'Flow User',
            'email': 'flow@example.com',
            'phone': '0503334444',
            'password': 'StrongPass1!',
            'confirm_password': 'StrongPass1!',
        })
        self.assertRedirects(response, reverse('signup_success'))
        self.assertTrue(User.objects.filter(email='flow@example.com').exists())

    def test_login_flow_with_database_authentication_and_session(self):
        user = User.objects.create(
            full_name='Login Flow',
            email='loginflow@example.com',
            phone='0504445555',
            password=make_password('StrongPass1!'),
            role='user',
        )
        response = self.client.post(reverse('login'), {
            'email': 'loginflow@example.com',
            'password': 'StrongPass1!',
        })
        self.assertRedirects(response, reverse('packages'))
        self.assertEqual(self.client.session['user_id'], user.id)
        self.assertEqual(self.client.session['role'], 'user')

    def test_role_based_redirection(self):
        admin = User.objects.create(
            full_name='Admin User',
            email='admin@example.com',
            phone='0505556666',
            password=make_password('StrongPass1!'),
            role='admin',
        )
        regular = User.objects.create(
            full_name='Regular User',
            email='regular@example.com',
            phone='0506667777',
            password=make_password('StrongPass1!'),
            role='user',
        )
        admin_response = self.client.post(reverse('login'), {'email': admin.email, 'password': 'StrongPass1!'})
        self.assertRedirects(admin_response, reverse('promotions'))
        self.client.get(reverse('logout'))
        user_response = self.client.post(reverse('login'), {'email': regular.email, 'password': 'StrongPass1!'})
        self.assertRedirects(user_response, reverse('packages'))

    def test_server_errors_are_displayed_in_ui(self):
        response = self.client.post(reverse('login'), {
            'email': 'missing@example.com',
            'password': 'StrongPass1!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'אימייל או סיסמה שגויים')
        self.assertContains(response, 'form-alert')
