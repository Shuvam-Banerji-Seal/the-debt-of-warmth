/* The ledger of lived days, each one a door into the chapter. */
(function () {
  'use strict';
  var S = window.Sarn;
  S.initChrome();

  var ledger = document.getElementById('ledger');
  var note = document.getElementById('days-note');
  var moreWrap = document.getElementById('more-wrap');
  var jump = document.getElementById('day-jump');
  var PAGE = 50;
  var shown = PAGE;
  var book = null;
  var days = [];

  Promise.all([S.getBook(), S.getJSON('data/timeline.json')]).then(function (results) {
    book = results[0];
    days = Array.isArray(results[1]) ? results[1] : [];
    days.sort(function (a, b) { return Number(a.day) - Number(b.day); });
    render();
  }).catch(function (err) {
    S.fail(document.getElementById('days-error'), 'The reckoning', err, function () { window.location.reload(); });
    note.textContent = '';
    moreWrap.hidden = true;
  });

  document.getElementById('more-days').addEventListener('click', function () {
    shown += PAGE;
    render();
  });
  document.getElementById('day-clear').addEventListener('click', function () {
    jump.value = '';
    shown = PAGE;
    render();
  });
  jump.addEventListener('change', function () {
    shown = PAGE;
    render();
  });

  function readerLink(dayNumber) {
    var n = Number(dayNumber);
    var chapters = book.chapters || [];
    for (var i = 0; i < chapters.length; i++) {
      var c = chapters[i];
      if (n >= Number(c.day_start) && n <= Number(c.day_end)) {
        var day = (c.days || []).filter(function (d) { return d.label === 'Day ' + n; })[0];
        if (!day) day = c.days[n - Number(c.day_start)];
        var hash = 'ch=' + c.n + (day && day.id ? '&day=' + encodeURIComponent(day.id) : '');
        return 'read.html#' + hash;
      }
    }
    return 'read.html';
  }

  function makeRow(entry) {
    var row = S.el('div', 'ledger-row');
    var href = readerLink(entry.day);
    var left = S.el('div', 'ledger-day');
    var dayLink = S.el('a', null, 'Day ' + entry.day);
    dayLink.href = href;
    left.appendChild(dayLink);
    left.appendChild(S.el('small', null, 'read the day ❧'));
    row.appendChild(left);

    var body = S.el('div', 'ledger-text');
    var parts = String(entry.text || '').split('|').map(function (s) { return s.trim(); });
    var date = parts[0] || '';
    var place = parts.length > 2 ? parts[1] : '';
    var what = parts.length > 2 ? parts.slice(2).join(' | ') : (parts[1] || '');

    if (date) body.appendChild(S.el('span', 'date', date));
    if (place) body.appendChild(S.el('span', 'place', place));
    if (what) {
      var span = S.el('span', 'what', what);
      span.appendChild(document.createTextNode(' '));
      var more = S.el('a', null, 'Read this day ❧');
      more.href = href;
      span.appendChild(more);
      body.appendChild(span);
    }
    row.appendChild(body);
    return row;
  }

  function render() {
    if (!book) return;
    ledger.replaceChildren();
    var wanted = Number(jump.value);
    var list = days;
    if (isFinite(wanted) && wanted > 0) {
      list = days.filter(function (d) { return Number(d.day) === wanted; });
      note.textContent = list.length ? 'One day, entered below.' : 'No such day has been lived yet.';
      moreWrap.hidden = true;
    } else {
      var visible = days.slice(0, shown);
      note.textContent = S.fmt(days.length) + ' days entered so far · showing ' + S.fmt(visible.length) + '.';
      moreWrap.hidden = shown >= days.length;
      list = visible;
    }
    if (!list.length) {
      ledger.appendChild(S.el('p', 'toc-empty', 'The ledger is empty for that number.'));
      return;
    }
    list.forEach(function (entry) { ledger.appendChild(makeRow(entry)); });
  }
})();
