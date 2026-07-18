"""Seed demo data so the frontend can be verified manually.

Run with: uv run python scripts/seed_demo_data.py
"""

import datetime
import os
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django

django.setup()

from django.core.files import File  # noqa: E402

from tours.models import (  # noqa: E402
    Category,
    Excursion,
    Faq,
    GastronomicOffer,
    Guide,
    Location,
    Memory,
    MemoryImage,
    OptionalActivity,
    PickupPoint,
    Slot,
    SocialLink,
    TeamMember,
)


def seed() -> None:
    beach = Category.objects.get(name='Playa')
    river = Category.objects.get(name='Río')
    trinidad = Location.objects.get(name='Trinidad')
    topes = Location.objects.get(name='Topes')
    peninsula = Location.objects.get(name='Peninsula de Trinidad')

    guide, _ = Guide.objects.get_or_create(
        name='Carlos Pérez', defaults={'age': 34, 'sex': Guide.Sex.MALE}
    )
    offer, _ = GastronomicOffer.objects.get_or_create(
        name='Almuerzo criollo', defaults={'price': Decimal('8.50')}
    )
    pickup, _ = PickupPoint.objects.get_or_create(
        location=trinidad,
        name='Parque Céspedes',
        defaults={'latitude': Decimal('21.803300'), 'longitude': Decimal('-79.984500')},
    )

    beach_tour, _ = Excursion.objects.get_or_create(
        name='Playa Ancón todo el día',
        defaults={
            'description': 'Día completo en la playa Ancón con transporte incluido, '
            'tiempo libre para nadar y opción de snorkel.',
            'adult_price': Decimal('25.00'),
            'child_price': Decimal('12.00'),
            'destination': peninsula,
            'category': beach,
            'latitude': Decimal('21.729200'),
            'longitude': Decimal('-79.996100'),
        },
    )
    OptionalActivity.objects.get_or_create(
        excursion=beach_tour, name='Snorkel en el arrecife', defaults={'price': Decimal('10.00')}
    )

    river_tour, _ = Excursion.objects.get_or_create(
        name='Salto del Caburní',
        defaults={
            'description': 'Senderismo en Topes de Collantes hasta la cascada del Caburní, '
            'con baño en pozas naturales.',
            'adult_price': Decimal('30.00'),
            'child_price': Decimal('15.00'),
            'destination': topes,
            'category': river,
            'latitude': Decimal('21.916700'),
            'longitude': Decimal('-80.016700'),
        },
    )

    today = datetime.date.today()
    for excursion, days_ahead, capacity in [(beach_tour, 2, 20), (beach_tour, 5, 30), (river_tour, 3, 4)]:
        slot, created = Slot.objects.get_or_create(
            excursion=excursion,
            date=today + datetime.timedelta(days=days_ahead),
            departure_time=datetime.time(8, 0),
            defaults={
                'capacity': capacity,
                'guide': guide,
                'payment_address': 'Calle Real #45, Trinidad',
                'contact_phone': '+5352123456',
                'return_time': datetime.time(17, 0),
                'pickup_point': pickup if capacity <= 4 else None,
            },
        )
        if created:
            slot.gastronomic_offers.add(offer)

    social_urls = {
        SocialLink.Platform.INSTAGRAM: 'https://instagram.com/mastour',
        SocialLink.Platform.FACEBOOK: 'https://facebook.com/mastour',
        SocialLink.Platform.WHATSAPP: 'https://wa.me/5352123456',
        SocialLink.Platform.YOUTUBE: 'https://youtube.com/@mastour',
        SocialLink.Platform.X: 'https://x.com/mastour',
        SocialLink.Platform.TELEGRAM: 'https://t.me/mastour',
    }
    for platform, url in social_urls.items():
        SocialLink.objects.get_or_create(platform=platform, defaults={'url': url})

    team_members = [
        ('Carlos Martínez', 'Fundador y Guía Principal',
         'Cada rincón de Cuba tiene una historia que contar', 'team-1.png'),
        ('María Elena Rodríguez', 'Coordinadora de Excursiones',
         'La mejor excursión es la que supera tus expectativas', 'team-2.png'),
        ('Roberto Fernández', 'Conductor y Logística',
         'Tu seguridad y comodidad son mi prioridad', 'team-3.png'),
        ('Ana Lucía Pérez', 'Atención al Cliente',
         'Estoy aquí para que tu experiencia sea perfecta', 'team-4.png'),
    ]
    static_img_dir = Path(__file__).resolve().parent.parent / 'static' / 'img'
    for index, (name, role, quote, image_name) in enumerate(team_members):
        member, created = TeamMember.objects.get_or_create(
            name=name, defaults={'role': role, 'quote': quote, 'order': index}
        )
        source_image = static_img_dir / image_name
        if created and source_image.exists():
            with source_image.open('rb') as image_file:
                member.photo.save(image_name, File(image_file), save=True)

    past_slot, _ = Slot.objects.get_or_create(
        excursion=beach_tour,
        date=today - datetime.timedelta(days=5),
        departure_time=datetime.time(8, 0),
        defaults={
            'capacity': 20,
            'guide': guide,
            'payment_address': 'Calle Real #45, Trinidad',
            'contact_phone': '+5352123456',
            'return_time': datetime.time(17, 0),
        },
    )
    memory, memory_created = Memory.objects.get_or_create(
        slot=past_slot,
        defaults={'title': 'Un día inolvidable en Ancón', 'description': 'Sol, arena y snorkel.'},
    )
    if memory_created:
        static_img_dir = Path(__file__).resolve().parent.parent / 'static' / 'img'
        memory_images = [
            ('about-hero.png', 'Rumbo a la playa'),
            ('about-philosophy.png', 'Sabores del día'),
        ]
        for image_name, caption in memory_images:
            source_image = static_img_dir / image_name
            if source_image.exists():
                memory_image = MemoryImage(memory=memory, caption=caption)
                with source_image.open('rb') as image_file:
                    memory_image.image.save(image_name, File(image_file), save=True)

    demo_faqs = [
        ('¿Cómo reservo una excursión?',
         'Elige la excursión, selecciona la fecha de salida y completa el formulario de reserva. '
         'Al confirmar, se abrirá el chat de WhatsApp del organizador con los datos de tu reserva.'),
        ('¿Cómo pago mi reserva?',
         'El pago se coordina por WhatsApp y se realiza en la dirección de pago indicada en cada salida.'),
        ('¿Hasta qué edad aplica el precio de niños?',
         'El precio de niños aplica hasta los 12 años inclusive.'),
        ('¿Dónde es el punto de recogida?',
         'El punto de recogida se define y anuncia cuando la salida completa todas sus plazas.'),
        ('¿Qué pasa si se agotan las plazas?',
         'Cada salida tiene capacidad limitada. Si se agota, puedes elegir otra fecha disponible '
         'de la misma excursión.'),
    ]
    for index, (question, answer) in enumerate(demo_faqs):
        Faq.objects.get_or_create(question=question, defaults={'answer': answer, 'order': index})

    print('Demo data seeded successfully.')


if __name__ == '__main__':
    seed()
