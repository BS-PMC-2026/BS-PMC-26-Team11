from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0011_discount'),
    ]

    operations = [
        migrations.AddField(
            model_name='discount',
            name='promotion_mode',
            field=models.CharField(
                choices=[('percentage', 'אחוז הנחה'), ('sale_price', 'מחיר מבצע ידני')],
                default='percentage',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='discount',
            name='sale_price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True),
        ),
        migrations.AlterField(
            model_name='discount',
            name='discount_percentage',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
    ]
