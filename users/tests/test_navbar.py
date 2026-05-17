from django.test import TestCase
from django.urls import reverse


class NavbarHoverTests(TestCase):

    def test_navbar_buttons_render_correctly(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)

        html = response.content.decode("utf-8")

        self.assertIn("דף הבית", html)
        self.assertIn("סיורים", html)
        self.assertIn("גלריה", html)
        self.assertIn("אודות", html)

    def test_navbar_links_have_correct_urls(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)

        html = response.content.decode("utf-8")

        self.assertIn('data-nav-key="home"', html)
        self.assertIn('data-nav-key="tours"', html)
        self.assertIn('data-nav-key="gallery"', html)
        self.assertIn('data-nav-key="about"', html)

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