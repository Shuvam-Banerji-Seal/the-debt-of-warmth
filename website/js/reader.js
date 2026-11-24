/* The reading room: one chapter at a time, every day within reach. */
(function () {
  'use strict';
  var S = window.Sarn;
  S.initChrome();

  var flow = document.getElementById('chapter-flow');
  var crumb = document.getElementById('crumb');
  var progress = document.getElementById('progress-bar');
  var tocDrawer = document.getElementById('toc-drawer');
  var settingsDrawer = document.getElementById('settings-drawer');
  var tocToggle = document.getElementById('toc-toggle');
  var settingsToggle = document.getElementById('settings-toggle');
  var scrim = document.getElementById('scrim');
  var tocList = document.getElementById('toc-list');
  var tocResults = document.getElementById('toc-results');
  var tocSearch = document.getElementById('toc-search');
  var prevLink = document.getElementById('prev-ch');
  var nextLink = document.getElementById('next-ch');
  var pdfLink = document.getElementById('chapter-pdf');
  var continueBox = document.getElementById('continue-next');
  var continueText = document.getElementById('continue-next-text');
  var appendBtn = document.getElementById('append-next');
  var banner = document.getElementById('continue-banner');

  var book = null;
  var current = null;
  var currentDayId = null;
  var lastSave = 0;
  var queued = false;
  var userMoved = false;
  var lastTrigger = null;
  var suppressSpyUntil = 0;
  var reduceMotion = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);

  bindUI();
  boot();

  /* ---------- data helpers ---------- */
  function chapters() { return book && Array.isArray(book.chapters) ? book.chapters : []; }
  function chapterByN(n) {
    n = Number(n);
    return chapters().filter(function (c) { return c.n === n; })[0] || null;
  }
  function chapterAt(i) { return chapters()[i] || null; }

  function findDay(n) {
    var list = chapters();
    for (var i = 0; i < list.length; i++) {
      var ch = list[i];
      if (n >= Number(ch.day_start) && n <= Number(ch.day_end)) {
        var days = ch.days || [];
        var d = days.filter(function (x) { return x.label === 'Day ' + n; })[0];
        if (!d) d = days[n - Number(ch.day_start)];
        if (d) return { ch: ch, day: d };
      }
    }
    return null;
  }

  /* ---------- boot and chapter rendering ---------- */
  function boot() {
    S.getBook().then(function (b) {
      book = b;
      buildTOC();
      syncSettings();

      var params = S.parseHash();
      var asked = Number(params.ch);
      var saved = S.store.get(S.KEY_POSITION, null);

      if (asked && chapterByN(asked)) {
        openChapter(asked, params.day || null, false, 0);
      } else if (saved && chapterByN(saved.chapter)) {
        openChapter(saved.chapter, saved.dayId || null, true, Number(saved.scroll) || 0);
      } else {
        var first = chapterAt(0);
        if (first) openChapter(first.n, null, false, 0);
        else S.fail(flow, 'The chapters', new Error('the manifest holds none'));
      }
      if (saved && chapterByN(saved.chapter)) showResume(saved);
    }).catch(function (err) {
      S.fail(flow, 'The book', err, function () { window.location.reload(); });
    });
  }

  function buildUnit(ch, html) {
    var unit = S.el('section', 'chapter-unit');
    unit.id = 'unit-' + ch.n;

    if (ch.plate) {
      var fig = S.el('figure', 'plate-figure');
      var img = document.createElement('img');
      img.src = ch.plate;
      img.alt = ch.caption || ('Illustration for chapter ' + ch.n + ': ' + ch.title);
      img.loading = 'lazy';
      img.width = 1024;
      img.height = 1536;
      fig.appendChild(img);
      if (ch.caption) fig.appendChild(S.el('figcaption', null, ch.caption));
      unit.appendChild(fig);
    }

    var prose = S.el('div', 'prose chapter-fragment');
    prose.innerHTML = html; /* the press's own fragment */
    unit.appendChild(prose);
    unit.appendChild(S.el('p', 'unit-end', '❦'));
    return unit;
  }

  function openChapter(n, dayId, restore, scrollY) {
    n = Number(n);
    var ch = chapterByN(n);
    if (!ch) {
      S.fail(flow, 'Chapter ' + n, new Error('no such chapter is in the manifest'));
      return;
    }
    if (current && current.n === n && flow.querySelector('.chapter-unit')) {
      if (dayId) gotoDay(dayId);
      else if (restore && scrollY > 0) restoreScroll(scrollY);
      else window.scrollTo(0, 0);
      S.setHash({ ch: n, day: dayId || null });
      return;
    }

    flow.setAttribute('aria-busy', 'true');
    S.getText(ch.html).then(function (html) {
      flow.replaceChildren(buildUnit(ch, html));
      flow.setAttribute('aria-busy', 'false');
      current = ch;
      currentDayId = null;
      updateChrome();
      markCurrent();
      if (dayId) suppressSpyUntil = Date.now() + 900;
      S.setHash({ ch: n, day: dayId || null });

      if (dayId) {
        window.requestAnimationFrame(function () { gotoDay(dayId); });
      } else if (restore && scrollY > 0) {
        restoreScroll(scrollY);
      } else {
        window.scrollTo(0, 0);
      }
      savePosition(true);
    }).catch(function (err) {
      flow.setAttribute('aria-busy', 'false');
      S.fail(flow, 'Chapter ' + n, err, function () { openChapter(n, dayId, restore, scrollY); });
    });
  }

  function restoreScroll(y) {
    userMoved = false;
    window.requestAnimationFrame(function () {
      window.requestAnimationFrame(function () {
        if (!userMoved) window.scrollTo(0, y);
      });
    });
    window.setTimeout(function () { if (!userMoved) window.scrollTo(0, y); }, 350);
  }

  function gotoDay(id) {
    var target = document.getElementById(id);
    if (!target || !flow.contains(target)) return false;
    /* A deep link is a jump, not a glide: land on the mark at once. */
    suppressSpyUntil = Date.now() + 900;
    target.scrollIntoView({ behavior: 'auto', block: 'start' });
    currentDayId = id;
    if (current) S.setHash({ ch: current.n, day: id });
    return true;
  }

  function appendNext() {
    if (!current) return;
    var next = chapterAt(chapters().indexOf(current) + 1);
    if (!next) return;
    appendBtn.disabled = true;
    S.getText(next.html).then(function (html) {
      var unit = buildUnit(next, html);
      flow.appendChild(unit);
      current = next;
      currentDayId = null;
      updateChrome();
      markCurrent();
      suppressSpyUntil = Date.now() + 900;
      S.setHash({ ch: next.n, day: null });
      unit.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'start' });
      appendBtn.disabled = false;
      savePosition(true);
    }).catch(function (err) {
      appendBtn.disabled = false;
      S.fail(continueBox, 'The next chapter', err, appendNext);
    });
  }

  /* ---------- toolbar, navigation, chrome ---------- */
  function updateChrome() {
    if (!current) return;
    crumb.replaceChildren();
    crumb.appendChild(S.el('strong', null, 'CHAPTER ' + current.n));
    crumb.appendChild(document.createTextNode(' — ' + current.title));

    var idx = chapters().indexOf(current);
    setNav(prevLink, chapters()[idx - 1], '← The chapter before');
    var next = chapters()[idx + 1];
    setNav(nextLink, next, 'The chapter after →');

    if (current.pdf) {
      pdfLink.hidden = false;
      pdfLink.href = current.pdf;
    } else {
      pdfLink.hidden = true;
    }

    if (next) {
      continueBox.hidden = false;
      continueText.textContent = 'Chapter ' + next.n + ' waits beyond this page — “' + next.title + '”. You may keep reading without lifting your eyes.';
    } else {
      continueBox.hidden = true;
    }
  }

  function setNav(a, ch, label) {
    if (!a) return;
    if (!ch) { a.hidden = true; return; }
    a.hidden = false;
    a.href = 'read.html#ch=' + ch.n;
    a.dataset.n = String(ch.n);
    a.replaceChildren();
    a.appendChild(S.el('span', 'nav-label', label));
    a.appendChild(S.el('span', 'nav-title', ch.title));
  }

  function markCurrent() {
    if (!current) return;
    Array.prototype.forEach.call(document.querySelectorAll('.toc-chapter > a'), function (a) {
      a.removeAttribute('aria-current');
    });
    Array.prototype.forEach.call(document.querySelectorAll('.toc-days a'), function (a) {
      a.removeAttribute('aria-current');
    });
    var row = tocList.querySelector('.toc-chapter[data-chapter="' + current.n + '"]');
    if (row && row.children.length) row.children[0].setAttribute('aria-current', 'true');
    if (currentDayId) {
      var dayLink = tocList.querySelector('.toc-days a[href*="day=' + currentDayId + '"]');
      if (dayLink) dayLink.setAttribute('aria-current', 'true');
    }
  }

  function showResume(saved) {
    var ch = chapterByN(saved.chapter);
    if (!ch) return;
    var dayLabel = '';
    if (saved.dayId) {
      var d = (ch.days || []).filter(function (x) { return x.id === saved.dayId; })[0];
      if (d) dayLabel = ', ' + d.label;
    }
    document.getElementById('resume-text').textContent =
      'Chapter ' + ch.n + ' — ' + ch.title + dayLabel + '.';
    document.getElementById('resume-jump').addEventListener('click', function () {
      closeDrawers(false);
      openChapter(ch.n, saved.dayId || null, true, Number(saved.scroll) || 0);
    });
    var first = chapterAt(0);
    if (first) document.getElementById('resume-start').href = 'read.html#ch=' + first.n;
    banner.hidden = false;
  }

  /* ---------- the contents drawer ---------- */
  function buildTOC() {
    tocList.replaceChildren();
    var arcs = book.arcs || [];
    if (!arcs.length) {
      tocList.appendChild(S.el('p', 'toc-empty', 'No arcs are recorded yet.'));
      return;
    }
    arcs.forEach(function (arc) {
      var details = S.el('details', 'toc-arc');
      details.appendChild(S.el('summary', null, arc.number + '. ' + arc.title));
      var wrap = S.el('div', 'toc-chapters');
      details.appendChild(wrap);
      details.addEventListener('toggle', function () {
        if (details.open && !details.dataset.populated) {
          populateArc(arc, wrap);
          details.dataset.populated = '1';
          markCurrent();
        }
      });
      tocList.appendChild(details);
    });
  }

  function populateArc(arc, wrap) {
    (arc.chapters || []).forEach(function (n) {
      var ch = chapterByN(n);
      if (!ch) return;
      var row = S.el('div', 'toc-chapter');
      row.dataset.chapter = String(ch.n);

      var a = S.el('a');
      a.href = 'read.html#ch=' + ch.n;
      a.appendChild(S.el('span', 'num', String(ch.n).padStart(4, '0')));
      a.appendChild(document.createTextNode(ch.title));
      a.addEventListener('click', function (e) {
        e.preventDefault();
        closeDrawers(false);
        openChapter(ch.n, null, false, 0);
      });
      row.appendChild(a);

      var days = ch.days || [];
      if (days.length) {
        var ul = S.el('ul', 'toc-days');
        days.forEach(function (day) {
          var da = S.el('a', null, String(day.label).replace(/^Day\s*/, ''));
          da.href = 'read.html#ch=' + ch.n + '&day=' + encodeURIComponent(day.id);
          da.title = day.label;
          da.addEventListener('click', function (e) {
            e.preventDefault();
            closeDrawers(false);
            openChapter(ch.n, day.id, false, 0);
          });
          ul.appendChild(da);
        });
        row.appendChild(ul);
      }
      wrap.appendChild(row);
    });
  }

  function doSearch() {
    var q = tocSearch.value.trim();
    if (!q) {
      tocResults.hidden = true;
      tocList.hidden = false;
      return;
    }
    tocList.hidden = true;
    tocResults.hidden = false;
    tocResults.replaceChildren();

    var items = [];
    var m = /^(?:chapter|ch)\s*#?(\d+)$/i.exec(q) || /^#?(\d+)$/.exec(q);
    if (m) {
      var ch = chapterByN(m[1]);
      if (ch) items.push({ ch: ch, label: 'Chapter ' + ch.n });
    } else if ((m = /^day\s*#?(\d+)$/i.exec(q))) {
      var found = findDay(Number(m[1]));
      if (found) items.push({ ch: found.ch, label: found.day.label, dayId: found.day.id });
    } else {
      var needle = q.toLowerCase();
      chapters().filter(function (c) {
        return String(c.title).toLowerCase().indexOf(needle) >= 0;
      }).slice(0, 250).forEach(function (c) {
        items.push({ ch: c, label: c.title });
      });
    }

    if (!items.length) {
      tocResults.appendChild(S.el('p', 'toc-empty', 'No chapter answers to that. Try a number, a day, or a word from a title.'));
      return;
    }
    items.forEach(function (item) {
      var hash = 'ch=' + item.ch.n + (item.dayId ? '&day=' + encodeURIComponent(item.dayId) : '');
      var a = S.el('a', 'toc-result');
      a.href = 'read.html#' + hash;
      a.appendChild(document.createTextNode(item.label));
      a.appendChild(S.el('small', null, 'Chapter ' + item.ch.n + ' · ' + item.ch.title));
      a.addEventListener('click', function (e) {
        e.preventDefault();
        closeDrawers(false);
        openChapter(item.ch.n, item.dayId || null, false, 0);
      });
      tocResults.appendChild(a);
    });
  }

  /* ---------- drawers ---------- */
  function anyOpen() {
    return tocDrawer.classList.contains('open') || settingsDrawer.classList.contains('open');
  }
  function openDrawer(kind) {
    closeDrawers(false);
    var drawer = kind === 'toc' ? tocDrawer : settingsDrawer;
    var toggle = kind === 'toc' ? tocToggle : settingsToggle;
    drawer.classList.add('open');
    drawer.setAttribute('aria-hidden', 'false');
    toggle.setAttribute('aria-expanded', 'true');
    scrim.hidden = false;
    lastTrigger = toggle;
    (kind === 'toc' ? tocSearch : document.getElementById('set-size')).focus();
  }
  function closeDrawers(restoreFocus) {
    if (!anyOpen()) return;
    tocDrawer.classList.remove('open');
    settingsDrawer.classList.remove('open');
    tocDrawer.setAttribute('aria-hidden', 'true');
    settingsDrawer.setAttribute('aria-hidden', 'true');
    tocToggle.setAttribute('aria-expanded', 'false');
    settingsToggle.setAttribute('aria-expanded', 'false');
    scrim.hidden = true;
    if (restoreFocus && lastTrigger && typeof lastTrigger.focus === 'function') lastTrigger.focus();
  }
  function toggleDrawer(kind) {
    var drawer = kind === 'toc' ? tocDrawer : settingsDrawer;
    if (drawer.classList.contains('open')) closeDrawers(true);
    else openDrawer(kind);
  }

  /* ---------- settings ---------- */
  function syncSettings() {
    var s = S.settings;
    document.getElementById('set-size').value = s.fontSize;
    document.getElementById('set-leading').value = s.lineHeight;
    document.getElementById('set-width').value = s.textWidth;
    document.getElementById('set-face').value = s.face;
    document.getElementById('out-size').textContent = s.fontSize + ' px';
    document.getElementById('out-leading').textContent = Number(s.lineHeight).toFixed(2);
    document.getElementById('out-width').textContent = s.textWidth + ' rem';
    Array.prototype.forEach.call(document.querySelectorAll('[data-theme-choice]'), function (btn) {
      btn.setAttribute('aria-pressed', btn.getAttribute('data-theme-choice') === s.theme ? 'true' : 'false');
    });
  }

  function bindSettings() {
    var ranges = [
      ['set-size', 'fontSize', 'out-size', function (v) { return v + ' px'; }],
      ['set-leading', 'lineHeight', 'out-leading', function (v) { return Number(v).toFixed(2); }],
      ['set-width', 'textWidth', 'out-width', function (v) { return v + ' rem'; }]
    ];
    ranges.forEach(function (spec) {
      var input = document.getElementById(spec[0]);
      input.addEventListener('input', function () {
        var value = Number(input.value);
        var patch = {};
        patch[spec[1]] = value;
        S.saveSettings(patch);
        document.getElementById(spec[2]).textContent = spec[3](input.value);
      });
    });
    document.getElementById('set-face').addEventListener('change', function (e) {
      S.saveSettings({ face: e.target.value });
    });
    Array.prototype.forEach.call(document.querySelectorAll('[data-theme-choice]'), function (btn) {
      btn.addEventListener('click', function () {
        S.saveSettings({ theme: btn.getAttribute('data-theme-choice') });
        syncSettings();
      });
    });
    document.getElementById('reset-settings').addEventListener('click', function () {
      S.resetSettings();
      syncSettings();
    });
  }

  /* ---------- progress, position, keys ---------- */
  function savePosition(force) {
    if (!current) return;
    var now = Date.now();
    if (!force && now - lastSave < 220) return;
    lastSave = now;
    S.store.set(S.KEY_POSITION, {
      chapter: current.n,
      dayId: currentDayId,
      scroll: Math.round(window.scrollY || window.pageYOffset || 0),
      title: current.title,
      savedAt: new Date().toISOString()
    });
  }

  function onScroll() {
    queued = false;
    var y = window.scrollY || window.pageYOffset || 0;
    var max = Math.max(0, document.documentElement.scrollHeight - window.innerHeight);
    progress.style.width = (max > 0 ? Math.min(100, Math.max(0, y / max * 100)) : 0) + '%';

    var units = flow.querySelectorAll('.chapter-unit');
    var active = null;
    for (var i = 0; i < units.length; i++) {
      if (units[i].getBoundingClientRect().top <= 160) active = units[i];
    }
    if (active && current) {
      var n = Number(String(active.id).replace('unit-', ''));
      if (n !== current.n) {
        var c = chapterByN(n);
        if (c) { current = c; updateChrome(); markCurrent(); }
      }
      var marks = active.querySelectorAll('.daymark[id]');
      var day = null;
      for (var j = 0; j < marks.length; j++) {
        if (marks[j].getBoundingClientRect().top <= 190) day = marks[j].id;
      }
      if (day !== currentDayId) {
        currentDayId = day;
        S.setHash({ ch: current.n, day: day });
      }
    }
    savePosition(false);
  }

  function goRelative(delta) {
    if (!current) return;
    var next = chapterAt(chapters().indexOf(current) + delta);
    if (next) openChapter(next.n, null, false, 0);
  }

  function bindUI() {
    tocToggle.addEventListener('click', function () { toggleDrawer('toc'); });
    settingsToggle.addEventListener('click', function () { toggleDrawer('settings'); });
    scrim.addEventListener('click', function () { closeDrawers(true); });
    Array.prototype.forEach.call(document.querySelectorAll('[data-close]'), function (btn) {
      btn.addEventListener('click', function () { closeDrawers(true); });
    });
    tocSearch.addEventListener('input', doSearch);

    bindSettings();

    [[prevLink, -1], [nextLink, 1]].forEach(function (pair) {
      pair[0].addEventListener('click', function (e) {
        if (!pair[0].dataset.n) return;
        e.preventDefault();
        openChapter(Number(pair[0].dataset.n), null, false, 0);
      });
    });
    appendBtn.addEventListener('click', appendNext);
    document.getElementById('resume-dismiss').addEventListener('click', function () { banner.hidden = true; });

    window.addEventListener('scroll', function () {
      if (!queued) { queued = true; window.requestAnimationFrame(onScroll); }
    }, { passive: true });
    ['wheel', 'touchstart', 'keydown'].forEach(function (type) {
      window.addEventListener(type, function () { userMoved = true; }, { passive: true });
    });
    window.addEventListener('pagehide', function () { savePosition(true); });
    document.addEventListener('visibilitychange', function () {
      if (document.visibilityState === 'hidden') savePosition(true);
    });

    window.addEventListener('hashchange', function () {
      if (!book) return;
      var params = S.parseHash();
      var n = Number(params.ch);
      if (n && chapterByN(n)) {
        if (current && current.n === n && params.day) gotoDay(params.day);
        else if (!current || current.n !== n) openChapter(n, params.day || null, false, 0);
      }
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        if (anyOpen()) { closeDrawers(true); e.preventDefault(); }
        return;
      }
      if (e.altKey || e.ctrlKey || e.metaKey) return;
      var tag = (e.target && e.target.tagName || '').toLowerCase();
      if (tag === 'input' || tag === 'select' || tag === 'textarea' || (e.target && e.target.isContentEditable)) return;
      if (anyOpen()) return;
      var key = String(e.key).toLowerCase();
      if (key === 't') { e.preventDefault(); toggleDrawer('toc'); }
      else if (key === 's') { e.preventDefault(); toggleDrawer('settings'); }
      else if (e.key === 'ArrowLeft') { e.preventDefault(); goRelative(-1); }
      else if (e.key === 'ArrowRight') { e.preventDefault(); goRelative(1); }
    });
  }
})();
