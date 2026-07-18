from django.db import migrations

LOCATION_NAMES = [
    'Topes',
    'Trinidad',
    'Santa Clara',
    'Cienfuegos',
    'Yaguajay',
    'Cabaiguan',
    'Sancti Spiritus',
    'Peninsula de Trinidad',
]

CATEGORY_NAMES = ['Playa', 'Río']


def seed_data(apps, schema_editor):
    Location = apps.get_model('tours', 'Location')
    Category = apps.get_model('tours', 'Category')
    for name in LOCATION_NAMES:
        Location.objects.get_or_create(name=name)
    for name in CATEGORY_NAMES:
        Category.objects.get_or_create(name=name)


def unseed_data(apps, schema_editor):
    Location = apps.get_model('tours', 'Location')
    Category = apps.get_model('tours', 'Category')
    Location.objects.filter(name__in=LOCATION_NAMES).delete()
    Category.objects.filter(name__in=CATEGORY_NAMES).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('tours', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_data, unseed_data),
    ]
