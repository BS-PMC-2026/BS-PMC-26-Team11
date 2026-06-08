from django.test import TestCase, Client
from django.urls import reverse
from users.models import User


class AdminUsersListTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create(
            full_name='Admin User',
            email='admin@example.com',
            password='hashed_password_admin',
            phone='0501234567',
            role='admin',
        )
        self.regular_user = User.objects.create(
            full_name='Regular User',
            email='user@example.com',
            password='hashed_password_user',
            phone='0509876543',
            role='user',
        )
        self.another_user = User.objects.create(
            full_name='Another User',
            email='another@example.com',
            password='hashed_password_another',
            phone='0505555555',
            role='user',
        )

    def test_non_admin_gets_403(self):
        session = self.client.session
        session['user_id'] = self.regular_user.id
        session.save()
        response = self.client.get(reverse('admin_users_list'))
        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_gets_403(self):
        response = self.client.get(reverse('admin_users_list'))
        self.assertEqual(response.status_code, 403)

    def test_admin_gets_200(self):
        session = self.client.session
        session['user_id'] = self.admin_user.id
        session.save()
        response = self.client.get(reverse('admin_users_list'))
        self.assertEqual(response.status_code, 200)

    def test_admin_sees_all_users(self):
        session = self.client.session
        session['user_id'] = self.admin_user.id
        session.save()
        response = self.client.get(reverse('admin_users_list'))
        self.assertContains(response, 'Regular User')
        self.assertContains(response, 'Another User')
        self.assertContains(response, 'Admin User')

    def test_users_ordered_by_id_descending(self):
        session = self.client.session
        session['user_id'] = self.admin_user.id
        session.save()
        response = self.client.get(reverse('admin_users_list'))
        users = response.context['users']
        user_ids = list(users.values_list('id', flat=True))
        self.assertEqual(user_ids, sorted(user_ids, reverse=True))

    def test_displayed_data_matches_db(self):
        session = self.client.session
        session['user_id'] = self.admin_user.id
        session.save()
        response = self.client.get(reverse('admin_users_list'))
        self.assertContains(response, self.regular_user.full_name)
        self.assertContains(response, self.regular_user.email)
        self.assertContains(response, self.another_user.full_name)
        self.assertContains(response, self.another_user.email)



class AdminDeleteUserTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create(
            full_name='Admin User',
            email='admin@example.com',
            password='hashed_password_admin',
            phone='0501234567',
            role='admin',
        )
        self.user_to_delete = User.objects.create(
            full_name='User To Delete',
            email='delete@example.com',
            password='hashed_password',
            phone='0501111111',
            role='user',
        )

    def test_non_admin_gets_403(self):
        regular_user = User.objects.create(
            full_name='Regular User',
            email='regular@example.com',
            password='hashed_password',
            phone='0509876543',
            role='user',
        )
        session = self.client.session
        session['user_id'] = regular_user.id
        session.save()
        response = self.client.post(
            reverse('admin_delete_user', args=[self.user_to_delete.id])
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(User.objects.filter(id=self.user_to_delete.id).exists())

    def test_unauthenticated_gets_403(self):
        response = self.client.post(
            reverse('admin_delete_user', args=[self.user_to_delete.id])
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(User.objects.filter(id=self.user_to_delete.id).exists())

    def test_admin_can_delete_user(self):
        session = self.client.session
        session['user_id'] = self.admin_user.id
        session.save()
        response = self.client.post(
            reverse('admin_delete_user', args=[self.user_to_delete.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(id=self.user_to_delete.id).exists())

    def test_delete_non_existent_user_returns_404(self):
        session = self.client.session
        session['user_id'] = self.admin_user.id
        session.save()
        response = self.client.post(
            reverse('admin_delete_user', args=[9999])
        )
        self.assertEqual(response.status_code, 404)

    def test_deleted_user_removed_from_db(self):
        session = self.client.session
        session['user_id'] = self.admin_user.id
        session.save()
        user_id = self.user_to_delete.id
        self.assertTrue(User.objects.filter(id=user_id).exists())
        self.client.post(reverse('admin_delete_user', args=[user_id]))
        self.assertFalse(User.objects.filter(id=user_id).exists())

    def test_only_post_allowed(self):
        session = self.client.session
        session['user_id'] = self.admin_user.id
        session.save()
        response = self.client.get(
            reverse('admin_delete_user', args=[self.user_to_delete.id])
        )
        self.assertEqual(response.status_code, 405)
        self.assertTrue(User.objects.filter(id=self.user_to_delete.id).exists())

    def test_delete_response_is_json(self):
        session = self.client.session
        session['user_id'] = self.admin_user.id
        session.save()
        response = self.client.post(
            reverse('admin_delete_user', args=[self.user_to_delete.id])
        )
        self.assertEqual(response['Content-Type'], 'application/json')
        data = response.json()
        self.assertEqual(data['status'], 'deleted')
