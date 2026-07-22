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


class UnsavedChangesAdminMixin:
    """Warns before leaving an add/change form with unsaved changes."""

    class Media:
        js = ('admin/js/unsaved_changes.js',)


class ImagePreviewMixin:
    """Renders image thumbnails in the admin list and change form.

    Set ``image_field_name`` to the model's ImageField/FileField name and add
    ``image_thumb`` to ``list_display`` and ``image_preview`` to ``readonly_fields``.
    """

    image_field_name = 'image'
    preview_height = 220
    thumb_size = 48

    def _image(self, obj):  # noqa: ANN001, ANN202
        return getattr(obj, self.image_field_name, None) if obj else None

    @admin.display(description='imagen')
    def image_thumb(self, obj):  # noqa: ANN001, ANN201
        image = self._image(obj)
        if not image:
            return '—'
        return format_html(
            '<img src="{}" style="height:{}px;width:{}px;border-radius:6px;'
            'object-fit:cover;border:1px solid #e5e7eb;" />',
            image.url,
            self.thumb_size,
            self.thumb_size,
        )

    @admin.display(description='vista previa')
    def image_preview(self, obj):  # noqa: ANN001, ANN201
        image = self._image(obj)
        if not image:
            return '—'
        return format_html(
            '<img src="{}" style="max-height:{}px;max-width:340px;border-radius:8px;'
            'object-fit:contain;border:1px solid #e5e7eb;" />',
            image.url,
            self.preview_height,
        )


class BaseModelAdmin(UnsavedChangesAdminMixin, admin.ModelAdmin):
    """Base admin that adds the unsaved-changes guard to every registered model."""


class ExcursionPhotoInline(ImagePreviewMixin, admin.TabularInline):
    model = ExcursionPhoto
    image_field_name = 'image'
    extra = 1
    fields = ['image', 'image_preview', 'photo_type', 'caption']
    readonly_fields = ['image_preview']


class ExcursionVideoInline(admin.TabularInline):
    model = ExcursionVideo
    extra = 0


class SlotInline(admin.TabularInline):
    model = Slot
    extra = 0
    show_change_link = True
    fields = ['date', 'departure_time', 'return_time', 'capacity', 'guide', 'contact_phone']


@admin.register(Excursion)
class ExcursionAdmin(BaseModelAdmin):
    list_display = ['name', 'destination', 'category', 'adult_price', 'child_price', 'is_active']
    list_filter = ['category', 'destination', 'is_active']
    search_fields = ['name', 'description']
    filter_horizontal = ['optional_activities']
    inlines = [ExcursionPhotoInline, ExcursionVideoInline, SlotInline]


@admin.register(OptionalActivity)
class OptionalActivityAdmin(BaseModelAdmin):
    list_display = ['name', 'price']
    search_fields = ['name']


class ReservationInline(admin.TabularInline):
    model = Reservation
    extra = 0
    readonly_fields = ['created_at']


@admin.register(Slot)
class SlotAdmin(BaseModelAdmin):
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
class ReservationAdmin(BaseModelAdmin):
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
class GuideAdmin(ImagePreviewMixin, BaseModelAdmin):
    image_field_name = 'photo'
    list_display = ['image_thumb', 'name', 'age', 'sex']
    readonly_fields = ['image_preview']
    search_fields = ['name']


@admin.register(GastronomicOffer)
class GastronomicOfferAdmin(ImagePreviewMixin, BaseModelAdmin):
    image_field_name = 'image'
    list_display = ['image_thumb', 'name', 'price']
    readonly_fields = ['image_preview']
    search_fields = ['name']


@admin.register(PickupPoint)
class PickupPointAdmin(ImagePreviewMixin, BaseModelAdmin):
    image_field_name = 'image'
    list_display = ['image_thumb', 'name', 'location']
    readonly_fields = ['image_preview']
    list_filter = ['location']
    search_fields = ['name']


@admin.register(Category)
class CategoryAdmin(BaseModelAdmin):
    search_fields = ['name']


@admin.register(Location)
class LocationAdmin(BaseModelAdmin):
    search_fields = ['name']


@admin.register(SocialLink)
class SocialLinkAdmin(BaseModelAdmin):
    list_display = ['platform', 'url', 'is_active']
    list_editable = ['url', 'is_active']


@admin.register(TeamMember)
class TeamMemberAdmin(ImagePreviewMixin, BaseModelAdmin):
    image_field_name = 'photo'
    list_display = ['image_thumb', 'name', 'role', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    readonly_fields = ['image_preview']
    search_fields = ['name', 'role']


@admin.register(Faq)
class FaqAdmin(BaseModelAdmin):
    list_display = ['question', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    search_fields = ['question', 'answer']


class MemoryImageInline(ImagePreviewMixin, admin.TabularInline):
    model = MemoryImage
    image_field_name = 'image'
    extra = 3
    fields = ['image', 'image_preview', 'caption']
    readonly_fields = ['image_preview']


@admin.register(Memory)
class MemoryAdmin(BaseModelAdmin):
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
