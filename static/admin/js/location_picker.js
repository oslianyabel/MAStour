/* Map picker for the Excursion admin form: a button opens a map of Cuba where the admin
   clicks (or drags the marker) to set the latitude/longitude fields automatically.
   Uses Leaflet + OpenStreetMap (no API key). */
(function () {
    'use strict';

    var CUBA_CENTER = [21.9, -79.5];
    var CUBA_ZOOM = 6;
    var PICKED_ZOOM = 13;
    var DECIMALS = 8; // ~1 mm precision, well within the field's capacity

    window.addEventListener('load', function () {
        var latInput = document.getElementById('id_latitude');
        var lngInput = document.getElementById('id_longitude');
        if (!latInput || !lngInput || typeof L === 'undefined') {
            return;
        }

        var button = document.createElement('button');
        button.type = 'button';
        button.className = 'button';
        button.textContent = '📍 Seleccionar en el mapa';
        button.style.marginTop = '4px';

        var help = document.createElement('p');
        help.className = 'help';
        help.textContent = 'Haz clic en el mapa para fijar la ubicación; ' +
            'arrastra el marcador para ajustarla con precisión.';

        var mapDiv = document.createElement('div');
        mapDiv.style.cssText = 'height:360px;max-width:640px;margin-top:8px;border-radius:8px;' +
            'overflow:hidden;border:1px solid #e5e7eb;display:none;';

        var container = document.createElement('div');
        container.style.marginTop = '8px';
        container.appendChild(button);
        container.appendChild(mapDiv);
        container.appendChild(help);

        var row = lngInput.closest('.form-row, .fieldBox') || lngInput.parentNode;
        row.parentNode.insertBefore(container, row.nextSibling);

        var map = null;
        var marker = null;

        function parseValue(raw) {
            var value = (raw || '').trim().replace(',', '.');
            var number = parseFloat(value);
            return isNaN(number) ? null : number;
        }

        function writeFields(lat, lng) {
            latInput.value = lat.toFixed(DECIMALS);
            lngInput.value = lng.toFixed(DECIMALS);
            [latInput, lngInput].forEach(function (el) {
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
            });
        }

        function placeMarker(latlng, writeBack) {
            if (marker) {
                marker.setLatLng(latlng);
            } else {
                marker = L.marker(latlng, { draggable: true }).addTo(map);
                marker.on('dragend', function () {
                    var pos = marker.getLatLng();
                    writeFields(pos.lat, pos.lng);
                });
            }
            if (writeBack) {
                writeFields(latlng.lat, latlng.lng);
            }
        }

        function initMap() {
            var lat = parseValue(latInput.value);
            var lng = parseValue(lngInput.value);
            var hasPoint = lat !== null && lng !== null;
            map = L.map(mapDiv).setView(hasPoint ? [lat, lng] : CUBA_CENTER, hasPoint ? PICKED_ZOOM : CUBA_ZOOM);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; OpenStreetMap contributors',
                maxZoom: 19
            }).addTo(map);
            if (hasPoint) {
                placeMarker(L.latLng(lat, lng), false);
            }
            map.on('click', function (event) {
                placeMarker(event.latlng, true);
            });
        }

        button.addEventListener('click', function () {
            var isHidden = mapDiv.style.display === 'none';
            if (!isHidden) {
                mapDiv.style.display = 'none';
                button.textContent = '📍 Seleccionar en el mapa';
                return;
            }
            mapDiv.style.display = 'block';
            button.textContent = '✖ Ocultar mapa';
            if (map === null) {
                initMap();
            }
            setTimeout(function () { map.invalidateSize(); }, 60);
        });

        // If the admin types the coordinates by hand, move the marker to match.
        function syncFromFields() {
            if (map === null) {
                return;
            }
            var lat = parseValue(latInput.value);
            var lng = parseValue(lngInput.value);
            if (lat === null || lng === null) {
                return;
            }
            var latlng = L.latLng(lat, lng);
            placeMarker(latlng, false);
            map.panTo(latlng);
        }
        latInput.addEventListener('change', syncFromFields);
        lngInput.addEventListener('change', syncFromFields);
    });
})();
