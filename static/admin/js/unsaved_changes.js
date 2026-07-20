/* Warns before leaving an add/change form with unsaved changes (e.g. clicking a sidebar link).
   Detects changes by comparing the form's serialized state against its baseline, so it works
   regardless of how a field was edited (typing, native selects or JS widgets). */
(function () {
    'use strict';

    var MESSAGE = 'Tienes cambios sin guardar en este registro. ' +
        'Si sales ahora se perderán todos los datos ingresados. ¿Deseas continuar?';

    function serialize(form) {
        try {
            return new URLSearchParams(new FormData(form)).toString();
        } catch (error) {
            return null;
        }
    }

    // Use window 'load' so any admin widget that mutates fields on init is already done,
    // giving us a stable baseline and avoiding false positives.
    window.addEventListener('load', function () {
        var form = document.querySelector('#content-main form');
        if (!form) {
            return;
        }

        var baseline = serialize(form);
        var submitting = false;

        function isDirty() {
            if (submitting || baseline === null) {
                return false;
            }
            var current = serialize(form);
            return current !== null && current !== baseline;
        }

        // Saving the form is a legitimate exit: do not warn.
        form.addEventListener('submit', function () {
            submitting = true;
        });

        // Intercept clicks on links that would navigate away from the form.
        document.addEventListener('click', function (event) {
            if (!isDirty()) {
                return;
            }
            var link = event.target.closest('a');
            if (!link) {
                return;
            }
            var href = link.getAttribute('href');
            if (!href || href.charAt(0) === '#' || href.indexOf('javascript:') === 0) {
                return;
            }
            if (link.target === '_blank') {
                return;
            }
            if (window.confirm(MESSAGE)) {
                // User accepted losing the changes: stop warning for this navigation.
                baseline = serialize(form);
            } else {
                event.preventDefault();
                event.stopPropagation();
            }
        }, true);

        // Fallback for browser back button, tab close or reload.
        window.addEventListener('beforeunload', function (event) {
            if (isDirty()) {
                event.preventDefault();
                event.returnValue = '';
            }
        });
    });
})();
