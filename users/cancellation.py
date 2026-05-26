from datetime import timedelta

from django.utils import timezone

from .exceptions import TimeExpired

CANCELLATION_WINDOW = timedelta(minutes=15)


def cancellation_deadline(reserved_at):
    """
    End of the period in which cancellation is allowed.
    """
    return reserved_at + CANCELLATION_WINDOW


def is_cancellation_window_open(reserved_at, *, now=None, is_admin=False):
    """
    Return True if cancellation is still allowed.

    Admin users are always allowed to cancel, even after the time window passed.
    """
    if is_admin:
        return True

    if now is None:
        now = timezone.now()

    return now <= cancellation_deadline(reserved_at)


def assert_cancellation_window_open(reserved_at, *, now=None, is_admin=False):
    """
    Ensure cancellation is still allowed.

    Raises TimeExpired if the cancellation period has passed.
    Admin users bypass the time check.
    """
    if not is_cancellation_window_open(reserved_at, now=now, is_admin=is_admin):
        raise TimeExpired

    return True
