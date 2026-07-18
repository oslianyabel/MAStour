from django.contrib import admin
from django.utils.html import format_html

from tours.models import (
    Category,
    Excursion,
    ExcursionPhoto,
    ExcursionVideo,
    Faq,
    GastronomicOffer,
    Guide,
    Location,
    Memory,
    MemoryImage,
    OptionalActivity,
    PickupPoint,
    Reservation,
    Slot,
    SocialLink,
    TeamMember,
)
from tours.services import refresh_slot_statuses


class ExcursionPhotoInline(admin.TabularInline):
    model = ExcursionPhoto
    extra = 1


class ExcursionVideoInline(admin.TabularInline):
    model = ExcursionVideo
    extra = 0


class OptionalActivityInline(admin.TabularInline):
    model = OptionalActivity
    extra = 0


class SlotInline(admin.TabularInline):
    model = Slot
    extra = 0
    show_change_link = True
    fields = ['date', 'departure_time', 'return_time', 'capacity', 'guide', 'contact_phone']


@admin.register(Excursion)
class ExcursionAdmin(admin.ModelAdmin):
    list_display = ['name', 'destination', 'category', 'adult_price', 'child_price', 'is_active']
    list_filter = ['category', 'destination', 'is_active']
    search_fields = ['name', 'description']
    inlines = [ExcursionPhotoInline, ExcursionVideoInline, OptionalActivityInline, SlotInline]


class ReservationInline(admin.TabularInline):
    model = Reservation
    extra = 0
    readonly_fields = ['created_at']


@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    list_display = [
        'excursion',
        'date',
        'departure_time',
        'status',
        'capacity',
        'seats_taken_display',
        'seats_available_display',
        'sold_out_display',
        'guide',
        'pickup_point',
    ]
    list_filter = ['status', 'date', 'excursion', 'guide']
    autocomplete_fields = ['excursion']
    filter_horizontal = ['gastronomic_offers']
    inlines = [ReservationInline]

    def get_queryset(self, request):  # noqa: ANN001, ANN201
        refresh_slot_statuses()
        return super().get_queryset(request)

    @admin.display(description='vendidas')
    def seats_taken_display(self, slot: Slot) -> int:
        return slot.seats_taken

    @admin.display(description='disponibles')
    def seats_available_display(self, slot: Slot) -> int:
        return slot.seats_available

    @admin.display(description='agotada')
    def sold_out_display(self, slot: Slot) -> str:
        if slot.is_sold_out:
            return format_html('<strong style="color:#c0392b;">Sí — definir punto de recogida</strong>')
        return 'No'


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = [
        'representative_name',
        'representative_phone',
        'slot',
        'adults_count',
        'children_count',
        'total_price_display',
        'created_at',
    ]
    list_filter = ['slot__date', 'slot__excursion']
    search_fields = ['representative_name', 'representative_phone']
    readonly_fields = ['created_at']

    @admin.display(description='total')
    def total_price_display(self, reservation: Reservation) -> str:
        return f'${reservation.total_price}'


@admin.register(Guide)
class GuideAdmin(admin.ModelAdmin):
    list_display = ['name', 'age', 'sex']
    search_fields = ['name']


@admin.register(GastronomicOffer)
class GastronomicOfferAdmin(admin.ModelAdmin):
    list_display = ['name', 'price']
    search_fields = ['name']


@admin.register(PickupPoint)
class PickupPointAdmin(admin.ModelAdmin):
    list_display = ['name', 'location']
    list_filter = ['location']
    search_fields = ['name']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ['name']


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    search_fields = ['name']


@admin.register(SocialLink)
class SocialLinkAdmin(admin.ModelAdmin):
    list_display = ['platform', 'url', 'is_active']
    list_editable = ['url', 'is_active']


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ['name', 'role', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    search_fields = ['name', 'role']


@admin.register(Faq)
class FaqAdmin(admin.ModelAdmin):
    list_display = ['question', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    search_fields = ['question', 'answer']


class MemoryImageInline(admin.TabularInline):
    model = MemoryImage
    extra = 3


@admin.register(Memory)
class MemoryAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'slot', 'images_count_display', 'created_at']
    inlines = [MemoryImageInline]

    def get_queryset(self, request):  # noqa: ANN001, ANN201
        refresh_slot_statuses()
        return super().get_queryset(request)

    def get_form(self, request, obj=None, **kwargs):  # noqa: ANN001, ANN201, ANN002, ANN003
        refresh_slot_statuses()
        return super().get_form(request, obj, **kwargs)

    @admin.display(description='imágenes')
    def images_count_display(self, memory: Memory) -> int:
        return memory.images.count()
