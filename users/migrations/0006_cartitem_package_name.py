from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_seed_packages'),
    ]

    operations = [
        migrations.AddField(
            model_name='cartitem',
            name='package_name',
            field=models.CharField(blank=True, max_length=120),
        ),
    ]
