from django.test import TestCase
from django.urls import reverse


class FrontendButtonTests(TestCase):

    def test_cta_buttons_render_correctly(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)

        html = response.content.decode("utf-8")

        self.assertIn("cta-buttons", html)
        self.assertIn("cta-button", html)
        self.assertIn("הירשמו עכשיו", html)
        self.assertIn("לחצו לקטלוג המלא", html)

    def test_cta_buttons_have_correct_links(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)

        html = response.content.decode("utf-8")

        self.assertIn('href="/users/signup/"', html)
        self.assertIn('href="/packages/"', html)

    def test_hover_effects_exist(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)

        html = response.content.decode("utf-8")

        self.assertIn(":hover", html)
        self.assertIn("transition", html)
        self.assertIn("transform", html)

    def test_cta_buttons_are_visible(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)

        html = response.content.decode("utf-8")

        self.assertIn(".cta-buttons", html)
        self.assertIn("display: flex", html)
        self.assertIn("flex-wrap: wrap", html)

    def test_responsive_css_exists_for_screen_sizes(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)

        html = response.content.decode("utf-8")

        self.assertIn("@media", html)
        self.assertIn("max-width", html)

    def test_login_button_state_is_enabled_by_default(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)

        html = response.content.decode("utf-8")

        self.assertIn('type="button"', html)
        self.assertIn("site-navbar__login", html)
        self.assertNotIn('site-navbar__login" disabled', html)

    def test_modal_submit_button_exists_and_is_enabled(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)

        html = response.content.decode("utf-8")

        self.assertIn('type="submit"', html)
        self.assertIn("modal-submit", html)
        self.assertNotIn('modal-submit" disabled', html)