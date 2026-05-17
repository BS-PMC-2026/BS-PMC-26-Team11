from django.db import migrations


def create_initial_packages(apps, schema_editor):
    Package = apps.get_model('users', 'Package')
    
    packages_data = [
        {
            'name': 'גילוי החווה',
            'description': 'ביקור מודרך בחווה עם פעילויות חקלאיות וטיול בשדות הפלפלים.',
            'price': '199.00',
            'package_type': 'ביקור משפחות',
            'farm_area': 'החווה הירוקה',
            'image_url': 'https://via.placeholder.com/600x400.png?text=Farm+Discovery',
            'capacity': 10,
        },
        {
            'name': 'הרפתקה משפחתית',
            'description': 'חוויית משפחה עשירה בטבע ובמטבח החווה עם ארוחת צהריים טבעונית.',
            'price': '249.00',
            'package_type': 'פעילות משפחתית',
            'farm_area': 'עמק הפלפלים',
            'image_url': 'https://via.placeholder.com/600x400.png?text=Family+Adventure',
            'capacity': 5,
        },
        {
            'name': 'טיול הזוגות',
            'description': 'ערב רומנטי בחווה עם פיקניק זוגי וצפייה בשקיעה על השדות.',
            'price': '299.00',
            'package_type': 'ערב רומנטי',
            'farm_area': 'גן הפירות',
            'image_url': 'https://via.placeholder.com/600x400.png?text=Couples+Tour',
            'capacity': 8,
        },
        {
            'name': 'קורס בישול חקלאי',
            'description': 'קורס בישול עם שף מקומי תוך שימוש בתוצרי החווה הטריים ביותר.',
            'price': '349.00',
            'package_type': 'ורקשופ בישול',
            'farm_area': 'מטבח החווה',
            'image_url': 'https://via.placeholder.com/600x400.png?text=Cooking+Class',
            'capacity': 6,
        },
        {
            'name': 'סיור בעלי החי',
            'description': 'סיור משפחתי עם פעילויות טיפול בחיות חום ולימוד על כלל הבעלים.',
            'price': '179.00',
            'package_type': 'ביקור משפחות',
            'farm_area': 'אזור החיות',
            'image_url': 'https://via.placeholder.com/600x400.png?text=Animal+Tour',
            'capacity': 12,
        },
        {
            'name': 'הצטיינות חקלאית',
            'description': 'סדנה מקיפה ללומדים על חקלאות בר קיימא וטכניקות חדישות בתחום.',
            'price': '329.00',
            'package_type': 'סדנה חינוכית',
            'farm_area': 'חלקת הניסויים',
            'image_url': 'https://via.placeholder.com/600x400.png?text=Agriculture+Workshop',
            'capacity': 7,
        },
        {
            'name': 'פסטיבל התרבות החקלאית',
            'description': 'חגיגה שנתית עם מוסיקה חיה, אומנות מקומית ומטעמים מהחווה.',
            'price': '199.00',
            'package_type': 'פסטיבל תרבות',
            'farm_area': 'כל השטח',
            'image_url': 'https://via.placeholder.com/600x400.png?text=Culture+Festival',
            'capacity': 15,
        },
    ]
    
    for pkg_data in packages_data:
        Package.objects.get_or_create(
            name=pkg_data['name'],
            defaults={
                'description': pkg_data['description'],
                'price': pkg_data['price'],
                'package_type': pkg_data['package_type'],
                'farm_area': pkg_data['farm_area'],
                'image_url': pkg_data['image_url'],
                'capacity': pkg_data['capacity'],
                'is_available': True,
            }
        )


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_package_cartitem'),
    ]

    operations = [
        migrations.RunPython(create_initial_packages),
    ]
