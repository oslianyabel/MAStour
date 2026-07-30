from django.apps import apps
from django.contrib.admin.models import CHANGE, DELETION, LogEntry
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_POST

# Only models of this app may be targeted, so the endpoint can never be pointed at
# unrelated models (e.g. auth) even by a staff user crafting the request by hand.
ALLOWED_APP_LABEL = 'tours'


@staff_member_required
@require_POST
def delete_image(request: HttpRequest) -> JsonResponse:
    """Delete an image from the admin UI, without needing to submit the whole form.

    Expects ``model`` (``app_label.model_name``), ``pk`` and ``field`` in POST data.

    When the field is optional the file is removed and the field cleared; when the image
    is the record's required content (e.g. an excursion photo) the whole record is
    deleted instead, which is what removing that image actually means.
    """
    model_path = request.POST.get('model', '')
    object_pk = request.POST.get('pk', '')
    field_name = request.POST.get('field', '')

    try:
        app_label, model_name = model_path.split('.')
    except ValueError:
        return JsonResponse({'error': 'Modelo no válido.'}, status=400)

    if app_label != ALLOWED_APP_LABEL:
        return JsonResponse({'error': 'Modelo no permitido.'}, status=403)

    try:
        model = apps.get_model(app_label, model_name)
    except LookupError:
        return JsonResponse({'error': 'Modelo no encontrado.'}, status=404)

    try:
        field = model._meta.get_field(field_name)
    except FieldDoesNotExist:
        return JsonResponse({'error': 'Campo no encontrado.'}, status=404)

    if not isinstance(field, models.FileField):
        return JsonResponse({'error': 'El campo no es una imagen o archivo.'}, status=400)

    # Check permissions before touching data, so nothing about the record is revealed
    # to a user who is not allowed to act on it.
    deletes_record = not field.blank
    required_perm = 'delete' if deletes_record else 'change'
    if not request.user.has_perm(f'{app_label}.{required_perm}_{model_name.lower()}'):
        return JsonResponse({'error': 'No tiene permiso para realizar esta acción.'}, status=403)

    instance = model.objects.filter(pk=object_pk).first()
    if instance is None:
        return JsonResponse({'error': 'Registro no encontrado.'}, status=404)

    file_field = getattr(instance, field_name)
    if not file_field:
        return JsonResponse({'error': 'Este registro no tiene imagen.'}, status=400)

    if deletes_record:
        # Log before deleting, while the instance still exists.
        LogEntry.objects.log_actions(
            request.user.pk,
            [instance],
            DELETION,
            change_message='Eliminado desde el botón de borrar imagen.',
            single_object=True,
        )
        # Django does not remove the stored file when deleting a record, so drop it
        # explicitly to avoid leaving orphan files behind.
        file_field.delete(save=False)
        instance.delete()
        return JsonResponse({'ok': True, 'deleted_record': True})

    file_field.delete(save=True)
    LogEntry.objects.log_actions(
        request.user.pk,
        [instance],
        CHANGE,
        change_message=f'Imagen eliminada del campo "{field_name}".',
        single_object=True,
    )
    return JsonResponse({'ok': True, 'deleted_record': False})
