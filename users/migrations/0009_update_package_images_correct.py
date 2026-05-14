from django.db import migrations


def update_package_images_correct(apps, schema_editor):
    Package = apps.get_model('users', 'Package')
    
    image_updates = [
        ('גילוי החווה', '/static/images/farm-discovery.jpeg'),
        ('הרפתקה משפחתית', '/static/images/images2.jpeg'),
        ('טיול הזוגות', '/static/images/images3.webp'),
        ('קורס בישול חקלאי', '/static/images/images4.jpeg'),
        ('סיור בעלי החי', '/static/images/images5.jpeg'),
        ('הצטיינות חקלאית', '/static/images/images6.jpeg'),
        ('פסטיבל התרבות החקלאית', '/static/images/images7.jpeg'),
    ]
    
    for package_name, image_path in image_updates:
        Package.objects.filter(name=package_name).update(image_url=image_path)


def reverse_update(apps, schema_editor):
    # Revert to placeholder URLs if needed
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_update_package_images'),
    ]

    operations = [
        migrations.RunPython(update_package_images_correct, reverse_update),
    ]
