from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from users.models import Package


class PackageShareFeatureTests(TestCase):
    def setUp(self):
        self.package = Package.objects.create(
            name="סדנת הכנת רטבים חריפים",
            description="למדו להכין רטבים חריפים ביתיים",
            price=Decimal("180.00"),
            capacity=8,
            is_available=True,
        )

    def test_packages_page_loads_successfully(self):
        response = self.client.get(reverse("packages"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "פעילויות וסיורים")

    def test_share_button_is_displayed_for_package(self):
        response = self.client.get(reverse("packages"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="share-button"')
        self.assertContains(response, "שתף")

    def test_share_button_contains_package_data(self):
        response = self.client.get(reverse("packages"))

        package_detail_url = reverse("package_detail", args=[self.package.id])

        self.assertContains(response, f'data-name="{self.package.name}"')
        self.assertContains(response, 'data-price="180"')
        self.assertContains(response, f'data-url="{package_detail_url}"')

    def test_share_modal_exists_on_packages_page(self):
        response = self.client.get(reverse("packages"))

        self.assertContains(response, 'id="shareModal"')
        self.assertContains(response, "שתף חבילה")
        self.assertContains(response, "WhatsApp")
        self.assertContains(response, "Telegram")
        self.assertContains(response, "Facebook")
        self.assertContains(response, "X / Twitter")
        self.assertContains(response, "העתק קישור")

    def test_share_javascript_exists(self):
        response = self.client.get(reverse("packages"))

        self.assertContains(response, "selectedShareData")
        self.assertContains(response, "navigator.share")
        self.assertContains(response, "https://wa.me/?text=")
        self.assertContains(response, "https://t.me/share/url")
        self.assertContains(response, "https://www.facebook.com/sharer/sharer.php")
        self.assertContains(response, "navigator.clipboard.writeText")