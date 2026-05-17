# Preserve data: Order -> CartItem, table Orders -> CartItems, columns aligned with story.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0013_order_model_and_orders_table'),
    ]

    operations = [
        migrations.AddField(
            model_name='package',
            name='reservation_minutes',
            field=models.PositiveIntegerField(
                db_column='ReservationMinutes',
                default=15,
                help_text='Minutes a user may hold this package in the cart without completing purchase.',
            ),
            preserve_default=False,
        ),
        migrations.RenameModel(
            old_name='Order',
            new_name='CartItem',
        ),
        migrations.AlterModelTable(
            name='CartItem',
            table='CartItems',
        ),
        migrations.RenameField(
            model_name='cartitem',
            old_name='created_at',
            new_name='reserved_at',
        ),
        migrations.RenameField(
            model_name='cartitem',
            old_name='reserved_until',
            new_name='expires_at',
        ),
        migrations.AlterField(
            model_name='cartitem',
            name='reserved_at',
            field=models.DateTimeField(db_column='ReservedAt'),
        ),
        migrations.AlterField(
            model_name='cartitem',
            name='expires_at',
            field=models.DateTimeField(db_column='ExpiresAt'),
        ),
        migrations.AlterField(
            model_name='cartitem',
            name='status',
            field=models.CharField(
                choices=[
                    ('Reserved', 'Reserved'),
                    ('Cancelled', 'Cancelled'),
                    ('Expired', 'Expired'),
                ],
                db_column='Status',
                default='Reserved',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='cartitem',
            name='user',
            field=models.ForeignKey(
                db_column='UserId',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='cart_items',
                to='users.user',
            ),
        ),
        migrations.AlterField(
            model_name='cartitem',
            name='package',
            field=models.ForeignKey(
                db_column='PackageId',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='cart_items',
                to='users.package',
            ),
        ),
        migrations.AlterField(
            model_name='cartitem',
            name='package_name',
            field=models.CharField(blank=True, db_column='PackageName', max_length=120),
        ),
    ]
