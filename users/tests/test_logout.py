from django.test import TestCase, Client
from django.urls import reverse

class LogoutViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_logout_view_clears_session_and_redirects(self):
        session = self.client.session
        session['user_id'] = 1
        session['role'] = 'user'
        session['full_name'] = 'Mohamad'
        session.save()

        response = self.client.get(reverse('logout'))

        self.assertRedirects(response, reverse('home'))

        session = self.client.session
        self.assertIsNone(session.get('user_id'))
        self.assertIsNone(session.get('role'))
        self.assertIsNone(session.get('full_name'))

        self.assertEqual(
            response['Cache-Control'],
            'no-cache, no-store, must-revalidate, private'
        )
        self.assertEqual(response['Pragma'], 'no-cache')
        self.assertEqual(response['Expires'], '0')