from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from users.cancellation import (
    assert_cancellation_window_open,
    cancellation_deadline,
    is_cancellation_window_open,
)
from users.exceptions import TimeExpired


class CancellationWindowUnitTests(TestCase):

    def test_is_cancellation_window_open_returns_true_before_deadline(self):
        now = timezone.now()
        created_at = now - timedelta(minutes=5)
        self.assertTrue(is_cancellation_window_open(created_at, now=now))

    def test_is_cancellation_window_open_returns_false_after_deadline(self):
        now = timezone.now()
        created_at = now - timedelta(minutes=16)
        self.assertFalse(is_cancellation_window_open(created_at, now=now))

    def test_assert_cancellation_window_open_raises_time_expired(self):
        now = timezone.now()
        created_at = now - timedelta(days=35)
        with self.assertRaises(TimeExpired):
            assert_cancellation_window_open(created_at, now=now)

    def test_assert_cancellation_window_open_does_not_raise_when_valid(self):
        now = timezone.now()
        created_at = now - timedelta(minutes=1)
        assert_cancellation_window_open(created_at, now=now)

    def test_cancellation_deadline_is_created_plus_window(self):
        created = timezone.now()
        deadline = cancellation_deadline(created)
        self.assertEqual(deadline, created + timedelta(minutes=15))
<<<<<<< HEAD
    def test_admin_can_cancel_after_deadline(self):
      now = timezone.now()
      created_at = now - timedelta(days=35)

      result = assert_cancellation_window_open(
        created_at,
        now=now,
        is_admin=True
        )

      self.assertTrue(result)
=======
>>>>>>> origin/Shahed_hackton
