from django.test import TestCase
from django.urls import reverse

from users.models import User, Package


class NavbarHoverTests(TestCase):

    def setUp(self):
        self.user = User.objects.create(
            full_name="דניאל כהן",
            email="daniel@example.com",
            phone="0501234567",
            password="Test123!",
            role="user"
        )

    def login_by_session(self, user):
        session = self.client.session
        session["user_id"] = user.id
        session["full_name"] = user.full_name
        session["user_role"] = user.role
        session.save()

    def test_navbar_buttons_render_correctly(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

        html = response.content.decode("utf-8")

        self.assertIn("דף הבית", html)
        self.assertIn("סיורים", html)
        self.assertIn("גלריה", html)
        self.assertIn("אודות", html)


    def test_hover_effect_css_exists(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

        html = response.content.decode("utf-8")

        self.assertIn(":hover", html)
        self.assertIn("transition", html)
        self.assertIn("transform", html)
        self.assertIn("background-color", html)

    def test_active_nav_class_exists(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

        html = response.content.decode("utf-8")

        self.assertIn("is-active", html)

    def test_navbar_text_color_is_consistent(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

        html = response.content.decode("utf-8")

        self.assertIn(".site-navbar__links", html)
        self.assertIn("color: #303030", html)


    def test_logo_is_displayed_correctly(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

        html = response.content.decode("utf-8")

        self.assertIn("הדינרים", html)
        self.assertIn("site-navbar__brand-flame", html)
        self.assertIn("<svg", html)

    def test_responsive_navbar_layout_exists(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

        html = response.content.decode("utf-8")

        self.assertIn("@media (max-width: 900px)", html)
        self.assertIn("flex-wrap", html)

    def test_guest_navbar_state(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

        html = response.content.decode("utf-8")

        self.assertIn("התחברות", html)
        self.assertNotIn("התנתקות", html)
        self.assertNotIn("שלום דניאל כהן", html)

    def test_logged_in_username_retrieval(self):
        self.login_by_session(self.user)

        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

        html = response.content.decode("utf-8")

        self.assertIn("שלום", html)
        self.assertIn("דניאל כהן", html)

    def test_user_navbar_state(self):
        self.login_by_session(self.user)

        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

        html = response.content.decode("utf-8")

        self.assertIn("שלום", html)
        self.assertIn("דניאל כהן", html)
        self.assertIn("התנתקות", html)
        self.assertIn("site-navbar__cart", html)

    def test_admin_navbar_state(self):
        admin = User.objects.create(
            full_name="Admin User",
            email="admin@example.com",
            phone="0509999999",
            password="Admin123!",
            role="admin"
        )

        self.login_by_session(admin)

        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

        html = response.content.decode("utf-8")

        self.assertIn("שלום", html)
        self.assertIn("Admin User", html)
        self.assertIn("התנתקות", html)

    def test_cart_count_retrieval_empty_cart(self):
        self.login_by_session(self.user)

        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

        html = response.content.decode("utf-8")

        self.assertIn("site-navbar__cart", html)


    def test_navbar_updates_after_login(self):
        response_guest = self.client.get(reverse("home"))
        self.assertContains(response_guest, "התחברות")

        self.login_by_session(self.user)

        response_user = self.client.get(reverse("home"))
        self.assertContains(response_user, "שלום")
        self.assertContains(response_user, "דניאל כהן")
        self.assertContains(response_user, "התנתקות")

    def test_navbar_updates_after_logout(self):
        self.login_by_session(self.user)

        response_user = self.client.get(reverse("home"))
        self.assertContains(response_user, "התנתקות")

        response_logout = self.client.get(reverse("logout"))
        self.assertIn(response_logout.status_code, [200, 302])

        response_guest = self.client.get(reverse("home"))
        self.assertContains(response_guest, "התחברות")

    def test_correct_navbar_state_for_guest_user_admin(self):
        guest_response = self.client.get(reverse("home"))
        self.assertContains(guest_response, "התחברות")
        self.assertNotContains(guest_response, "התנתקות")

        self.login_by_session(self.user)

        user_response = self.client.get(reverse("home"))
        self.assertContains(user_response, "שלום")
        self.assertContains(user_response, "דניאל כהן")
        self.assertContains(user_response, "התנתקות")

        admin = User.objects.create(
            full_name="Admin User",
            email="admin2@example.com",
            phone="0508888888",
            password="Admin123!",
            role="admin"
        )

        self.login_by_session(admin)

        admin_response = self.client.get(reverse("home"))
        self.assertContains(admin_response, "שלום")
        self.assertContains(admin_response, "Admin User")
        self.assertContains(admin_response, "התנתקות")


class NavbarIntegrationTests(TestCase):

    def setUp(self):
        self.user = User.objects.create(
            full_name="דניאל כהן",
            email="daniel@example.com",
            phone="0501234567",
            password="Test123!",
            role="user"
        )

        self.package = Package.objects.create(
            name="סיור בחווה + טעימות",
            description="סיור בחווה",
            package_type="סיור",
            farm_area="אזור א",
            price=80,
            capacity=10,
            is_available=True,
            reservation_minutes=30,
            image_url=""
        )

    def login_by_session(self, user):
        session = self.client.session
        session["user_id"] = user.id
        session["full_name"] = user.full_name
        session["user_role"] = user.role
        session.save()

    def test_cart_icon_count_updates_after_adding_item(self):
        self.login_by_session(self.user)

        response_add = self.client.post(reverse("add_to_cart", args=[self.package.id]))
        self.assertIn(response_add.status_code, [200, 302])

        response = self.client.get(reverse("packages"))
        self.assertEqual(response.status_code, 200)

        html = response.content.decode("utf-8")

        self.assertIn("site-navbar__cart", html)
        self.assertIn("site-navbar__badge", html)
        self.assertIn("side-cart", html)