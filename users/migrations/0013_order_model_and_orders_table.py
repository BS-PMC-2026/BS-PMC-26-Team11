# Safe migration: rename CartItem -> Order, physical table -> Orders, column -> Created_At

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0012_discount_promotion_mode'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='CartItem',
            new_name='Order',
        ),
        migrations.AlterModelTable(
            name='Order',
            table='Orders',
        ),
        migrations.AlterField(
            model_name='order',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_column='Created_At'),
        ),
        migrations.AlterField(
            model_name='order',
            name='user',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='orders',
                to='users.user',
            ),
        ),
        migrations.AlterField(
            model_name='order',
            name='package',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='orders',
                to='users.package',
            ),
        ),
    ]
