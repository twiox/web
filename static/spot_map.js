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

    async function post(url, fields, csrfToken) {
        const body = new FormData();
        Object.entries(fields).forEach(([key, value]) => body.append(key, value));
        body.append('csrfmiddlewaretoken', csrfToken);
        const response = await fetch(url, { method: 'POST', body });
        let data = {};
        try { data = await response.json(); } catch (error) { /* e.g. a 403 page */ }
        return { ok: response.ok, data };
    }

    // A link inside a popup. The click must stop here: when it swaps the popup content, the link
    // is gone from the popup, and Leaflet would take the click for one on the map and close the popup.
    function link(text, onclick) {
        return el('a', { href: '#', onclick: event => { event.preventDefault(); event.stopPropagation(); onclick(); } }, text);
    }

    // Dashboard: all spots as markers. Trainers/chairmen also get the list, and create, move
    // edit and delete spots right on the map.
    function overview(element, spots, options) {
        const map = baseMap(element, LEIPZIG, 12);
        const markers = {};
        const say = text => options.onMessage && options.onMessage(text);

        function popupFor(spot) {
            const box = el('div', { class: 'spot_popup' }, el('strong', {}, spot.title));
            if (spot.description) box.append(el('p', {}, spot.description));
            if (spot.sessions && spot.sessions.length) {
                box.append(el('p', { class: 'spot_popup__sessions' }, spot.sessions.join(' · ')));
            }
            const links = el('p', { class: 'spot_popup__links' },
                el('a', { href: routeUrl(spot.lat, spot.long), target: '_blank' }, 'Route'),
            );
            if (options.canEdit) links.append(link('Bearbeiten', () => editSpot(spot)));
            if (options.canDelete) links.append(link('Löschen', () => confirmDelete(spot)));
            box.append(links);
            if (options.canEdit) box.append(el('p', { class: 'spot_popup__hint' }, 'Zum Verschieben den Marker ziehen.'));
            return box;
        }

        function addMarker(spot) {
            const marker = L.marker([spot.lat, spot.long], { draggable: options.canEdit, title: spot.title })
                .addTo(map)
                .bindPopup(() => popupFor(spot));
            let from;
            marker.on('dragstart', () => { from = marker.getLatLng(); });
            marker.on('dragend', () => confirmMove(spot, marker, from));
            markers[spot.id] = marker;
            return marker;
        }

        function confirmMove(spot, marker, from) {
            const to = marker.getLatLng();
            async function save() {
                const { ok, data } = await post(spot.update_url, { lat: to.lat.toFixed(6), long: to.lng.toFixed(6) }, options.csrfToken);
                if (ok) {
                    spot.lat = data.lat;
                    spot.long = data.long;
                    marker.closePopup();
                    say('Position gespeichert');
                } else {
                    reset();
                    say('Position konnte nicht gespeichert werden');
                }
            }
            function reset() { marker.setLatLng(from).closePopup(); }
            marker.setPopupContent(el('div', { class: 'spot_popup' },
                el('strong', {}, spot.title),
                el('p', {}, 'Neue Position speichern?'),
                el('p', { class: 'spot_popup__links' }, link('Speichern', save), link('Abbrechen', reset)),
            )).openPopup();
            restoreAfterClose(spot, marker);
        }

        function confirmDelete(spot) {
            const marker = markers[spot.id];
            const used = (spot.sessions || []).length;
            async function remove() {
                const { ok } = await post(spot.delete_url, {}, options.csrfToken);
                if (!ok) { say('Spot konnte nicht gelöscht werden'); return; }
                marker.remove();
                delete markers[spot.id];
                spots.splice(spots.indexOf(spot), 1);
                renderList();
                say(`${spot.title} gelöscht`);
            }
            const box = el('div', { class: 'spot_popup' },
                el('strong', {}, spot.title),
                el('p', {}, 'Spot wirklich löschen?'),
            );
            if (used) {
                box.append(el('p', { class: 'spot_popup__warning' },
                    `Wird noch von ${used} Trainingszeit${used === 1 ? '' : 'en'} genutzt; dort steht danach kein Ort mehr.`));
            }
            box.append(el('p', { class: 'spot_popup__links' }, link('Löschen', remove), link('Abbrechen', () => marker.closePopup())));
            marker.setPopupContent(box).openPopup();
            restoreAfterClose(spot, marker);
        }

        // the form for a new spot and for editing one: name and description
        function spotForm(heading, values, onSave, onCancel, hint) {
            const title = el('input', { type: 'text', maxlength: '30', placeholder: 'Name des Spots', required: '' });
            const description = el('textarea', { rows: '2', placeholder: 'Beschreibung (optional), z.B. Eingang, Treffpunkt' });
            title.value = values.title || '';
            description.value = values.description || '';
            const error = el('p', { class: 'spot_popup__warning', hidden: '' });
            const form = el('form', { class: 'spot_popup spot_popup__form' },
                el('strong', {}, heading), title, description, error,
                el('p', { class: 'spot_popup__links' }, el('button', { type: 'submit' }, 'Speichern'), link('Abbrechen', onCancel)),
            );
            if (hint) form.append(el('p', { class: 'spot_popup__hint' }, hint));
            form.addEventListener('submit', async event => {
                event.preventDefault();
                if (!title.value.trim()) { title.focus(); return; }
                const errors = await onSave({ title: title.value.trim(), description: description.value.trim() });
                if (errors) { error.textContent = errors; error.hidden = false; }
            });
            setTimeout(() => title.focus(), 0);
            return form;
        }
        const errorText = (data, fallback) => data.errors ? Object.values(data.errors).flat().join(' ') : fallback;

        function editSpot(spot) {
            const marker = markers[spot.id];
            marker.setPopupContent(spotForm(spot.title, spot, async values => {
                const { ok, data } = await post(spot.update_url, values, options.csrfToken);
                if (!ok) return errorText(data, 'Spot konnte nicht gespeichert werden');
                Object.assign(spot, data);
                if (marker.getElement()) marker.getElement().title = spot.title;
                marker.setPopupContent(() => popupFor(spot));
                renderList();
                say(`${spot.title} gespeichert`);
            }, () => marker.closePopup())).openPopup();
            restoreAfterClose(spot, marker);
        }

        // a question or form in the popup (move, edit, delete) is gone once the popup closes
        function restoreAfterClose(spot, marker) {
            marker.once('popupclose', () => marker.setPopupContent(() => popupFor(spot)));
        }

        // the list next to the map, built from the same data so it follows creating and deleting
        function renderList() {
            if (!options.list) return;
            options.list.replaceChildren();
            if (!spots.length) {
                options.list.append(el('li', { class: 'member_panel__hint' }, 'Noch keine Spots.'));
                return;
            }
            [...spots].sort((a, b) => a.title.localeCompare(b.title, 'de')).forEach(spot => {
                const used = (spot.sessions || []).length;
                const actions = el('span', { class: 'table_actions' },
                    el('a', { href: '#', title: 'Bearbeiten', onclick: event => {
                        event.preventDefault();
                        map.flyTo(markers[spot.id].getLatLng(), 16);
                        editSpot(spot);
                    } }, el('i', { class: 'fas fa-pen-square' })));
                if (options.canDelete) {
                    actions.append(el('a', { href: '#', title: 'Löschen', onclick: event => {
                        event.preventDefault();
                        map.flyTo(markers[spot.id].getLatLng(), 16);
                        confirmDelete(spot);
                    } }, el('i', { class: 'far fa-minus-square' })));
                }
                options.list.append(el('li', { 'data-spot': spot.id },
                    el('span', {},
                        el('strong', {}, spot.title),
                        el('small', {}, used ? `${used} Trainingszeit${used === 1 ? '' : 'en'}` : 'nicht genutzt'),
                    ),
                    actions,
                ));
            });
        }

        // "Neuer Spot": the next click on the map places a marker, the popup asks for the name
        let placing = false;
        function placeNew() {
            if (placing) return;
            placing = true;
            element.classList.add('spot_map--placing');
            say('Klicke auf die Karte, um den neuen Spot zu setzen');
            map.once('click', event => {
                placing = false;
                element.classList.remove('spot_map--placing');
                const marker = L.marker(event.latlng, { draggable: true }).addTo(map);
                let saved = false;
                const form = spotForm('Neuer Spot', {}, async values => {
                    const at = marker.getLatLng();
                    const { ok, data } = await post(options.createUrl, {
                        ...values, lat: at.lat.toFixed(6), long: at.lng.toFixed(6),
                    }, options.csrfToken);
                    if (!ok) return errorText(data, 'Spot konnte nicht angelegt werden');
                    saved = true;
                    marker.remove();
                    spots.push(data);
                    addMarker(data).openPopup();
                    renderList();
                    say(`${data.title} angelegt`);
                }, () => marker.closePopup(), 'Der Marker lässt sich noch verschieben.');
                marker.bindPopup(form, { closeOnClick: false }).openPopup();
                marker.on('dragend', () => marker.openPopup());
                // closing the popup without saving discards the new marker
                marker.on('popupclose', () => { if (!saved) marker.remove(); });
            });
        }

        spots.forEach(addMarker);
        renderList();
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
        if (options.newButton) options.newButton.addEventListener('click', placeNew);
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
