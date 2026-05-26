from datetime import timedelta

from django.utils import timezone

from .exceptions import TimeExpired

CANCELLATION_WINDOW = timedelta(minutes=15)


def cancellation_deadline(reserved_at):
    """End of the period in which cancellation is allowed (based on cart ReservedAt)."""
    return reserved_at + CANCELLATION_WINDOW


def is_cancellation_window_open(reserved_at, *, now=None):
    """Return True if cancellation is still allowed for a cart row with the given ReservedAt."""
    if now is None:
        now = timezone.now()
    return now <= cancellation_deadline(reserved_at)


def assert_cancellation_window_open(reserved_at, *, now=None):
    """
    Ensure cancellation is still allowed.
    Raises TimeExpired if the cancellation period has passed.
    """
    if not is_cancellation_window_open(reserved_at, now=now):
        raise TimeExpired
