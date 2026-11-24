/* Maps, and a glass through which to read them. */
(function () {
  'use strict';
  var S = window.Sarn;
  S.initChrome();

  var wrap = document.getElementById('atlas-grid-wrap');
  var dialog = document.getElementById('map-dialog');
  var viewport = document.getElementById('map-viewport');
  var image = document.getElementById('map-image');
  var caption = document.getElementById('map-caption');
  var title = document.getElementById('map-title');

  var scale = 1, tx = 0, ty = 0, dragging = false, lastX = 0, lastY = 0;

  S.getBook().then(function (book) {
    var maps = Array.isArray(book.maps) ? book.maps : [];
    var grid = S.el('ul', 'atlas-grid');
    if (!maps.length) grid.appendChild(S.el('p', 'toc-empty', 'No maps have been surveyed yet.'));
    maps.forEach(function (map) { grid.appendChild(makeCard(map)); });
    wrap.replaceChildren(grid);
  }).catch(function (err) {
    S.fail(wrap, 'The atlas', err, function () { window.location.reload(); });
  });

  function makeCard(map) {
    var li = document.createElement('li');
    var btn = S.el('button', 'map-card');
    btn.type = 'button';
    var img = document.createElement('img');
    img.src = map.image || '';
    img.alt = 'Map: ' + map.title;
    img.loading = 'lazy';
    img.addEventListener('error', function () { img.alt = 'The map could not be drawn: ' + map.title; });
    btn.appendChild(img);
    btn.appendChild(S.el('h3', null, map.title));
    if (map.caption) btn.appendChild(S.el('p', null, map.caption));
    btn.appendChild(S.el('span', 'zoom-hint', 'Open the map ❦ zoom and pan'));
    btn.addEventListener('click', function () { openMap(map); });
    li.appendChild(btn);
    return li;
  }

  function openMap(map) {
    title.textContent = map.title;
    caption.textContent = map.caption || '';
    image.alt = 'Map: ' + map.title;
    image.src = map.image || '';
    reset();
    if (typeof dialog.showModal === 'function') dialog.showModal();
    else dialog.setAttribute('open', 'open');
    document.getElementById('zoom-in').focus();
  }

  function apply() {
    var w = image.clientWidth || 1, h = image.clientHeight || 1;
    var maxX = Math.max(0, (w * scale - viewport.clientWidth) / 2 + 40);
    var maxY = Math.max(0, (h * scale - viewport.clientHeight) / 2 + 40);
    tx = Math.min(maxX, Math.max(-maxX, tx));
    ty = Math.min(maxY, Math.max(-maxY, ty));
    image.style.transform = 'translate(' + tx + 'px,' + ty + 'px) scale(' + scale + ')';
  }

  function zoom(factor) {
    scale = Math.min(6, Math.max(1, scale * factor));
    if (scale === 1) { tx = 0; ty = 0; }
    apply();
  }

  function reset() {
    scale = 1; tx = 0; ty = 0;
    image.style.transform = '';
  }

  document.getElementById('zoom-in').addEventListener('click', function () { zoom(1.35); });
  document.getElementById('zoom-out').addEventListener('click', function () { zoom(1 / 1.35); });
  document.getElementById('zoom-reset').addEventListener('click', reset);
  document.getElementById('map-close').addEventListener('click', function () { dialog.close(); });
  dialog.addEventListener('click', function (e) { if (e.target === dialog) dialog.close(); });
  dialog.addEventListener('close', reset);

  viewport.addEventListener('wheel', function (e) {
    e.preventDefault();
    zoom(e.deltaY < 0 ? 1.18 : 1 / 1.18);
  }, { passive: false });

  viewport.addEventListener('dblclick', function () {
    if (scale > 1) reset(); else zoom(2.4);
  });

  viewport.addEventListener('pointerdown', function (e) {
    dragging = true;
    lastX = e.clientX; lastY = e.clientY;
    viewport.classList.add('dragging');
    if (viewport.setPointerCapture) viewport.setPointerCapture(e.pointerId);
  });
  viewport.addEventListener('pointermove', function (e) {
    if (!dragging) return;
    tx += e.clientX - lastX;
    ty += e.clientY - lastY;
    lastX = e.clientX; lastY = e.clientY;
    apply();
  });
  function endDrag(e) {
    if (!dragging) return;
    dragging = false;
    viewport.classList.remove('dragging');
    if (e && viewport.releasePointerCapture && viewport.hasPointerCapture && viewport.hasPointerCapture(e.pointerId)) {
      viewport.releasePointerCapture(e.pointerId);
    }
  }
  viewport.addEventListener('pointerup', endDrag);
  viewport.addEventListener('pointercancel', endDrag);

  document.addEventListener('keydown', function (e) {
    if (!dialog.open) return;
    if (e.key === '+' || e.key === '=') { e.preventDefault(); zoom(1.25); }
    else if (e.key === '-') { e.preventDefault(); zoom(1 / 1.25); }
    else if (e.key === '0') { e.preventDefault(); reset(); }
    else if (e.key === 'ArrowLeft') { e.preventDefault(); tx += 30; apply(); }
    else if (e.key === 'ArrowRight') { e.preventDefault(); tx -= 30; apply(); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); ty += 30; apply(); }
    else if (e.key === 'ArrowDown') { e.preventDefault(); ty -= 30; apply(); }
  });
})();
