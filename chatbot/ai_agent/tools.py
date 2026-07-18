"""Read-only tools that expose the tours database to the AI agent.

All tools are synchronous: PydanticAI executes them in a worker thread, where
Django opens a dedicated DB connection, so ORM access is safe.
"""

import datetime
import logging

from django.db.models import QuerySet
from django.urls import reverse

from tours.models import Category, Excursion, Location, Reservation, Slot, SocialLink

logger = logging.getLogger(__name__)


def _format_slot(slot: Slot) -> str:
    availability = 'AGOTADA' if slot.is_sold_out else f'{slot.seats_available} plazas disponibles'
    pickup = slot.pickup_point.name if slot.pickup_point else 'por definir'
    offers = ', '.join(f'{offer.name} (${offer.price})' for offer in slot.gastronomic_offers.all())
    return (
        f'- Salida id={slot.pk} | {slot.date:%d/%m/%Y} | salida {slot.departure_time:%H:%M}, '
        f'retorno {slot.return_time:%H:%M} | {availability} (capacidad {slot.capacity}) | '
        f'guía: {slot.guide.name} | punto de recogida: {pickup}'
        + (f' | ofertas gastronómicas: {offers}' if offers else '')
        + f' | enlace de reserva: {reverse("tours:reserve_slot", args=[slot.pk])}'
    )


def _upcoming_slots() -> QuerySet[Slot]:
    return (
        Slot.objects.filter(date__gte=datetime.date.today(), excursion__is_active=True)
        .select_related('excursion', 'excursion__destination', 'guide', 'pickup_point')
        .prefetch_related('gastronomic_offers', 'reservations')
        .order_by('date', 'departure_time')
    )


def list_categories() -> str:
    """List every excursion category available.

    Returns:
        One category name per line.
    """
    logger.debug('[list_categories] called')
    names = list(Category.objects.values_list('name', flat=True))
    return 'Categorías: ' + ', '.join(names) if names else 'No hay categorías registradas.'


def list_destinations() -> str:
    """List every destination locality available.

    Returns:
        One destination name per line.
    """
    logger.debug('[list_destinations] called')
    names = list(Location.objects.values_list('name', flat=True))
    return 'Destinos: ' + ', '.join(names) if names else 'No hay destinos registrados.'


def list_excursions(category: str = '', destination: str = '') -> str:
    """List active excursions, optionally filtered by category and/or destination.

    Args:
        category: Optional category name (partial match, case-insensitive), e.g. "Playa".
        destination: Optional destination locality name (partial match, case-insensitive),
            e.g. "Trinidad".

    Returns:
        For each excursion: id, name, destination, category, prices and detail page link.
    """
    logger.debug('[list_excursions] category=%r destination=%r', category, destination)
    excursions = Excursion.objects.filter(is_active=True).select_related('destination', 'category')
    if category:
        excursions = excursions.filter(category__name__icontains=category)
    if destination:
        excursions = excursions.filter(destination__name__icontains=destination)

    lines = [
        f'- id={excursion.pk} | {excursion.name} | destino: {excursion.destination.name} | '
        f'categoría: {excursion.category.name} | adultos: ${excursion.adult_price} | '
        f'niños (hasta 12): ${excursion.child_price} | '
        f'detalles: {reverse("tours:excursion_detail", args=[excursion.pk])}'
        for excursion in excursions
    ]
    if not lines:
        return 'No se encontraron excursiones con esos filtros.'
    return 'Excursiones activas:\n' + '\n'.join(lines)


def get_excursion_details(excursion_id: int) -> str:
    """Get the full details of one excursion.

    Includes description, prices, optional activities, media available, map coordinates
    and every upcoming departure (slot) with its availability.

    Args:
        excursion_id: The id of the excursion, as returned by list_excursions.

    Returns:
        A detailed description of the excursion and its upcoming departures.
    """
    logger.debug('[get_excursion_details] excursion_id=%s', excursion_id)
    excursion = (
        Excursion.objects.filter(pk=excursion_id, is_active=True)
        .select_related('destination', 'category')
        .prefetch_related('optional_activities', 'photos', 'videos')
        .first()
    )
    if excursion is None:
        return f'No existe una excursión activa con id={excursion_id}.'

    activities = '\n'.join(
        f'  - {activity.name}: ${activity.price}'
        + (f' — {activity.description}' if activity.description else '')
        for activity in excursion.optional_activities.all()
    )
    slots = '\n'.join(_format_slot(slot) for slot in _upcoming_slots().filter(excursion=excursion))
    photos_count = excursion.photos.count()
    videos_count = excursion.videos.count()
    map_info = (
        f'coordenadas: {excursion.latitude}, {excursion.longitude}' if excursion.has_map else 'sin mapa'
    )
    return (
        f'{excursion.name} (id={excursion.pk})\n'
        f'Destino: {excursion.destination.name} | Categoría: {excursion.category.name}\n'
        f'Precios: adultos ${excursion.adult_price}, niños (hasta 12 años) ${excursion.child_price}\n'
        f'Descripción: {excursion.description or "sin descripción"}\n'
        f'Multimedia: {photos_count} fotos, {videos_count} videos | {map_info}\n'
        f'Página de detalles: {reverse("tours:excursion_detail", args=[excursion.pk])}\n'
        + (f'Actividades opcionales:\n{activities}\n' if activities else 'Sin actividades opcionales.\n')
        + (f'Próximas salidas:\n{slots}' if slots else 'Sin salidas programadas próximamente.')
    )


def get_upcoming_departures(destination: str = '') -> str:
    """List every upcoming departure (slot) across all excursions.

    Args:
        destination: Optional destination locality name to filter by (partial match,
            case-insensitive).

    Returns:
        Each upcoming departure with date, times, availability, guide and booking link.
    """
    logger.debug('[get_upcoming_departures] destination=%r', destination)
    slots = _upcoming_slots()
    if destination:
        slots = slots.filter(excursion__destination__name__icontains=destination)
    lines = [f'{slot.excursion.name}: {_format_slot(slot)}' for slot in slots]
    if not lines:
        return 'No hay salidas programadas próximamente.'
    return 'Próximas salidas:\n' + '\n'.join(lines)


def get_departure_details(slot_id: int) -> str:
    """Get the full details of one departure (slot).

    Includes capacity, availability, guide, gastronomic offers, payment address,
    contact phone, schedule and pickup point.

    Args:
        slot_id: The id of the departure, as returned by other tools.

    Returns:
        A detailed description of the departure.
    """
    logger.debug('[get_departure_details] slot_id=%s', slot_id)
    slot = (
        Slot.objects.filter(pk=slot_id)
        .select_related('excursion', 'excursion__destination', 'guide', 'pickup_point')
        .prefetch_related('gastronomic_offers')
        .first()
    )
    if slot is None:
        return f'No existe una salida con id={slot_id}.'

    guide = slot.guide
    offers = '\n'.join(f'  - {offer.name}: ${offer.price}' for offer in slot.gastronomic_offers.all())
    pickup = slot.pickup_point.name if slot.pickup_point else 'por definir (se fija al agotarse las plazas)'
    availability = 'AGOTADA' if slot.is_sold_out else f'{slot.seats_available} plazas disponibles'
    return (
        f'Salida de {slot.excursion.name} — {slot.date:%d/%m/%Y} (id={slot.pk})\n'
        f'Horario: salida {slot.departure_time:%H:%M}, retorno {slot.return_time:%H:%M}\n'
        f'Disponibilidad: {availability} (capacidad {slot.capacity})\n'
        f'Guía: {guide.name} ({guide.age} años, {guide.get_sex_display()})\n'
        f'Punto de recogida: {pickup}\n'
        f'Dirección de pago: {slot.payment_address}\n'
        f'Teléfono de contacto (WhatsApp): {slot.contact_phone}\n'
        + (f'Ofertas gastronómicas:\n{offers}\n' if offers else 'Sin ofertas gastronómicas.\n')
        + f'Enlace de reserva: {reverse("tours:reserve_slot", args=[slot.pk])}'
    )


def find_reservations_by_phone(phone: str) -> str:
    """Find reservations by the representative's phone number.

    Args:
        phone: The phone number used when booking (digits are compared, ignoring
            spaces, dashes and the plus sign).

    Returns:
        Each reservation with excursion, date, people count and total price.
    """
    logger.debug('[find_reservations_by_phone] phone=%r', phone)
    digits = ''.join(character for character in phone if character.isdigit())
    if not digits:
        return 'Indica un número de teléfono válido para buscar la reserva.'

    reservations = Reservation.objects.select_related(
        'slot', 'slot__excursion', 'slot__excursion__destination'
    ).order_by('-created_at')
    matches = [
        reservation
        for reservation in reservations
        if digits in ''.join(ch for ch in reservation.representative_phone if ch.isdigit())
    ]
    if not matches:
        return f'No se encontraron reservas para el teléfono {phone}.'

    lines = [
        f'- {reservation.excursion.name} el {reservation.slot.date:%d/%m/%Y} a nombre de '
        f'{reservation.representative_name}: {reservation.adults_count} adultos, '
        f'{reservation.children_count} niños, total ${reservation.total_price}'
        for reservation in matches
    ]
    return 'Reservas encontradas:\n' + '\n'.join(lines)


def get_contact_channels() -> str:
    """Get the agency's social networks and contact channels.

    Returns:
        Each active social network with its link.
    """
    logger.debug('[get_contact_channels] called')
    links = SocialLink.objects.filter(is_active=True)
    lines = [f'- {link.get_platform_display()}: {link.url}' for link in links]
    if not lines:
        return 'No hay redes sociales registradas por el momento.'
    return 'Canales de contacto de MAS tour:\n' + '\n'.join(lines)
