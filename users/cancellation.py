from datetime import timedelta

from django.utils import timezone

from .exceptions import TimeExpired

CANCELLATION_WINDOW = timedelta(minutes=15)


def cancellation_deadline(created_at):
    """End of the period in which cancellation is allowed (based on order Created_At)."""
    return created_at + CANCELLATION_WINDOW


def is_cancellation_window_open(created_at, *, now=None):
    """Return True if cancellation is still allowed for an order with the given creation time."""
    if now is None:
        now = timezone.now()
    return now <= cancellation_deadline(created_at)


def assert_cancellation_window_open(created_at, *, now=None):
    """
    Ensure cancellation is still allowed.
    Raises TimeExpired if the cancellation period has passed.
    """
    if not is_cancellation_window_open(created_at, now=now):
        raise TimeExpired
