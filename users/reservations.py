from django.utils import timezone

from .models import CartItem


def release_expired_reservations():
    """Mark reserved cart rows as Expired when past ExpiresAt (releases capacity)."""
    now = timezone.now()
    CartItem.objects.filter(status='Reserved', expires_at__lte=now).update(status='Expired')
