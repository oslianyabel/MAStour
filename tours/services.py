from dataclasses import dataclass
from urllib.parse import quote

from django.db import transaction

from tours.exceptions import NotEnoughCapacityError
from tours.models import Reservation, Slot


@dataclass
class ReservationData:
    """Validated client input needed to create a reservation."""

    adults_count: int
    children_count: int
    address: str
    representative_name: str
    representative_phone: str


def create_reservation(slot_id: int, data: ReservationData) -> Reservation:
    """Create a reservation, locking the slot row so capacity is never oversold."""
    with transaction.atomic():
        slot = Slot.objects.select_for_update().get(pk=slot_id)
        requested_seats = data.adults_count + data.children_count
        if requested_seats > slot.seats_available:
            raise NotEnoughCapacityError(slot.seats_available)
        return Reservation.objects.create(
            slot=slot,
            adults_count=data.adults_count,
            children_count=data.children_count,
            address=data.address,
            representative_name=data.representative_name,
            representative_phone=data.representative_phone,
        )


def refresh_slot_statuses() -> int:
    """Mark pending slots as completed once their return time (Havana) has passed.

    Returns the number of slots updated.
    """
    pending_slots = Slot.objects.filter(status=Slot.Status.PENDING)
    completed_ids = [slot.pk for slot in pending_slots if slot.is_past]
    if not completed_ids:
        return 0
    return Slot.objects.filter(pk__in=completed_ids).update(status=Slot.Status.COMPLETED)


def build_whatsapp_url(reservation: Reservation) -> str:
    """Build the wa.me link that opens the contact phone chat with the reservation details."""
    slot = reservation.slot
    excursion = slot.excursion
    lines = [
        '¡Hola! Acabo de realizar una reserva:',
        f'*Excursión:* {excursion.name} ({excursion.destination})',
        f'*Fecha:* {slot.date:%d/%m/%Y}',
        f'*Salida:* {slot.departure_time:%H:%M} — *Retorno:* {slot.return_time:%H:%M}',
        f'*Adultos:* {reservation.adults_count}',
        f'*Niños:* {reservation.children_count}',
        f'*Total a pagar:* ${reservation.total_price}',
        f'*Representante:* {reservation.representative_name}',
        f'*Teléfono:* {reservation.representative_phone}',
        f'*Dirección:* {reservation.address}',
        f'*Reserva #:* {reservation.pk}',
    ]
    message = '\n'.join(lines)
    return f'https://wa.me/{slot.whatsapp_phone}?text={quote(message)}'
