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
        return self.orders.filter(status='Reserved', reserved_until__gt=now).count()

    def available_capacity(self):
        return max(self.capacity - self.active_reservations(), 0)

    def get_active_discount(self):
        """Get the currently active discount for this package."""
        today = timezone.localdate()
        discount = self.discounts.filter(
            start_date__lte=today,
            end_date__gte=today
        ).first()
        return discount

    def get_discounted_price(self):
        """Calculate the discounted price if an active promotion exists."""
        discount = self.get_active_discount()
        if not discount:
            return None
        if discount.promotion_mode == Discount.PromotionMode.SALE_PRICE and discount.sale_price is not None:
            return round(discount.sale_price, 2)
        if discount.discount_percentage is not None:
            discount_amount = (self.price * discount.discount_percentage) / 100
            discounted = self.price - discount_amount
            return round(discounted, 2)
        return None

    def has_active_discount(self):
        """Check if this package has an active discount."""
        return self.get_active_discount() is not None


class Discount(models.Model):
    class PromotionMode(models.TextChoices):
        PERCENTAGE = 'percentage', 'אחוז הנחה'
        SALE_PRICE = 'sale_price', 'מחיר מבצע ידני'

    class Meta:
        db_table = 'Discounts'

    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='discounts', db_column='PackageId')
    promotion_mode = models.CharField(
        max_length=20,
        choices=PromotionMode.choices,
        default=PromotionMode.PERCENTAGE,
    )
    discount_percentage = models.PositiveSmallIntegerField(null=True, blank=True)
    sale_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.promotion_mode == self.PromotionMode.SALE_PRICE and self.sale_price is not None:
            return f"{self.package.name} - ₪{self.sale_price}"
        if self.discount_percentage is not None:
            return f"{self.package.name} - {self.discount_percentage}%"
        return f"{self.package.name} - מבצע"

    def promotion_label(self):
        if self.promotion_mode == self.PromotionMode.SALE_PRICE and self.sale_price is not None:
            return f"₪{self.sale_price} (מחיר מבצע)"
        if self.discount_percentage is not None:
            return f"{self.discount_percentage}%"
        return "—"

    def is_active(self):
        today = timezone.localdate()
        return self.start_date <= today <= self.end_date


class Order(models.Model):
    """User reservation / order row; stored in DB table ``Orders`` (Created_At column)."""

    class Meta:
        db_table = 'Orders'

    STATUS_CHOICES = [
        ('Reserved', 'Reserved'),
        ('Cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='orders')
    package_name = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Reserved')
    reserved_until = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True, db_column='Created_At')

    def __str__(self):
        return f"{self.user.full_name} - {self.package.name}"

    def is_active(self):
        return self.status == 'Reserved' and self.reserved_until > timezone.now()