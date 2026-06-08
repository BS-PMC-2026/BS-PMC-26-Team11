from django.db import models
from django.utils import timezone
from io import BytesIO
import qrcode
from django.core.files.base import ContentFile

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
    image_url = models.CharField(max_length=500, default='', db_column='image_url')  
    image = models.ImageField(upload_to='packages/', blank=True, null=True, db_column='Image')
    capacity = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)


    reservation_minutes = models.PositiveIntegerField(
        default=15,
        db_column='ReservationMinutes',
        help_text='Minutes a user may hold this package in the cart without completing purchase.',
    )

    tour_datetime = models.DateTimeField(
        null=True,
        blank=True,
        db_column='TourDateTime',
        help_text='Date and time of the tour.',
    )

    cancellation_hours = models.PositiveIntegerField(
        default=24,
        db_column='CancellationHours',
        help_text='How many hours before the tour the user can cancel.',
    )

    def __str__(self):
        return self.name

    def active_reservations(self):
        now = timezone.now()

        return self.cart_items.filter(
            models.Q(status='Reserved', expires_at__gt=now) |
            models.Q(status='Paid')
        ).count()
    
    
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


class CartItem(models.Model):
    """Cart / reservation row in ``CartItems`` (UserId, PackageId, ReservedAt, ExpiresAt, Status)."""

    class Meta:
        db_table = 'CartItems'

    STATUS_CHOICES = [
    ('Reserved', 'Reserved'),
    ('Paid', 'Paid'),
    ('Cancelled', 'Cancelled'),
    ('Expired', 'Expired'),
]

    tour_access_code = models.CharField(
    max_length=6,
    blank=True,
    null=True,
    db_column='TourAccessCode'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cart_items',
        db_column='UserId',
    )
    quantity = models.PositiveIntegerField(default=1)
    package = models.ForeignKey(
        Package,
        on_delete=models.CASCADE,
        related_name='cart_items',
        db_column='PackageId',
    )
    package_name = models.CharField(max_length=120, blank=True, db_column='PackageName')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Reserved',
        db_column='Status',
    )
    reserved_at = models.DateTimeField(db_column='ReservedAt')
    expires_at = models.DateTimeField(db_column='ExpiresAt')

    def __str__(self):
        return f"{self.user.full_name} - {self.package.name}"

    def is_active(self):
        return self.status == 'Reserved' and self.expires_at > timezone.now()




class PepperType(models.Model):
    class Meta:
        db_table = 'PepperTypes'

    name = models.CharField(max_length=120, db_column='Name')
    description = models.TextField(db_column='Description')
    spiciness_level = models.PositiveSmallIntegerField(default=1, db_column='SpicinessLevel')
    origin = models.CharField(max_length=120, blank=True, db_column='Origin')
    usage = models.TextField(blank=True, db_column='Usage')
    fun_fact = models.TextField(blank=True, db_column='FunFact')
    image = models.ImageField(upload_to='peppers/', blank=True, null=True, db_column='Image')
    qr_code_value = models.CharField(max_length=50, unique=True, blank=True, db_column='QRCodeValue')
    is_active = models.BooleanField(default=True, db_column='IsActive')
    created_at = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='UpdatedAt')
    guide_text = models.TextField(
    blank=True,
    default=''
    )
    qr_code_image = models.ImageField(
        upload_to='pepper_qr/',
        blank=True,
        null=True,
        db_column='QRCodeImage'
    )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        updated_fields = []

        if not self.qr_code_value:
            self.qr_code_value = f"PEPPER:{self.id}"
            updated_fields.append('qr_code_value')

        if self.qr_code_value and not self.qr_code_image:
            qr = qrcode.make(self.qr_code_value)

            buffer = BytesIO()
            qr.save(buffer, format='PNG')

            file_name = f'pepper_{self.id}_qr.png'

            self.qr_code_image.save(
                file_name,
                ContentFile(buffer.getvalue()),
                save=False
            )

            updated_fields.append('qr_code_image')

        if updated_fields:
            super().save(update_fields=updated_fields)

    def __str__(self):
        return self.name
    


class Feedback(models.Model):
    class Meta:
        db_table = 'FEEDBACKS'

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='feedbacks',
        db_column='user_id',
    )
    content = models.TextField(db_column='content')
    rating = models.PositiveSmallIntegerField(default=5, db_column='rating')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')

    def __str__(self):
        return f"{self.user.full_name} - {self.rating}★"
