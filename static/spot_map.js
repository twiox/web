// Leaflet maps for the training spots: dashboard overview and the picker in the spot form.
// Needs Leaflet (members/snippets/leaflet.html) to be loaded first.
(function () {
    const LEIPZIG = [51.3397, 12.3731];

    function baseMap(element, center, zoom) {
        const map = L.map(element).setView(center, zoom);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            // OSM blocks tile requests without a Referer; the site's same-origin policy would send none
            referrerPolicy: 'strict-origin-when-cross-origin',
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        }).addTo(map);
        return map;
    }

    function el(tag, attrs, ...children) {
        const node = document.createElement(tag);
        Object.entries(attrs || {}).forEach(([key, value]) => {
            if (key === 'onclick') node.addEventListener('click', value);
            else node.setAttribute(key, value);
        });
        children.forEach(child => node.append(child));
        return node;
    }

    function routeUrl(lat, long) {
        return `https://www.google.de/maps/dir//${lat},${long}/@${lat},${long},17z`;
    }

    // Dashboard: all spots as markers, optional list and editing for trainers/chairmen
    function overview(element, spots, options) {
        const map = baseMap(element, LEIPZIG, 12);
        const markers = {};

        function popupFor(spot) {
            const box = el('div', { class: 'spot_popup' }, el('strong', {}, spot.title));
            if (spot.description) box.append(el('p', {}, spot.description));
            if (spot.sessions && spot.sessions.length) {
                box.append(el('p', { class: 'spot_popup__sessions' }, spot.sessions.join(' · ')));
            }
            const links = el('p', { class: 'spot_popup__links' },
                el('a', { href: routeUrl(spot.lat, spot.long), target: '_blank' }, 'Route'),
            );
            if (options.canEdit) {
                links.append(el('a', { href: spot.edit_url }, 'Bearbeiten'));
                links.append(el('a', { href: spot.delete_url }, 'Löschen'));
            }
            box.append(links);
            if (options.canEdit) box.append(el('p', { class: 'spot_popup__hint' }, 'Zum Verschieben den Marker ziehen.'));
            return box;
        }

        function confirmMove(spot, marker, from) {
            const to = marker.getLatLng();
            const box = el('div', { class: 'spot_popup' },
                el('strong', {}, spot.title),
                el('p', {}, 'Neue Position speichern?'),
                el('p', { class: 'spot_popup__links' },
                    el('a', { href: '#', onclick: event => { event.preventDefault(); save(); } }, 'Speichern'),
                    el('a', { href: '#', onclick: event => { event.preventDefault(); reset(); } }, 'Abbrechen'),
                ),
            );
            async function save() {
                const body = new FormData();
                body.append('lat', to.lat.toFixed(6));
                body.append('long', to.lng.toFixed(6));
                body.append('csrfmiddlewaretoken', options.csrfToken);
                const response = await fetch(spot.move_url, { method: 'POST', body });
                if (response.ok) {
                    const saved = await response.json();
                    spot.lat = saved.lat;
                    spot.long = saved.long;
                    marker.setPopupContent(popupFor(spot)).closePopup();
                    options.onMessage && options.onMessage('Position gespeichert');
                } else {
                    reset();
                    options.onMessage && options.onMessage('Position konnte nicht gespeichert werden');
                }
            }
            function reset() {
                marker.setLatLng(from).setPopupContent(popupFor(spot)).closePopup();
            }
            marker.setPopupContent(box).openPopup();
        }

        spots.forEach(spot => {
            const marker = L.marker([spot.lat, spot.long], { draggable: options.canEdit, title: spot.title })
                .addTo(map)
                .bindPopup(popupFor(spot));
            let from;
            marker.on('dragstart', () => { from = marker.getLatLng(); });
            marker.on('dragend', () => confirmMove(spot, marker, from));
            markers[spot.id] = marker;
        });

        if (spots.length) {
            map.fitBounds(L.latLngBounds(spots.map(s => [s.lat, s.long])), { padding: [40, 40], maxZoom: 15 });
        }

        // list next to the map: click zooms to the spot
        if (options.list) {
            options.list.addEventListener('click', event => {
                const item = event.target.closest('[data-spot]');
                if (!item || event.target.closest('a')) return;
                const marker = markers[item.dataset.spot];
                map.flyTo(marker.getLatLng(), 16);
                marker.openPopup();
            });
        }

        // "Neuer Spot": the next click on the map opens the form with that position
        if (options.newButton) {
            options.newButton.addEventListener('click', () => {
                element.classList.add('spot_map--placing');
                options.onMessage && options.onMessage('Klicke auf die Karte, um den neuen Spot zu setzen');
                map.once('click', event => {
                    const params = new URLSearchParams({ lat: event.latlng.lat.toFixed(6), long: event.latlng.lng.toFixed(6) });
                    window.location.href = `${options.createUrl}?${params}`;
                });
            });
        }
        return map;
    }

    // Spot and event forms: click or drag sets the coordinate inputs, typing moves the marker.
    // Without coordinates (the event meeting point is optional) the marker appears on the first click
    // and disappears again when the inputs are emptied.
    function picker(element, latInput, longInput) {
        const hasValue = latInput.value !== '' && longInput.value !== '';
        const start = hasValue ? [parseFloat(latInput.value), parseFloat(longInput.value)] : LEIPZIG;
        const map = baseMap(element, start, hasValue ? 16 : 12);
        const marker = L.marker(start, { draggable: true });
        if (hasValue) marker.addTo(map);

        function setInputs(latlng) {
            latInput.value = latlng.lat.toFixed(6);
            longInput.value = latlng.lng.toFixed(6);
            [latInput, longInput].forEach(input => input.dispatchEvent(new Event('input', { bubbles: true })));
        }
        map.on('click', event => { marker.setLatLng(event.latlng).addTo(map); setInputs(event.latlng); });
        marker.on('dragend', () => setInputs(marker.getLatLng()));
        [latInput, longInput].forEach(input => input.addEventListener('change', () => {
            const lat = parseFloat(latInput.value), long = parseFloat(longInput.value);
            if (!isNaN(lat) && !isNaN(long)) { marker.setLatLng([lat, long]).addTo(map); map.panTo([lat, long]); }
            else marker.remove();
        }));
        return map;
    }

    // Event detail: a single fixed marker, e.g. the meeting point
    function point(element, lat, long) {
        const map = baseMap(element, [lat, long], 16);
        L.marker([lat, long]).addTo(map);
        return map;
    }

    window.SpotMap = { overview, picker, point, routeUrl };
})();
