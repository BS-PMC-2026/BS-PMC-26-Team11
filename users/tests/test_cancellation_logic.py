from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from users.cancellation import assert_cancellation_window_open
from users.exceptions import TimeExpired


class CancellationLogicUnitTests(TestCase):
    def test_admin_can_cancel_even_after_cancellation_window_expired(self):
        reserved_at = timezone.now() - timedelta(hours=5)

        try:
            result = assert_cancellation_window_open(
                reserved_at,
                is_admin=True
            )
        except TimeExpired:
            self.fail("Admin should be allowed to cancel even after the time window expired.")

        self.assertTrue(result)

    def test_regular_user_cannot_cancel_after_cancellation_window_expired(self):
        reserved_at = timezone.now() - timedelta(hours=5)

        with self.assertRaises(TimeExpired):
            assert_cancellation_window_open(
                reserved_at,
                is_admin=False
            )