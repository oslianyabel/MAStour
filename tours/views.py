import datetime

from django.contrib import messages
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from tours.exceptions import NotEnoughCapacityError
from tours.forms import ReservationForm
from tours.models import Category, Excursion, Location, Slot, SocialLink, TeamMember
from tours.services import (
    ReservationData,
    build_whatsapp_url,
    create_reservation,
    refresh_slot_statuses,
)


def _upcoming_slots() -> QuerySet[Slot]:
    refresh_slot_statuses()
    today = datetime.date.today()
    return (
        Slot.objects.filter(date__gte=today, status=Slot.Status.PENDING, excursion__is_active=True)
        .select_related('excursion', 'excursion__destination', 'excursion__category', 'guide')
        .order_by('date', 'departure_time')
    )


def excursion_list(request: HttpRequest) -> HttpResponse:
    """Home: excursions with upcoming departures, filterable by category and destination."""
    slots = _upcoming_slots()
    category_id = request.GET.get('categoria')
    location_id = request.GET.get('localidad')
    if category_id:
        slots = slots.filter(excursion__category_id=category_id)
    if location_id:
        slots = slots.filter(excursion__destination_id=location_id)

    excursions: dict[int, dict] = {}
    for slot in slots:
        entry = excursions.setdefault(slot.excursion_id, {'excursion': slot.excursion, 'slots': []})
        entry['slots'].append(slot)

    context = {
        'excursion_entries': excursions.values(),
        'categories': Category.objects.all(),
        'locations': Location.objects.all(),
        'selected_category': category_id or '',
        'selected_location': location_id or '',
    }
    return render(request, 'tours/excursion_list.html', context)


def excursion_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """Excursion detail: photos, videos, map, optional activities and upcoming departures."""
    excursion = get_object_or_404(
        Excursion.objects.select_related('destination', 'category').prefetch_related(
            'photos', 'videos', 'optional_activities'
        ),
        pk=pk,
        is_active=True,
    )
    slots = (
        _upcoming_slots()
        .filter(excursion=excursion)
        .select_related('guide', 'pickup_point')
        .prefetch_related('gastronomic_offers')
    )
    destination_photos = [
        photo for photo in excursion.photos.all() if photo.photo_type == photo.PhotoType.DESTINATION
    ]
    transport_photos = [
        photo for photo in excursion.photos.all() if photo.photo_type == photo.PhotoType.TRANSPORT
    ]
    context = {
        'excursion': excursion,
        'slots': slots,
        'destination_photos': destination_photos,
        'transport_photos': transport_photos,
    }
    return render(request, 'tours/excursion_detail.html', context)


def past_excursions(request: HttpRequest) -> HttpResponse:
    """Past excursions: completed slots with their memory photo albums."""
    refresh_slot_statuses()
    slots = (
        Slot.objects.filter(status=Slot.Status.COMPLETED)
        .select_related('excursion', 'excursion__destination', 'excursion__category', 'guide')
        .prefetch_related('memory__images')
        .order_by('-date', '-departure_time')
    )
    return render(request, 'tours/past_excursions.html', {'slots': slots})


def about(request: HttpRequest) -> HttpResponse:
    """About-us page with philosophy, team and contact CTA."""
    whatsapp_link = SocialLink.objects.filter(
        platform=SocialLink.Platform.WHATSAPP, is_active=True
    ).first()
    team_members = TeamMember.objects.filter(is_active=True)
    return render(
        request,
        'tours/about.html',
        {'whatsapp_link': whatsapp_link, 'team_members': team_members},
    )


def reserve_slot(request: HttpRequest, slot_id: int) -> HttpResponse:
    """Reservation form for a slot; on success redirects to the WhatsApp chat."""
    slot = get_object_or_404(
        Slot.objects.select_related('excursion', 'excursion__destination', 'guide'),
        pk=slot_id,
        excursion__is_active=True,
    )
    if slot.status == Slot.Status.COMPLETED or slot.is_past:
        messages.error(request, 'Esta salida ya no está disponible.')
        return redirect('tours:excursion_detail', pk=slot.excursion_id)

    if request.method == 'POST':
        form = ReservationForm(slot, request.POST)
        if form.is_valid():
            data = ReservationData(
                adults_count=form.cleaned_data['adults_count'],
                children_count=form.cleaned_data['children_count'],
                address=form.cleaned_data['address'],
                representative_name=form.cleaned_data['representative_name'],
                representative_phone=form.cleaned_data['representative_phone'],
            )
            try:
                reservation = create_reservation(slot.pk, data)
            except NotEnoughCapacityError as error:
                form.add_error(
                    None,
                    f'No hay capacidad suficiente: quedan {error.seats_available} plazas disponibles.',
                )
            else:
                return redirect(build_whatsapp_url(reservation))
    else:
        form = ReservationForm(slot)

    return render(request, 'tours/reserve_slot.html', {'slot': slot, 'form': form})
