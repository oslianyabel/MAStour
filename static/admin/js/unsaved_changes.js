/* Warns before leaving an add/change form with unsaved changes (e.g. clicking a sidebar link).

   Dirtiness is decided by comparing each control to its own initial value (defaultValue /
   defaultChecked / the option marked selected in the HTML). This is immune to *when* the check
   runs, so admin widgets that rebuild the DOM on load (date/time shortcuts, related-object
   widgets) never produce a false "unsaved changes" warning.

   Note: the horizontal/vertical M2M selectors (filter_horizontal / filter_vertical) are skipped.
   Those widgets discard the original selected state from the DOM, so there is no reliable,
   timing-independent baseline for them; skipping avoids false positives at the cost of not
   warning when ONLY an M2M selector was changed. */
(function () {
    'use strict';

    var MESSAGE = 'Tienes cambios sin guardar en este registro. ' +
        'Si sales ahora se perderán todos los datos ingresados. ¿Deseas continuar?';

    function controlChanged(el) {
        var type = el.type;
        if (type === 'checkbox' || type === 'radio') {
            return el.checked !== el.defaultChecked;
        }
        if (el.tagName === 'SELECT') {
            if (el.multiple) {
                return false; // M2M selectors are intentionally not tracked (see file header)
            }
            var defaultOption = null;
            for (var i = 0; i < el.options.length; i++) {
                if (el.options[i].defaultSelected) {
                    defaultOption = el.options[i];
                    break;
                }
            }
            var defaultValue = defaultOption ? defaultOption.value
                : (el.options.length ? el.options[0].value : '');
            return el.value !== defaultValue;
        }
        if (type === 'file') {
            return !!(el.files && el.files.length);
        }
        return el.value !== el.defaultValue;
    }

    window.addEventListener('load', function () {
        var form = document.querySelector('#content-main form');
        if (!form) {
            return;
        }

        var submitting = false;

        function isDirty() {
            if (submitting) {
                return false;
            }
            var controls = form.querySelectorAll('input[name], textarea[name], select[name]');
            for (var i = 0; i < controls.length; i++) {
                if (controlChanged(controls[i])) {
                    return true;
                }
            }
            return false;
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
            if (!window.confirm(MESSAGE)) {
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
