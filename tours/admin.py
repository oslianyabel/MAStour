import os
from urllib.parse import urlencode

from django.contrib import admin, messages
from django.core.files.base import ContentFile
from django.db import models
from django.urls import reverse
from django.utils.html import format_html
from import_export.admin import ImportExportModelAdmin

from tours.admin_widgets import TwelveHourTimeField, format_time_12h
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


def _copy_file(source_field, target_field) -> bool:  # noqa: ANN001
    """Copy the bytes of one FileField into another; return False if unreadable."""
    try:
        source_field.open('rb')
        content = source_field.read()
    except (FileNotFoundError, OSError, ValueError):
        return False
    finally:
        try:
            source_field.close()
        except (OSError, ValueError):
            pass
    target_field.save(os.path.basename(source_field.name), ContentFile(content), save=False)
    return True


class AdminEnhancementsMixin:
    """Shared admin UX: unsaved-changes guard, image delete buttons, time/date helpers."""

    class Media:
        css = {'all': ('admin/css/admin_extras.css',)}
        js = (
            'admin/js/unsaved_changes.js',
            'admin/js/image_delete.js',
            'admin/js/time_picker.js',
            'admin/js/date_label.js',
        )


class TwelveHourTimeAdminMixin:
    """Renders TimeFields with the 12-hour (AM/PM) widget and clock picker."""

    def formfield_for_dbfield(self, db_field, request, **kwargs):  # noqa: ANN001, ANN201, ANN003
        if isinstance(db_field, models.TimeField) and not isinstance(db_field, models.DateTimeField):
            defaults = {'form_class': TwelveHourTimeField}
            if db_field.blank:
                defaults['required'] = False
            defaults.update(kwargs)
            return db_field.formfield(**defaults)
        return super().formfield_for_dbfield(db_field, request, **kwargs)


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
        preview = format_html(
            '<img src="{}" style="max-height:{}px;max-width:340px;border-radius:8px;'
            'object-fit:contain;border:1px solid #e5e7eb;display:block;" />',
            image.url,
            self.preview_height,
        )
        if not obj.pk:
            return preview
        meta = obj._meta
        field = meta.get_field(self.image_field_name)
        # A required image IS the record's content, so removing it deletes the record.
        deletes_record = 'true' if not field.blank else 'false'
        button = format_html(
            '<button type="button" class="delete-image-button" '
            'data-model="{}.{}" data-pk="{}" data-field="{}" data-deletes-record="{}" '
            'title="Eliminar imagen">🗑 Eliminar imagen</button>',
            meta.app_label,
            meta.model_name,
            obj.pk,
            self.image_field_name,
            deletes_record,
        )
        return format_html('<div class="image-preview-box">{}{}</div>', preview, button)


class BaseModelAdmin(AdminEnhancementsMixin, TwelveHourTimeAdminMixin, ImportExportModelAdmin):
    """Base admin with the shared UX plus import/export (CSV, XLSX, JSON…)."""


class BaseTabularInline(TwelveHourTimeAdminMixin, admin.TabularInline):
    """Tabular inline with the same 12-hour time widgets as the main forms."""


class ExcursionPhotoInline(ImagePreviewMixin, admin.TabularInline):
    model = ExcursionPhoto
    image_field_name = 'image'
    extra = 1
    fields = ['image', 'image_preview', 'photo_type', 'caption']
    readonly_fields = ['image_preview']


class ExcursionVideoInline(admin.TabularInline):
    model = ExcursionVideo
    extra = 0


class SlotInline(BaseTabularInline):
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
    change_form_template = 'admin/tours/excursion/change_form.html'

    class Media:
        css = {'all': ('https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',)}
        js = (
            'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js',
            'admin/js/location_picker.js',
        )

    def formfield_for_dbfield(self, db_field, request, **kwargs):  # noqa: ANN001, ANN201, ANN003
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        # Keep coordinates dot-formatted (unlocalized) so the map picker can read/write them.
        if db_field.name in ('latitude', 'longitude') and formfield is not None:
            formfield.localize = False
            formfield.widget.is_localized = False
        return formfield

    @staticmethod
    def _duplicate_url(excursion: Excursion) -> str:
        """URL of the add form pre-filled with this excursion's data (no name, no slots)."""
        params: dict[str, str] = {
            'description': excursion.description,
            'adult_price': excursion.adult_price,
            'child_price': excursion.child_price,
            'destination': excursion.destination_id,
            'category': excursion.category_id,
            '_duplicate_from': excursion.pk,
        }
        if excursion.latitude is not None:
            params['latitude'] = excursion.latitude
        if excursion.longitude is not None:
            params['longitude'] = excursion.longitude
        if excursion.is_active:
            # A checkbox is checked for any non-empty value, so only send it when True.
            params['is_active'] = '1'
        activity_ids = list(excursion.optional_activities.values_list('pk', flat=True))
        if activity_ids:
            params['optional_activities'] = ','.join(str(pk) for pk in activity_ids)
        return f'{reverse("admin:tours_excursion_add")}?{urlencode(params)}'

    def change_view(self, request, object_id, form_url='', extra_context=None):  # noqa: ANN001, ANN201
        excursion = self.get_object(request, object_id)
        extra_context = extra_context or {}
        if excursion is not None:
            extra_context['duplicate_url'] = self._duplicate_url(excursion)
        return super().change_view(request, object_id, form_url, extra_context)

    def save_related(self, request, form, formsets, change):  # noqa: ANN001, ANN201
        super().save_related(request, form, formsets, change)
        source_pk = request.GET.get('_duplicate_from')
        if change or not source_pk:
            return
        source = Excursion.objects.filter(pk=source_pk).first()
        if source is None:
            return
        copied = self._copy_media(source, form.instance)
        if copied:
            self.message_user(
                request,
                f'Se copiaron {copied} archivos (fotos y videos) desde «{source.name}».',
                messages.INFO,
            )

    @staticmethod
    def _copy_media(source: Excursion, target: Excursion) -> int:
        """Copy the source excursion's photos and videos onto the new one."""
        copied = 0
        for photo in source.photos.all():
            new_photo = ExcursionPhoto(
                excursion=target, photo_type=photo.photo_type, caption=photo.caption
            )
            if photo.image and _copy_file(photo.image, new_photo.image):
                new_photo.save()
                copied += 1
        for video in source.videos.all():
            new_video = ExcursionVideo(
                excursion=target, title=video.title, video_url=video.video_url
            )
            has_file = bool(video.video_file) and _copy_file(video.video_file, new_video.video_file)
            if has_file or video.video_url:
                new_video.save()
                copied += 1
        return copied


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
        'departure_time_display',
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

    @admin.display(description='salida', ordering='departure_time')
    def departure_time_display(self, slot: Slot) -> str:
        return format_time_12h(slot.departure_time)

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
