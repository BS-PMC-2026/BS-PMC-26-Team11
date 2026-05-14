from django.db import models
from django.utils import timezone


class User(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('user', 'User'),
    ]

    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')

    def __str__(self):
        return self.full_name


class Package(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    package_type = models.CharField(max_length=80)
    farm_area = models.CharField(max_length=80)
    image_url = models.URLField(blank=True)
    capacity = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def active_reservations(self):
        now = timezone.now()
        return self.cart_items.filter(reserved_until__gt=now).count()

    def available_capacity(self):
        return max(self.capacity - self.active_reservations(), 0)


class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items')
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='cart_items')
    package_name = models.CharField(max_length=120, blank=True)
    reserved_until = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.full_name} - {self.package.name}"

    def is_active(self):
        return self.reserved_until > timezone.now()