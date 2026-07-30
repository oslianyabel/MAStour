/* Shows a human-readable date next to admin date inputs: 08/07/2026 -> "8 de julio del 2026". */
(function () {
    'use strict';

    var MONTHS = [
        'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
        'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
    ];

    function parseDate(rawValue) {
        var value = (rawValue || '').trim();
        if (!value) {
            return null;
        }
        var day;
        var month;
        var year;
        var slashed = /^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$/.exec(value); // dd/mm/yyyy
        var iso = /^(\d{4})-(\d{1,2})-(\d{1,2})$/.exec(value);           // yyyy-mm-dd
        if (slashed) {
            day = parseInt(slashed[1], 10);
            month = parseInt(slashed[2], 10);
            year = parseInt(slashed[3], 10);
        } else if (iso) {
            year = parseInt(iso[1], 10);
            month = parseInt(iso[2], 10);
            day = parseInt(iso[3], 10);
        } else {
            return null;
        }
        if (month < 1 || month > 12 || day < 1 || day > 31) {
            return null;
        }
        // Reject impossible days such as 31/02.
        var probe = new Date(year, month - 1, day);
        if (probe.getMonth() !== month - 1 || probe.getDate() !== day) {
            return null;
        }
        return day + ' de ' + MONTHS[month - 1] + ' del ' + year;
    }

    function attach(input) {
        if (input.dataset.dateLabelReady) {
            return;
        }
        input.dataset.dateLabelReady = '1';

        var label = document.createElement('span');
        label.className = 'date-label';
        input.parentNode.insertBefore(label, input.nextSibling);

        function update() {
            var text = parseDate(input.value);
            label.textContent = text || '';
        }

        input.addEventListener('input', update);
        input.addEventListener('change', update);
        // The admin calendar widget writes the value without firing events.
        input.addEventListener('blur', update);
        setInterval(function () {
            if (input.dataset.lastSeen !== input.value) {
                input.dataset.lastSeen = input.value;
                update();
            }
        }, 300);
        update();
    }

    function attachAll(root) {
        (root || document).querySelectorAll('input.vDateField').forEach(attach);
    }

    window.addEventListener('load', function () {
        attachAll(document);
        document.addEventListener('formset:added', function (event) {
            attachAll(event.target);
        });
    });
})();
