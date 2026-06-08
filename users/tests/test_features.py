import json
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.db import models
from django.db.models import NOT_PROVIDED

from users.models import User, Package, CartItem, Feedback


def model_has_field(model, field_name):
    return any(field.name == field_name for field in model._meta.fields)


def fill_required_fields(model, data):
    """
    Adds safe default values for required fields that were not provided.
    This makes the tests safer if the team added required fields later.
    """
    for field in model._meta.fields:
        if field.primary_key or field.auto_created:
            continue

        if field.name in data:
            continue

        if field.null:
            continue

        if field.default is not NOT_PROVIDED:
            continue

        if isinstance(field, models.CharField):
            data[field.name] = "test"
        elif isinstance(field, models.TextField):
            data[field.name] = "test text"
        elif isinstance(field, models.EmailField):
            data[field.name] = "test@example.com"
        elif isinstance(field, models.DecimalField):
            data[field.name] = Decimal("100.00")
        elif isinstance(field, models.IntegerField):
            data[field.name] = 1
        elif isinstance(field, models.BooleanField):
            data[field.name] = True
        elif isinstance(field, models.DateTimeField):
            data[field.name] = timezone.now()
        elif isinstance(field, models.DateField):
            data[field.name] = timezone.now().date()
        elif isinstance(field, models.TimeField):
            data[field.name] = timezone.now().time()

    return data


def create_test_user(email="user@example.com", role="user"):
    data = {}

    if model_has_field(User, "email"):
        data["email"] = email
    if model_has_field(User, "password"):
        data["password"] = "123456"
    if model_has_field(User, "full_name"):
        data["full_name"] = "Test User"
    if model_has_field(User, "role"):
        data["role"] = role
    if model_has_field(User, "phone"):
        data["phone"] = "0500000000"

    data = fill_required_fields(User, data)
    return User.objects.create(**data)


def create_test_package(name="Test Package", price=Decimal("100.00"), capacity=10):
    data = {}

    if model_has_field(Package, "name"):
        data["name"] = name
    if model_has_field(Package, "description"):
        data["description"] = "Test package description"
    if model_has_field(Package, "price"):
        data["price"] = price
    if model_has_field(Package, "capacity"):
        data["capacity"] = capacity
    if model_has_field(Package, "is_available"):
        data["is_available"] = True
    if model_has_field(Package, "image_url"):
        data["image_url"] = ""

    data = fill_required_fields(Package, data)
    return Package.objects.create(**data)


def create_cart_item(user, package, status="Reserved", quantity=1):
    data = {
        "user": user,
        "package": package,
    }

    if model_has_field(CartItem, "status"):
        data["status"] = status
    if model_has_field(CartItem, "expires_at"):
        data["expires_at"] = timezone.now() + timezone.timedelta(minutes=30)
    if model_has_field(CartItem, "quantity"):
        data["quantity"] = quantity
    if model_has_field(CartItem, "package_name"):
        data["package_name"] = package.name
    if model_has_field(CartItem, "price"):
        data["price"] = package.price

    data = fill_required_fields(CartItem, data)
    return CartItem.objects.create(**data)


class MohamadPackageShareTests(TestCase):
    def setUp(self):
        self.user = create_test_user()
        self.package = create_test_package(
            name="סדנת הכנת רטבים חריפים",
            price=Decimal("180.00"),
        )

        session = self.client.session
        session["user_id"] = self.user.id
        session.save()

    def test_packages_page_has_share_button(self):
        response = self.client.get(reverse("packages"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "share-button")
        self.assertContains(response, "שתף")

    def test_packages_page_has_share_modal_and_social_options(self):
        response = self.client.get(reverse("packages"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "shareModal")
        self.assertContains(response, "WhatsApp")
        self.assertContains(response, "Telegram")
        self.assertContains(response, "Facebook")
        self.assertContains(response, "X / Twitter")
        self.assertContains(response, "העתק קישור")

    def test_share_button_contains_package_data(self):
        response = self.client.get(reverse("packages"))
        package_detail_url = reverse("package_detail", args=[self.package.id])

        self.assertContains(response, f'data-name="{self.package.name}"')
        self.assertContains(response, f'data-url="{package_detail_url}"')


class MohamadCartTests(TestCase):
    def setUp(self):
        self.user = create_test_user()
        self.package = create_test_package(
            name="סדנת הכנת רטבים חריפים",
            price=Decimal("88.00"),
        )
        self.suggested_package = create_test_package(
            name="סיור בחווה + טעימות",
            price=Decimal("300.00"),
        )

        session = self.client.session
        session["user_id"] = self.user.id
        session.save()

        self.cart_item = create_cart_item(
            user=self.user,
            package=self.package,
            status="Reserved",
            quantity=1,
        )

    def test_cart_drawer_exists_on_packages_page(self):
        response = self.client.get(reverse("packages"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "cart-overlay")
        self.assertContains(response, "side-cart")
        self.assertContains(response, "sideCartList")
        self.assertContains(response, "סל הקניות")

    def test_cart_suggestions_section_exists(self):
        response = self.client.get(reverse("packages"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "cart-suggestions-section")
        self.assertContains(response, "אולי תאהב גם")

    def test_cart_drawer_exists_on_all_feedbacks_page_too(self):
        response = self.client.get(reverse("all_feedbacks_page"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "cart-overlay")
        self.assertContains(response, "side-cart")
        self.assertContains(response, "סל הקניות")

    def test_increase_cart_item_updates_quantity_without_creating_new_row(self):
        url = reverse("increase_cart_item", args=[self.cart_item.id])

        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.cart_item.refresh_from_db()

        self.assertEqual(data["status"], "updated")
        self.assertEqual(data["quantity"], 2)
        self.assertEqual(self.cart_item.quantity, 2)
        self.assertEqual(CartItem.objects.filter(user=self.user, package=self.package).count(), 1)
        self.assertEqual(Decimal(str(data["item_total"])), Decimal("176.0"))

    def test_decrease_cart_item_updates_quantity(self):
        self.cart_item.quantity = 3
        self.cart_item.save()

        url = reverse("decrease_cart_item", args=[self.cart_item.id])

        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.cart_item.refresh_from_db()

        self.assertEqual(data["status"], "updated")
        self.assertEqual(data["quantity"], 2)
        self.assertEqual(self.cart_item.quantity, 2)
        self.assertEqual(Decimal(str(data["item_total"])), Decimal("176.0"))

    def test_decrease_cart_item_deletes_when_quantity_is_one(self):
        self.cart_item.quantity = 1
        self.cart_item.save()

        url = reverse("decrease_cart_item", args=[self.cart_item.id])

        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(data["status"], "deleted")
        self.assertFalse(CartItem.objects.filter(id=self.cart_item.id).exists())

    def test_remove_cart_item_deletes_item(self):
        url = reverse("remove_cart_item", args=[self.cart_item.id])

        response = self.client.delete(url)

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(data["status"], "deleted")
        self.assertFalse(CartItem.objects.filter(id=self.cart_item.id).exists())


class MohamadFeedbackPermissionTests(TestCase):
    def setUp(self):
        self.user = create_test_user(email="buyer@example.com")
        self.package = create_test_package(
            name="חבילת בדיקה",
            price=Decimal("120.00"),
        )

        session = self.client.session
        session["user_id"] = self.user.id
        session.save()

    def test_user_without_paid_order_cannot_submit_feedback(self):
        payload = {
            "content": "the best",
            "rating": 5,
        }

        response = self.client.post(
            reverse("submit_feedback"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Feedback.objects.filter(user=self.user).exists())

    def test_user_with_paid_order_can_submit_feedback(self):
        create_cart_item(
            user=self.user,
            package=self.package,
            status="Paid",
            quantity=1,
        )

        payload = {
            "content": "the best",
            "rating": 5,
        }

        response = self.client.post(
            reverse("submit_feedback"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(Feedback.objects.filter(user=self.user, content="the best").exists())


class MohamadNavbarTests(TestCase):
    def setUp(self):
        self.user = create_test_user()

        session = self.client.session
        session["user_id"] = self.user.id
        session.save()

    def test_all_feedbacks_navbar_uses_shared_navbar(self):
        response = self.client.get(reverse("all_feedbacks_page"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "site-navbar")
        self.assertContains(response, "משובים")

    def test_external_pepper_link_exists_in_navbar(self):
        response = self.client.get(reverse("packages"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "פלפלים")
        self.assertContains(response, 'target="_blank"')
        self.assertContains(response, 'rel="noopener noreferrer"')