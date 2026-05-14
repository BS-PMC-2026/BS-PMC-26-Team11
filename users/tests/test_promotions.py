from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.hashers import make_password

from users.models import User, Package, Discount


class PromotionManagementTests(TestCase):

    def setUp(self):
        self.admin_user = User.objects.create(
            full_name='Admin User',
            email='admin@example.com',
            phone='0501111111',
            password=make_password('AdminPass1!'),
            role='admin'
        )
        self.regular_user = User.objects.create(
            full_name='Regular User',
            email='user@example.com',
            phone='0502222222',
            password=make_password('UserPass1!'),
            role='user'
        )
        self.package = Package.objects.create(
            name='Farm Promo',
            description='מבצע על חבילה',
            price='120.00',
            package_type='ביקור משפחות',
            farm_area='החווה הירוקה',
            capacity=10,
            is_available=True
        )

    def _login_as(self, user):
        session = self.client.session
        session['user_id'] = user.id
        session['full_name'] = user.full_name
        session['role'] = user.role
        session.save()

    def test_admin_can_access_promotions_page(self):
        self._login_as(self.admin_user)

        response = self.client.get(reverse('promotions'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ניהול מבצעים')

    def test_non_admin_is_redirected_from_promotions_page(self):
        self._login_as(self.regular_user)

        response = self.client.get(reverse('promotions'))

        self.assertRedirects(response, reverse('home'))

    def test_admin_can_create_promotion(self):
        self._login_as(self.admin_user)
        start_date = timezone.localdate()
        end_date = start_date + timedelta(days=7)

        response = self.client.post(reverse('promotions'), {
            'package_id': self.package.id,
            'promotion_mode': 'percentage',
            'discount_percentage': '20',
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
        })

        self.assertRedirects(response, reverse('promotions') + '?success=created')
        self.assertEqual(Discount.objects.count(), 1)

        promotion = Discount.objects.first()
        self.assertEqual(promotion.package, self.package)
        self.assertEqual(promotion.promotion_mode, Discount.PromotionMode.PERCENTAGE)
        self.assertEqual(promotion.discount_percentage, 20)
        self.assertEqual(promotion.start_date, start_date)
        self.assertEqual(promotion.end_date, end_date)
        self.assertTrue(promotion.is_active())

    def test_invalid_discount_percentage_shows_error(self):
        self._login_as(self.admin_user)
        start_date = timezone.localdate()
        end_date = start_date + timedelta(days=3)

        response = self.client.post(reverse('promotions'), {
            'package_id': self.package.id,
            'promotion_mode': 'percentage',
            'discount_percentage': '150',
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
        })

        self.assertContains(response, 'יש להזין אחוז הנחה חוקי בין 1 ל-100.')
        self.assertEqual(Discount.objects.count(), 0)

    def test_invalid_date_range_shows_error(self):
        self._login_as(self.admin_user)
        start_date = timezone.localdate()
        end_date = start_date - timedelta(days=1)

        response = self.client.post(reverse('promotions'), {
            'package_id': self.package.id,
            'promotion_mode': 'percentage',
            'discount_percentage': '15',
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
        })

        self.assertContains(response, 'תאריך ההתחלה חייב להיות לפני או שווה לתאריך הסיום.')
        self.assertEqual(Discount.objects.count(), 0)

    def test_admin_can_create_sale_price_promotion(self):
        self._login_as(self.admin_user)
        start_date = timezone.localdate()
        end_date = start_date + timedelta(days=7)

        response = self.client.post(reverse('promotions'), {
            'package_id': self.package.id,
            'promotion_mode': 'sale_price',
            'sale_price': '99.00',
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
        })

        self.assertRedirects(response, reverse('promotions') + '?success=created')
        self.assertEqual(Discount.objects.count(), 1)
        promotion = Discount.objects.first()
        self.assertEqual(promotion.promotion_mode, Discount.PromotionMode.SALE_PRICE)
        self.assertIsNone(promotion.discount_percentage)
        self.assertEqual(promotion.sale_price, Decimal('99.00'))
        self.package.refresh_from_db()
        self.assertEqual(self.package.get_discounted_price(), Decimal('99.00'))

    def test_sale_price_must_be_strictly_below_original(self):
        self._login_as(self.admin_user)
        start_date = timezone.localdate()
        end_date = start_date + timedelta(days=7)

        response = self.client.post(reverse('promotions'), {
            'package_id': self.package.id,
            'promotion_mode': 'sale_price',
            'sale_price': '120.00',
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
        })

        self.assertContains(response, 'מחיר המבצע חייב להיות נמוך ממחיר החבילה המקורי.')
        self.assertEqual(Discount.objects.count(), 0)
