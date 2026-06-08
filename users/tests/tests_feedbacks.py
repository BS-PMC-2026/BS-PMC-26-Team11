from datetime import timedelta
import json

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from users.models import User, Feedback, Package, CartItem


class FeedbackTestMixin:
    def login(self, user):
        session = self.client.session
        session['user_id'] = user.id
        session.save()

    def create_package(self):
        return Package.objects.create(
            name='Test Package',
            description='Test package',
            price=100,
            package_type='Tour',
            farm_area='Area A',
            capacity=10,
        )
    def create_paid_order(self, user):
        now = timezone.now()

        return CartItem.objects.create(
            user=user,
            package=self.package,
            package_name=self.package.name,
            quantity=1,
            status='Paid',
            reserved_at=now,
            expires_at=now + timezone.timedelta(minutes=15)
        )

    def make_second_feedback_later(self, first_feedback, second_feedback):
        now = timezone.now()
        Feedback.objects.filter(id=first_feedback.id).update(
            created_at=now - timedelta(minutes=1)
        )
        Feedback.objects.filter(id=second_feedback.id).update(
            created_at=now
        )
        first_feedback.refresh_from_db()
        second_feedback.refresh_from_db()


class FeedbackModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            full_name='Test User',
            email='test@example.com',
            password='hashedpassword',
            phone='0501234567',
            role='user',
        )

    def test_create_feedback(self):
        feedback = Feedback.objects.create(
            user=self.user,
            content='Great experience!',
            rating=5,
        )
        self.assertEqual(feedback.user.full_name, 'Test User')
        self.assertEqual(feedback.content, 'Great experience!')
        self.assertEqual(feedback.rating, 5)

    def test_feedback_default_rating(self):
        feedback = Feedback.objects.create(
            user=self.user,
            content='Test feedback',
        )
        self.assertEqual(feedback.rating, 5)

    def test_feedback_created_at_auto_set(self):
        feedback = Feedback.objects.create(
            user=self.user,
            content='Test',
            rating=4,
        )
        self.assertIsNotNone(feedback.created_at)
        self.assertLessEqual(
            (timezone.now() - feedback.created_at).total_seconds(),
            5,
        )


class AdminFeedbacksApiTests(FeedbackTestMixin, TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create(
            full_name='Admin User',
            email='admin@example.com',
            password='hashedpassword',
            phone='0501234567',
            role='admin',
        )
        self.regular_user = User.objects.create(
            full_name='Regular User',
            email='user@example.com',
            password='hashedpassword',
            phone='0509876543',
            role='user',
        )

    def test_non_admin_cannot_access(self):
        self.login(self.regular_user)

        response = self.client.get(reverse('admin_feedbacks_api'))

        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'forbidden')

    def test_unauthenticated_cannot_access(self):
        response = self.client.get(reverse('admin_feedbacks_api'))
        self.assertEqual(response.status_code, 403)

    def test_admin_can_access_empty_feedbacks(self):
        self.login(self.admin_user)

        response = self.client.get(reverse('admin_feedbacks_api'))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['feedbacks'], [])
        self.assertEqual(data['message'], 'No feedbacks found')

    def test_admin_can_get_feedbacks(self):
        Feedback.objects.create(
            user=self.regular_user,
            content='Great tour!',
            rating=5,
        )
        Feedback.objects.create(
            user=self.admin_user,
            content='Nice experience',
            rating=4,
        )
        self.login(self.admin_user)

        response = self.client.get(reverse('admin_feedbacks_api'))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['feedbacks']), 2)

    def test_feedbacks_ordered_by_date_descending(self):
        feedback1 = Feedback.objects.create(
            user=self.regular_user,
            content='First feedback',
            rating=3,
        )
        feedback2 = Feedback.objects.create(
            user=self.regular_user,
            content='Second feedback',
            rating=5,
        )
        self.make_second_feedback_later(feedback1, feedback2)
        self.login(self.admin_user)

        response = self.client.get(reverse('admin_feedbacks_api'))
        data = json.loads(response.content)

        self.assertEqual(data['feedbacks'][0]['content'], 'Second feedback')
        self.assertEqual(data['feedbacks'][1]['content'], 'First feedback')

    def test_feedback_data_structure(self):
        Feedback.objects.create(
            user=self.regular_user,
            content='Test content',
            rating=4,
        )
        self.login(self.admin_user)

        response = self.client.get(reverse('admin_feedbacks_api'))
        data = json.loads(response.content)

        feedback_data = data['feedbacks'][0]
        self.assertIn('id', feedback_data)
        self.assertIn('name', feedback_data)
        self.assertIn('content', feedback_data)
        self.assertIn('rating', feedback_data)
        self.assertIn('created_at', feedback_data)
        self.assertEqual(feedback_data['name'], 'Regular User')
        self.assertEqual(feedback_data['content'], 'Test content')
        self.assertEqual(feedback_data['rating'], 4)

    def test_only_get_method_allowed(self):
        self.login(self.admin_user)

        response = self.client.post(reverse('admin_feedbacks_api'))

        self.assertEqual(response.status_code, 405)


class AdminFeedbacksPageTests(FeedbackTestMixin, TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create(
            full_name='Admin User',
            email='admin@example.com',
            password='hashedpassword',
            phone='0501234567',
            role='admin',
        )
        self.regular_user = User.objects.create(
            full_name='Regular User',
            email='user@example.com',
            password='hashedpassword',
            phone='0509876543',
            role='user',
        )

    def test_non_admin_redirected_to_home(self):
        self.login(self.regular_user)

        response = self.client.get(reverse('admin_feedbacks_page'))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith('/'))

    def test_unauthenticated_redirected_to_home(self):
        response = self.client.get(reverse('admin_feedbacks_page'))
        self.assertEqual(response.status_code, 302)

    def test_admin_can_access_page(self):
        self.login(self.admin_user)

        response = self.client.get(reverse('admin_feedbacks_page'))

        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('feedbacks', content.lower())

    def test_page_contains_table_structure(self):
        self.login(self.admin_user)

        response = self.client.get(reverse('admin_feedbacks_page'))
        content = response.content.decode('utf-8')

        self.assertIn('feedbacks-table', content.lower())


class AdminFeedbackIntegrationTests(FeedbackTestMixin, TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create(
            full_name='Admin',
            email='admin@test.com',
            password='hashedpassword',
            phone='0501234567',
            role='admin',
        )
        self.user1 = User.objects.create(
            full_name='User One',
            email='user1@test.com',
            password='hashedpassword',
            phone='0501111111',
            role='user',
        )
        self.user2 = User.objects.create(
            full_name='User Two',
            email='user2@test.com',
            password='hashedpassword',
            phone='0502222222',
            role='user',
        )

    def test_multiple_feedbacks_from_different_users(self):
        Feedback.objects.create(
            user=self.user1,
            content='User 1 feedback',
            rating=5,
        )
        Feedback.objects.create(
            user=self.user2,
            content='User 2 feedback',
            rating=3,
        )
        self.login(self.admin_user)

        response = self.client.get(reverse('admin_feedbacks_api'))
        data = json.loads(response.content)

        self.assertEqual(len(data['feedbacks']), 2)
        names = [feedback['name'] for feedback in data['feedbacks']]
        self.assertIn('User One', names)
        self.assertIn('User Two', names)

    def test_feedbacks_match_database_records(self):
        feedback1 = Feedback.objects.create(
            user=self.user1,
            content='Feedback content 1',
            rating=5,
        )
        feedback2 = Feedback.objects.create(
            user=self.user2,
            content='Feedback content 2',
            rating=2,
        )
        self.make_second_feedback_later(feedback1, feedback2)
        self.login(self.admin_user)

        response = self.client.get(reverse('admin_feedbacks_api'))
        data = json.loads(response.content)

        self.assertEqual(data['feedbacks'][0]['id'], feedback2.id)
        self.assertEqual(data['feedbacks'][1]['id'], feedback1.id)



class SubmitFeedbackTests(FeedbackTestMixin, TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(
            full_name='Test User',
            email='user@test.com',
            password='hashedpassword',
            phone='0501234567',
            role='user',
        )
        self.package = self.create_package()

    def test_unauthenticated_user_cannot_submit(self):
        response = self.client.post(
            reverse('submit_feedback'),
            data=json.dumps({'content': 'Test feedback', 'rating': 5}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'authentication_required')

    def test_authenticated_user_without_paid_order_cannot_submit(self):
        self.login(self.user)

        response = self.client.post(
            reverse('submit_feedback'),
            data=json.dumps({'content': 'Test feedback', 'rating': 5}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'purchase_required')

    def test_missing_content_field(self):
        self.login(self.user)
        self.create_paid_order(self.user)

        response = self.client.post(
            reverse('submit_feedback'),
            data=json.dumps({'rating': 5}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'content_required')

    def test_missing_rating_field(self):
        self.login(self.user)
        self.create_paid_order(self.user)

        response = self.client.post(
            reverse('submit_feedback'),
            data=json.dumps({'content': 'Test feedback'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'rating_required')

    def test_empty_content_is_invalid(self):
        self.login(self.user)
        self.create_paid_order(self.user)

        response = self.client.post(
            reverse('submit_feedback'),
            data=json.dumps({'content': '   ', 'rating': 5}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'content_required')

    def test_invalid_rating_below_range(self):
        self.login(self.user)
        self.create_paid_order(self.user)

        response = self.client.post(
            reverse('submit_feedback'),
            data=json.dumps({'content': 'Test feedback', 'rating': 0}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'invalid_rating')

    def test_invalid_rating_above_range(self):
        self.login(self.user)
        self.create_paid_order(self.user)

        response = self.client.post(
            reverse('submit_feedback'),
            data=json.dumps({'content': 'Test feedback', 'rating': 6}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'invalid_rating')

    def test_invalid_rating_non_numeric(self):
        self.login(self.user)
        self.create_paid_order(self.user)

        response = self.client.post(
            reverse('submit_feedback'),
            data=json.dumps({'content': 'Test feedback', 'rating': 'invalid'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'invalid_rating')

    def test_successful_feedback_submission(self):
        self.login(self.user)
        self.create_paid_order(self.user)

        response = self.client.post(
            reverse('submit_feedback'),
            data=json.dumps({'content': 'Great experience!', 'rating': 5}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertEqual(data['name'], 'Test User')
        self.assertEqual(data['content'], 'Great experience!')
        self.assertEqual(data['rating'], 5)
        self.assertIn('id', data)
        self.assertIn('created_at', data)

    def test_feedback_saved_to_database(self):
        self.login(self.user)
        self.create_paid_order(self.user)
        initial_count = Feedback.objects.count()

        response = self.client.post(
            reverse('submit_feedback'),
            data=json.dumps({'content': 'Test feedback', 'rating': 4}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Feedback.objects.count(), initial_count + 1)

        feedback = Feedback.objects.latest('id')
        self.assertEqual(feedback.user.id, self.user.id)
        self.assertEqual(feedback.content, 'Test feedback')
        self.assertEqual(feedback.rating, 4)

    def test_only_post_method_allowed(self):
        self.login(self.user)
        self.create_paid_order(self.user)

        response = self.client.get(reverse('submit_feedback'))

        self.assertEqual(response.status_code, 405)

    def test_valid_ratings_1_to_5(self):
        self.login(self.user)

        for rating in range(1, 6):
            self.create_paid_order(self.user)

            response = self.client.post(
                reverse('submit_feedback'),
                data=json.dumps({
                    'content': f'Feedback with rating {rating}',
                    'rating': rating,
                }),
                content_type='application/json',
            )

            self.assertEqual(response.status_code, 201)
            data = json.loads(response.content)
            self.assertEqual(data['rating'], rating)

    def test_content_with_special_characters(self):
        self.login(self.user)
        self.create_paid_order(self.user)

        special_content = 'שלום! זה משוב עם תווים מיוחדים: <>&"'

        response = self.client.post(
            reverse('submit_feedback'),
            data=json.dumps({'content': special_content, 'rating': 5}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertEqual(data['content'], special_content)










#---------------------

class GetUserFeedbacksTests(FeedbackTestMixin, TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(
            full_name='Test User',
            email='user@test.com',
            password='hashedpassword',
            phone='0501234567',
            role='user',
        )
        self.other_user = User.objects.create(
            full_name='Other User',
            email='other@test.com',
            password='hashedpassword',
            phone='0509876543',
            role='user',
        )

    def test_unauthenticated_user_cannot_access(self):
        response = self.client.get(reverse('get_user_feedbacks'))

        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'authentication_required')

    def test_only_get_method_allowed(self):
        self.login(self.user)

        response = self.client.post(reverse('get_user_feedbacks'))

        self.assertEqual(response.status_code, 405)

    def test_user_can_get_empty_feedbacks(self):
        self.login(self.user)

        response = self.client.get(reverse('get_user_feedbacks'))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['feedbacks'], [])

    def test_user_can_get_their_feedbacks(self):
        Feedback.objects.create(
            user=self.user,
            content='My feedback 1',
            rating=5,
        )
        Feedback.objects.create(
            user=self.user,
            content='My feedback 2',
            rating=4,
        )
        Feedback.objects.create(
            user=self.other_user,
            content='Other user feedback',
            rating=3,
        )
        self.login(self.user)

        response = self.client.get(reverse('get_user_feedbacks'))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['feedbacks']), 2)
        contents = [feedback['content'] for feedback in data['feedbacks']]
        self.assertIn('My feedback 1', contents)
        self.assertIn('My feedback 2', contents)
        self.assertNotIn('Other user feedback', contents)

    def test_feedbacks_ordered_by_date_descending(self):
        feedback1 = Feedback.objects.create(
            user=self.user,
            content='First feedback',
            rating=5,
        )
        feedback2 = Feedback.objects.create(
            user=self.user,
            content='Second feedback',
            rating=4,
        )
        self.make_second_feedback_later(feedback1, feedback2)
        self.login(self.user)

        response = self.client.get(reverse('get_user_feedbacks'))
        data = json.loads(response.content)

        self.assertEqual(data['feedbacks'][0]['content'], 'Second feedback')
        self.assertEqual(data['feedbacks'][1]['content'], 'First feedback')

    def test_feedback_data_structure(self):
        Feedback.objects.create(
            user=self.user,
            content='Test feedback',
            rating=4,
        )
        self.login(self.user)

        response = self.client.get(reverse('get_user_feedbacks'))
        data = json.loads(response.content)

        feedback_data = data['feedbacks'][0]
        self.assertIn('id', feedback_data)
        self.assertIn('name', feedback_data)
        self.assertIn('content', feedback_data)
        self.assertIn('rating', feedback_data)
        self.assertIn('created_at', feedback_data)
        self.assertEqual(feedback_data['name'], 'Test User')


class FeedbacksPageTests(FeedbackTestMixin, TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(
            full_name='Test User',
            email='user@test.com',
            password='hashedpassword',
            phone='0501234567',
            role='user',
        )
        self.package = self.create_package()

    def test_authenticated_user_can_access_feedbacks_page(self):
        self.login(self.user)

        response = self.client.get(reverse('feedbacks_page'))

        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('feedback', content.lower())

    def test_unauthenticated_user_sees_auth_required_message(self):
        response = self.client.get(reverse('feedbacks_page'))

        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('התחברות', content)

    def test_paid_user_sees_feedback_form(self):
        self.login(self.user)
        self.create_paid_order(self.user)

        response = self.client.get(reverse('feedbacks_page'))
        content = response.content.decode('utf-8')

        self.assertIn('feedback-form', content.lower())
        self.assertIn('feedback-content', content.lower())
        self.assertIn('rating-picker', content.lower())
        self.assertIn('שלח משוב', content)




class ViewAllFeedbacksTests(FeedbackTestMixin, TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create(
            full_name='User One',
            email='user1@test.com',
            password='hashedpassword',
            phone='0501111111',
            role='user',
        )
        self.user2 = User.objects.create(
            full_name='User Two',
            email='user2@test.com',
            password='hashedpassword',
            phone='0502222222',
            role='user',
        )

    def test_unauthenticated_user_can_access(self):
        response = self.client.get(reverse('view_all_feedbacks'))
        self.assertEqual(response.status_code, 200)

    def test_authenticated_user_can_access(self):
        self.login(self.user1)

        response = self.client.get(reverse('view_all_feedbacks'))

        self.assertEqual(response.status_code, 200)

    def test_returns_empty_list_when_no_feedbacks(self):
        response = self.client.get(reverse('view_all_feedbacks'))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['feedbacks'], [])

    def test_returns_all_feedbacks(self):
        Feedback.objects.create(
            user=self.user1,
            content='Feedback 1',
            rating=5,
        )
        Feedback.objects.create(
            user=self.user2,
            content='Feedback 2',
            rating=4,
        )

        response = self.client.get(reverse('view_all_feedbacks'))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['feedbacks']), 2)

    def test_feedbacks_ordered_by_date_descending(self):
        feedback1 = Feedback.objects.create(
            user=self.user1,
            content='First feedback',
            rating=5,
        )
        feedback2 = Feedback.objects.create(
            user=self.user2,
            content='Second feedback',
            rating=4,
        )
        self.make_second_feedback_later(feedback1, feedback2)

        response = self.client.get(reverse('view_all_feedbacks'))
        data = json.loads(response.content)

        self.assertEqual(data['feedbacks'][0]['content'], 'Second feedback')
        self.assertEqual(data['feedbacks'][1]['content'], 'First feedback')

    def test_feedback_data_structure(self):
        Feedback.objects.create(
            user=self.user1,
            content='Test content',
            rating=3,
        )

        response = self.client.get(reverse('view_all_feedbacks'))
        data = json.loads(response.content)

        feedback_data = data['feedbacks'][0]
        self.assertIn('id', feedback_data)
        self.assertIn('name', feedback_data)
        self.assertIn('content', feedback_data)
        self.assertIn('rating', feedback_data)
        self.assertIn('created_at', feedback_data)
        self.assertEqual(feedback_data['name'], 'User One')
        self.assertEqual(feedback_data['content'], 'Test content')
        self.assertEqual(feedback_data['rating'], 3)

    def test_only_get_method_allowed(self):
        response = self.client.post(reverse('view_all_feedbacks'))
        self.assertEqual(response.status_code, 405)

        response = self.client.delete(reverse('view_all_feedbacks'))
        self.assertEqual(response.status_code, 405)

    def test_multiple_feedbacks_display_correctly(self):
        feedbacks_data = [
            ('User 1 feedback', 5),
            ('User 2 feedback', 4),
            ('User 3 feedback', 3),
            ('User 4 feedback', 2),
            ('User 5 feedback', 1),
        ]

        created_feedbacks = []
        for i, (content, rating) in enumerate(feedbacks_data):
            created_feedbacks.append(
                Feedback.objects.create(
                    user=self.user1 if i % 2 == 0 else self.user2,
                    content=content,
                    rating=rating,
                )
            )

        base_time = timezone.now()
        for i, feedback in enumerate(created_feedbacks):
            Feedback.objects.filter(id=feedback.id).update(
                created_at=base_time + timedelta(minutes=i)
            )

        response = self.client.get(reverse('view_all_feedbacks'))
        data = json.loads(response.content)

        self.assertEqual(len(data['feedbacks']), 5)
        self.assertEqual(data['feedbacks'][0]['content'], 'User 5 feedback')
        self.assertEqual(data['feedbacks'][4]['content'], 'User 1 feedback')

    def test_includes_user_name_not_id(self):
        Feedback.objects.create(
            user=self.user1,
            content='Test',
            rating=5,
        )

        response = self.client.get(reverse('view_all_feedbacks'))
        data = json.loads(response.content)

        self.assertEqual(data['feedbacks'][0]['name'], 'User One')
        self.assertNotIn('user_id', data['feedbacks'][0])

    def test_created_at_is_iso_format(self):
        Feedback.objects.create(
            user=self.user1,
            content='Test',
            rating=5,
        )

        response = self.client.get(reverse('view_all_feedbacks'))
        data = json.loads(response.content)

        created_at = data['feedbacks'][0]['created_at']
        self.assertRegex(created_at, r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}')


class AllFeedbacksPageTests(FeedbackTestMixin, TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(
            full_name='Test User',
            email='user@test.com',
            password='hashedpassword',
            phone='0501234567',
            role='user',
        )
        self.package = self.create_package()

    def test_unauthenticated_user_can_access_page(self):
        response = self.client.get(reverse('all_feedbacks_page'))

        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('feedbacks', content.lower())

    def test_authenticated_user_can_access_page(self):
        self.login(self.user)

        response = self.client.get(reverse('all_feedbacks_page'))

        self.assertEqual(response.status_code, 200)

    def test_page_contains_grid_view_container(self):
        response = self.client.get(reverse('all_feedbacks_page'))
        content = response.content.decode('utf-8')
        self.assertIn('feedbacks-grid', content.lower())

    def test_page_contains_table_view_container(self):
        response = self.client.get(reverse('all_feedbacks_page'))
        content = response.content.decode('utf-8')
        self.assertIn('feedbacks-table', content.lower())

    def test_paid_user_sees_add_feedback_button(self):
        self.login(self.user)
        self.create_paid_order(self.user)

        response = self.client.get(reverse('all_feedbacks_page'))
        content = response.content.decode('utf-8')

        self.assertIn('הוסף משוב', content)

    def test_logged_in_user_without_paid_order_sees_purchase_required_message(self):
        self.login(self.user)

        response = self.client.get(reverse('all_feedbacks_page'))
        content = response.content.decode('utf-8')

        self.assertIn('רכישת חבילה', content)
        self.assertNotIn('הוסף משוב', content)

    def test_unauthenticated_user_does_not_see_add_feedback_button(self):
        response = self.client.get(reverse('all_feedbacks_page'))
        content = response.content.decode('utf-8')

        self.assertNotIn('הוסף משוב', content)

    def test_page_loads_feedbacks_on_render(self):
        response = self.client.get(reverse('all_feedbacks_page'))
        content = response.content.decode('utf-8')
        self.assertIn('loadFeedbacks', content)

    def test_page_has_view_toggle_buttons(self):
        response = self.client.get(reverse('all_feedbacks_page'))
        content = response.content.decode('utf-8')
        self.assertIn('view-mode-toggle', content.lower())
        self.assertIn('תצוגת כרטיסים', content)
        self.assertIn('תצוגת טבלה', content)


class FeedbackSubmissionIntegrationTests(FeedbackTestMixin, TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(
            full_name='Test User',
            email='user@test.com',
            password='hashedpassword',
            phone='0501234567',
            role='user',
        )
        self.package = self.create_package()

    def test_complete_feedback_submission_flow(self):
        self.login(self.user)
        self.create_paid_order(self.user)

        response = self.client.post(
            reverse('submit_feedback'),
            data=json.dumps({'content': 'Great experience!', 'rating': 5}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)

        response = self.client.get(reverse('get_user_feedbacks'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['feedbacks']), 1)
        self.assertEqual(data['feedbacks'][0]['content'], 'Great experience!')
        self.assertEqual(data['feedbacks'][0]['rating'], 5)

    def test_multiple_users_feedbacks_are_separate(self):
        user2 = User.objects.create(
            full_name='Other User',
            email='other@test.com',
            password='hashedpassword',
            phone='0509876543',
            role='user',
        )
        self.create_paid_order(self.user)
        self.create_paid_order(user2)

        self.login(self.user)
        response = self.client.post(
            reverse('submit_feedback'),
            data=json.dumps({'content': 'User 1 feedback', 'rating': 5}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)

        self.login(user2)
        response = self.client.post(
            reverse('submit_feedback'),
            data=json.dumps({'content': 'User 2 feedback', 'rating': 3}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)

        self.login(self.user)
        response = self.client.get(reverse('get_user_feedbacks'))
        data = json.loads(response.content)
        self.assertEqual(len(data['feedbacks']), 1)
        self.assertEqual(data['feedbacks'][0]['content'], 'User 1 feedback')

        self.login(user2)
        response = self.client.get(reverse('get_user_feedbacks'))
        data = json.loads(response.content)
        self.assertEqual(len(data['feedbacks']), 1)
        self.assertEqual(data['feedbacks'][0]['content'], 'User 2 feedback')

    def test_all_feedbacks_visible_to_everyone(self):
        user2 = User.objects.create(
            full_name='Other User',
            email='other@test.com',
            password='hashedpassword',
            phone='0509876543',
            role='user',
        )
        Feedback.objects.create(
            user=self.user,
            content='User 1 feedback',
            rating=5,
        )
        Feedback.objects.create(
            user=user2,
            content='User 2 feedback',
            rating=3,
        )

        response = self.client.get(reverse('view_all_feedbacks'))
        data = json.loads(response.content)
        self.assertEqual(len(data['feedbacks']), 2)

        self.login(self.user)
        response = self.client.get(reverse('view_all_feedbacks'))
        data = json.loads(response.content)
        self.assertEqual(len(data['feedbacks']), 2)

        self.login(user2)
        response = self.client.get(reverse('view_all_feedbacks'))
        data = json.loads(response.content)
        self.assertEqual(len(data['feedbacks']), 2)

    def test_public_feedbacks_match_submitted_feedbacks(self):
        self.login(self.user)
        self.create_paid_order(self.user)

        response = self.client.post(
            reverse('submit_feedback'),
            data=json.dumps({'content': 'Great experience!', 'rating': 5}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)

        self.client.session.flush()
        response = self.client.get(reverse('view_all_feedbacks'))
        data = json.loads(response.content)

        self.assertEqual(len(data['feedbacks']), 1)
        self.assertEqual(data['feedbacks'][0]['content'], 'Great experience!')
        self.assertEqual(data['feedbacks'][0]['rating'], 5)
        self.assertEqual(data['feedbacks'][0]['name'], 'Test User')
