/* One-click image deletion in the admin: asks for confirmation and removes the image
   immediately (no need to tick "Limpiar" and save the form). */
(function () {
    'use strict';

    function getCookie(name) {
        var match = document.cookie.match(new RegExp('(^|;\\s*)' + name + '=([^;]*)'));
        return match ? decodeURIComponent(match[2]) : null;
    }

    /* Finds the <input type="file"> that belongs to this button's field. Inline rows prefix
       the name (e.g. "photos-0-image"), so match the exact name or the "-<field>" suffix. */
    function findFileInput(button) {
        var field = button.dataset.field;
        var scope = button.closest('tr') || button.closest('form') || document;
        var found = null;
        scope.querySelectorAll('input[type="file"]').forEach(function (input) {
            if (input.name === field || input.name.endsWith('-' + field)) {
                found = input;
            }
        });
        return found;
    }

    /* The stock ClearableFileInput checkbox would be a second, confusing way to delete,
       so it is hidden for the fields that have the new button. */
    function hideNativeClearWidget(button) {
        var fileInput = findFileInput(button);
        if (!fileInput) {
            return;
        }
        var wrapper = fileInput.closest('p.file-upload') || fileInput.parentNode;
        if (!wrapper) {
            return;
        }
        wrapper.querySelectorAll('.clearable-file-input').forEach(function (node) {
            node.style.display = 'none';
        });
    }

    /* Rebuilds the file widget so it no longer advertises a file that is gone, while
       keeping the same <input type="file"> node so a new image can still be uploaded. */
    function refreshWidgetAfterDelete(button) {
        var fileInput = findFileInput(button);
        if (!fileInput) {
            return;
        }
        var paragraph = fileInput.closest('p.file-upload');
        if (!paragraph) {
            return;
        }
        var label = document.createElement('span');
        label.textContent = 'Sin imagen. Subir: ';
        paragraph.innerHTML = '';
        paragraph.appendChild(label);
        paragraph.appendChild(fileInput);
    }

    function removePreview(button) {
        if (button.dataset.deletesRecord === 'true') {
            var row = button.closest('tr');
            if (row) {
                row.style.transition = 'opacity .2s';
                row.style.opacity = '0';
                setTimeout(function () { row.remove(); }, 200);
                return;
            }
        }
        var box = button.closest('.image-preview-box');
        if (box) {
            box.innerHTML = '<span class="image-preview-empty">Imagen eliminada.</span>';
        }
        refreshWidgetAfterDelete(button);
    }

    function confirmMessage(button) {
        if (button.dataset.deletesRecord === 'true') {
            return '¿Eliminar esta imagen? Se borrará el registro completo de la lista. ' +
                'Esta acción no se puede deshacer.';
        }
        return '¿Eliminar esta imagen? Esta acción no se puede deshacer.';
    }

    document.addEventListener('click', function (event) {
        var button = event.target.closest('.delete-image-button');
        if (!button) {
            return;
        }
        event.preventDefault();
        if (!window.confirm(confirmMessage(button))) {
            return;
        }

        var body = new URLSearchParams({
            model: button.dataset.model,
            pk: button.dataset.pk,
            field: button.dataset.field
        });

        button.disabled = true;
        button.textContent = 'Eliminando…';

        fetch('/admin/tools/delete-image/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: body.toString(),
            credentials: 'same-origin'
        })
            .then(function (response) {
                return response.json().then(function (data) {
                    return { ok: response.ok, data: data };
                });
            })
            .then(function (result) {
                if (!result.ok || !result.data.ok) {
                    throw new Error(result.data.error || 'No se pudo eliminar la imagen.');
                }
                removePreview(button);
            })
            .catch(function (error) {
                button.disabled = false;
                button.textContent = '🗑 Eliminar imagen';
                window.alert(error.message);
            });
    });

    window.addEventListener('load', function () {
        document.querySelectorAll('.delete-image-button').forEach(hideNativeClearWidget);
    });
})();
