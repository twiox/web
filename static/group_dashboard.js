// Training group dashboard (trainer/training_group_detail.html): one table in which the line chart
// "Teilnehmende pro Training" and the heatmap "Teilnahme pro Person" share the x-axis, one column per
// Trainingsstunde. The script draws the line over the columns (their centres measured from the table,
// so it stays aligned at any width or zoom), puts the y labels into the sticky name column, and links
// the hover of both: the crosshair and the highlighted column follow the pointer on either part.
// Colours come from CSS custom properties on .group_dash, validated against the panel surface.
(function () {
    const SVG = 'http://www.w3.org/2000/svg';
    const dash = document.querySelector('.group_dash');
    if (!dash) return;
    const css = name => getComputedStyle(dash).getPropertyValue(name).trim();
    const data = JSON.parse(document.getElementById('timeline_data').textContent);
    const box = document.getElementById('timeline_chart');
    const yaxis = document.getElementById('timeline_yaxis');
    const wrap = document.getElementById('heatmap_wrap');
    const tip = document.getElementById('dash_tip');
    const HEIGHT = 170, PAD_TOP = 16, PAD_BOTTOM = 8;

    function el(tag, attrs, parent) {
        const node = document.createElementNS(SVG, tag);
        Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value));
        if (parent) parent.appendChild(node);
        return node;
    }

    // tooltip next to the pointer, inside the panel; texts via textContent (names are user data)
    function showTip(lines, x, y) {
        tip.replaceChildren(...lines.map(([text, strong]) => {
            const line = document.createElement(strong ? 'strong' : 'span');
            line.textContent = text;
            return line;
        }));
        tip.hidden = false;
        const panel = tip.parentElement.getBoundingClientRect();
        const left = Math.min(x - panel.left + 12, panel.width - tip.offsetWidth - 4);
        tip.style.left = Math.max(4, left) + 'px';
        tip.style.top = (y - panel.top - tip.offsetHeight - 10) + 'px';
    }

    // clean tick step for a maximum value: 1, 2, 5, 10, 20, ...
    function niceStep(max) {
        const raw = Math.max(1, max) / 3;
        const power = Math.pow(10, Math.floor(Math.log10(raw)));
        return [1, 2, 5, 10].map(f => f * power).find(step => step >= raw);
    }

    // the highlighted column, shared by the chart and the heatmap
    let marked = [];
    function markColumn(i) {
        marked.forEach(node => node.classList.remove('is_col'));
        marked = i === null ? [] : [...wrap.querySelectorAll(`[data-col="${i}"]`)];
        marked.forEach(node => node.classList.add('is_col'));
    }

    // Too many trainings for the width: only the last 6 months, the rest via "Alle anzeigen"
    const heads = [...wrap.querySelectorAll('.heatmap__axis [data-col]')];
    const chartCell = box ? box.closest('td') : null;
    const hint = document.getElementById('dash_restricted');
    let showAll = false;
    function restrict() {
        wrap.querySelectorAll('.is_old').forEach(node => node.classList.remove('is_old'));
        hint.hidden = true;
        if (showAll || wrap.scrollWidth <= wrap.clientWidth || !heads.length) return;
        const cutoff = new Date(heads[heads.length - 1].dataset.date);
        cutoff.setMonth(cutoff.getMonth() - 6);
        heads.forEach(th => {
            if (new Date(th.dataset.date) < cutoff) {
                wrap.querySelectorAll(`[data-col="${th.dataset.col}"]`).forEach(node => node.classList.add('is_old'));
            }
        });
        hint.hidden = false;
    }
    document.getElementById('dash_show_all')?.addEventListener('click', event => {
        event.preventDefault();
        showAll = true;
        draw();
    });

    let chart = null;  // {shown: [column index], points: {column index: [x, y]}, cross, dot}
    function render() {
        if (!box || !data.length) return;
        const shown = heads.filter(th => !th.classList.contains('is_old')).map(th => +th.dataset.col);
        chartCell.colSpan = shown.length + 1;  // the date columns plus "Zuletzt hier"
        const left = box.getBoundingClientRect().left;
        const width = box.clientWidth;
        const h = HEIGHT - PAD_TOP - PAD_BOTTOM;
        const max = Math.max(...shown.map(i => data[i].count));
        const step = niceStep(max);
        const top = Math.max(step, Math.ceil(max / step) * step);
        const y = v => PAD_TOP + h - v / top * h;
        const points = {};
        shown.forEach(i => { const r = heads[i].getBoundingClientRect(); points[i] = [r.left + r.width / 2 - left, y(data[i].count)]; });

        const svg = el('svg', { width, height: HEIGHT, viewBox: `0 0 ${width} ${HEIGHT}`, 'aria-hidden': 'true' });
        // narrow, right-aligned in the name column (an SVG without a width counts as 300px wide)
        const TICKS_WIDTH = 36;
        const ticks = el('svg', { width: TICKS_WIDTH, height: HEIGHT, 'aria-hidden': 'true' });
        // recessive grid: solid hairlines one step off the surface; tick labels in the name column
        for (let v = 0; v <= top; v += step) {
            el('line', { x1: 0, x2: width, y1: y(v), y2: y(v), stroke: css('--grid'), 'stroke-width': 1 }, svg);
            el('text', { x: TICKS_WIDTH - 8, y: y(v), dy: '0.32em', 'text-anchor': 'end', class: 'group_dash__tick' }, ticks).textContent = v;
        }
        // area wash and 2px line in the series colour, one point per shown column
        const ordered = shown.map(i => points[i]);
        const line = ordered.map((p, k) => (k ? 'L' : 'M') + p[0].toFixed(1) + ',' + p[1].toFixed(1)).join('');
        if (ordered.length > 1) {
            el('path', { d: `${line}L${ordered[ordered.length - 1][0]},${y(0)}L${ordered[0][0]},${y(0)}Z`, fill: css('--series'), 'fill-opacity': 0.1 }, svg);
            el('path', { d: line, fill: 'none', stroke: css('--series'), 'stroke-width': 2, 'stroke-linejoin': 'round', 'stroke-linecap': 'round' }, svg);
        }
        // the latest value: end dot and direct label, in the "Zuletzt hier" column
        const last = ordered[ordered.length - 1];
        el('circle', { cx: last[0], cy: last[1], r: 4, fill: css('--series'), stroke: css('--surface'), 'stroke-width': 2 }, svg);
        el('text', { x: last[0] + 10, y: last[1], dy: '0.32em', class: 'group_dash__value' }, svg).textContent = `${data[data.length - 1].count} zuletzt`;
        // crosshair and hover dot, hidden until a column is hovered
        const cross = el('line', { y1: PAD_TOP, y2: HEIGHT - PAD_BOTTOM, stroke: css('--crosshair'), 'stroke-width': 1, visibility: 'hidden' }, svg);
        const dot = el('circle', { r: 4, fill: css('--series'), stroke: css('--surface'), 'stroke-width': 2, visibility: 'hidden' }, svg);
        box.replaceChildren(svg);
        yaxis.replaceChildren(ticks);
        chart = { shown, points, cross, dot };
    }

    let current = null;
    function select(i, clientX, clientY, extra) {
        if (!chart.points[i]) return;
        current = i;
        markColumn(i);
        const [px, py] = chart.points[i];
        [chart.cross, chart.dot].forEach(node => node.setAttribute('visibility', 'visible'));
        chart.cross.setAttribute('x1', px); chart.cross.setAttribute('x2', px);
        chart.dot.setAttribute('cx', px); chart.dot.setAttribute('cy', py);
        const r = box.getBoundingClientRect();
        showTip(extra || [[`${data[i].count} Teilnehmende`, true], [data[i].label]],
            clientX ?? r.left + px, clientY ?? r.top + py);
    }
    function clear() {
        current = null;
        markColumn(null);
        if (chart) [chart.cross, chart.dot].forEach(node => node.setAttribute('visibility', 'hidden'));
        tip.hidden = true;
    }

    // hover on the chart: snap to the nearest shown column
    box.addEventListener('pointermove', event => {
        const px = event.clientX - box.getBoundingClientRect().left;
        const nearest = chart.shown.reduce((best, i) => Math.abs(chart.points[i][0] - px) < Math.abs(chart.points[best][0] - px) ? i : best);
        select(nearest, event.clientX, event.clientY);
    });
    box.addEventListener('pointerleave', clear);
    // keyboard: the same readout with the arrow keys, over the shown columns
    box.addEventListener('keydown', event => {
        if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return;
        event.preventDefault();
        const at = chart.shown.indexOf(current);
        const k = current === null ? chart.shown.length - 1 : at + (event.key === 'ArrowRight' ? 1 : -1);
        select(chart.shown[Math.min(chart.shown.length - 1, Math.max(0, k))]);
    });
    box.addEventListener('blur', clear);

    // hover on a heatmap cell: its tooltip (data-tip: first line bold, then the rest, e.g. the names
    // in the "Andere" row), and the same column marked in the chart
    wrap.addEventListener('pointerover', event => {
        const cell = event.target.closest('[data-tip]');
        if (!cell) return;
        const [head, ...rest] = cell.dataset.tip.split('|');
        const r = cell.getBoundingClientRect();
        select(+cell.closest('[data-col]').dataset.col, r.left + r.width / 2, r.top, [[head, true], ...rest.map(line => [line])]);
    });
    wrap.addEventListener('pointerleave', clear);

    // newest trainings are on the right; redrawn when the layout changes (fonts, window size)
    function draw() {
        // measure the full width first, without the previous drawing (its fixed width would count)
        if (box) box.replaceChildren();
        if (chartCell) chartCell.colSpan = heads.length + 1;
        restrict();
        render();
        wrap.scrollLeft = wrap.scrollWidth;
    }
    draw();
    window.addEventListener('load', draw);
    let resize;
    window.addEventListener('resize', () => { clearTimeout(resize); resize = setTimeout(draw, 150); });
})();
