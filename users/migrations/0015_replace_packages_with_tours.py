from django.db import migrations


TOURS = [
    {
        'name': 'סדנת הכנת רטבים חריפים',
        'description': 'למדו להכין רטבים חריפים ביתיים מהחומרים הטובים ביותר',
        'price': '180.00',
        'package_type': '3 שעות',
        'farm_area': 'חוות החריף, גליל עליון',
        'image_url': '/static/images/tour-hot-sauce-peppers.png',
        'capacity': 8,
        'is_available': True,
        'reservation_minutes': 15,
    },
    {
        'name': 'סיור בחווה + טעימות',
        'description': 'סיור מודרך בחווה עם טעימות של זנים נדירים',
        'price': '80.00',
        'package_type': '2 שעות',
        'farm_area': 'חוות החריף, גליל עליון',
        'image_url': '/static/images/tour-single-red-pepper.png',
        'capacity': 15,
        'is_available': True,
        'reservation_minutes': 15,
    },
    {
        'name': 'סדנת גידול חריפים ביתי',
        'description': 'למדו לגדל חריפים בבית עם ערכת התחלה',
        'price': '150.00',
        'package_type': '2.5 שעות',
        'farm_area': 'חוות החריף, גליל עליון',
        'image_url': '/static/images/tour-two-red-peppers.png',
        'capacity': 0,
        'is_available': False,
        'reservation_minutes': 15,
    },
]


def replace_packages_with_tours(apps, schema_editor):
    Package = apps.get_model('users', 'Package')
    Package.objects.all().delete()
    for tour in TOURS:
        Package.objects.create(**tour)


def reverse_replace_packages_with_tours(apps, schema_editor):
    Package = apps.get_model('users', 'Package')
    Package.objects.filter(name__in=[tour['name'] for tour in TOURS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0014_reservation_minutes_cartitems_schema'),
    ]

    operations = [
        migrations.RunPython(replace_packages_with_tours, reverse_replace_packages_with_tours),
    ]
