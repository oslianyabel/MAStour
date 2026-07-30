/* Dropdown clock picker for admin time fields (12-hour format with AM/PM).
   Attaches to inputs rendered by TwelveHourTimeWidget (class "vTime12Field"). */
(function () {
    'use strict';

    var HOURS = [12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11];
    var MINUTES = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55];

    function pad(value) {
        return value < 10 ? '0' + value : String(value);
    }

    function parseInput(value) {
        var match = /^(\d{1,2}):(\d{2})\s*(am|pm)$/i.exec((value || '').trim());
        if (match) {
            return { hour: parseInt(match[1], 10), minute: parseInt(match[2], 10), meridiem: match[3].toUpperCase() };
        }
        var military = /^(\d{1,2}):(\d{2})/.exec((value || '').trim());
        if (military) {
            var hour24 = parseInt(military[1], 10);
            return {
                hour: hour24 % 12 || 12,
                minute: parseInt(military[2], 10),
                meridiem: hour24 < 12 ? 'AM' : 'PM'
            };
        }
        return { hour: 8, minute: 0, meridiem: 'AM' };
    }

    function buildPicker(input) {
        var state = parseInput(input.value);

        var panel = document.createElement('div');
        panel.className = 'time-picker-panel';
        panel.style.display = 'none';

        function section(title, values, key, formatter) {
            var wrapper = document.createElement('div');
            wrapper.className = 'time-picker-section';
            var label = document.createElement('div');
            label.className = 'time-picker-label';
            label.textContent = title;
            wrapper.appendChild(label);
            var grid = document.createElement('div');
            grid.className = 'time-picker-grid';
            values.forEach(function (value) {
                var option = document.createElement('button');
                option.type = 'button';
                option.className = 'time-picker-option';
                option.textContent = formatter(value);
                option.dataset.key = key;
                option.dataset.value = value;
                grid.appendChild(option);
            });
            wrapper.appendChild(grid);
            return wrapper;
        }

        panel.appendChild(section('Hora', HOURS, 'hour', String));
        panel.appendChild(section('Minutos', MINUTES, 'minute', pad));
        panel.appendChild(section('AM / PM', ['AM', 'PM'], 'meridiem', String));

        var footer = document.createElement('div');
        footer.className = 'time-picker-footer';
        var nowButton = document.createElement('button');
        nowButton.type = 'button';
        nowButton.className = 'time-picker-now';
        nowButton.textContent = 'Ahora';
        var closeButton = document.createElement('button');
        closeButton.type = 'button';
        closeButton.className = 'time-picker-close';
        closeButton.textContent = 'Listo';
        footer.appendChild(nowButton);
        footer.appendChild(closeButton);
        panel.appendChild(footer);

        function highlight() {
            panel.querySelectorAll('.time-picker-option').forEach(function (option) {
                var isSelected = String(state[option.dataset.key]) === String(option.dataset.value);
                option.classList.toggle('is-selected', isSelected);
            });
        }

        function writeValue() {
            input.value = pad(state.hour) + ':' + pad(state.minute) + ' ' + state.meridiem;
            input.dispatchEvent(new Event('input', { bubbles: true }));
            input.dispatchEvent(new Event('change', { bubbles: true }));
            highlight();
        }

        panel.addEventListener('click', function (event) {
            var option = event.target.closest('.time-picker-option');
            if (option) {
                var raw = option.dataset.value;
                state[option.dataset.key] = option.dataset.key === 'meridiem' ? raw : parseInt(raw, 10);
                writeValue();
                return;
            }
            if (event.target.closest('.time-picker-now')) {
                var now = new Date();
                state.hour = now.getHours() % 12 || 12;
                state.minute = now.getMinutes();
                state.meridiem = now.getHours() < 12 ? 'AM' : 'PM';
                writeValue();
                return;
            }
            if (event.target.closest('.time-picker-close')) {
                hide();
            }
        });

        var wrapper = document.createElement('span');
        wrapper.className = 'time-picker-wrapper';
        input.parentNode.insertBefore(wrapper, input);
        wrapper.appendChild(input);

        var toggle = document.createElement('button');
        toggle.type = 'button';
        toggle.className = 'time-picker-toggle';
        toggle.textContent = '🕐';
        toggle.title = 'Seleccionar hora';
        wrapper.appendChild(toggle);
        wrapper.appendChild(panel);

        function show() {
            state = parseInput(input.value);
            highlight();
            panel.style.display = 'block';
        }

        function hide() {
            panel.style.display = 'none';
        }

        toggle.addEventListener('click', function () {
            if (panel.style.display === 'none') {
                show();
            } else {
                hide();
            }
        });
        input.addEventListener('focus', show);

        document.addEventListener('click', function (event) {
            if (!wrapper.contains(event.target)) {
                hide();
            }
        });
    }

    function attachAll(root) {
        (root || document).querySelectorAll('input.vTime12Field').forEach(function (input) {
            if (!input.dataset.timePickerReady) {
                input.dataset.timePickerReady = '1';
                buildPicker(input);
            }
        });
    }

    window.addEventListener('load', function () {
        attachAll(document);
        // Inline rows added dynamically by the admin ("Añadir otro") also get a picker.
        document.addEventListener('formset:added', function (event) {
            attachAll(event.target);
        });
    });
})();
