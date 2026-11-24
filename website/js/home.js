/* The landing page: live numbers, doors into the book. */
(function () {
  'use strict';
  var S = window.Sarn;
  S.initChrome();

  var errorBox = document.getElementById('home-error');
  var stats = document.getElementById('stats');
  var arcs = document.getElementById('arcs');
  S.addCorners(document.querySelector('.hero'));

  S.getBook().then(function (book) {
    renderActions(book);
    renderStats(book);
    renderArcs(book);
    renderTeasers(book);
  }).catch(function (err) {
    S.fail(errorBox, 'The book', err, function () { globalThis.location.reload(); });
    [stats, arcs].forEach(function (node) { node.textContent = ''; });
  });

  function renderActions(book) {
    var chapters = Array.isArray(book.chapters) ? book.chapters : [];
    var begin = document.querySelector('a[href^="read.html#ch="]');
    if (begin && chapters.length) {
      begin.href = 'read.html#ch=' + chapters[0].n;
    }

    var saved = S.store.get(S.KEY_POSITION, null);
    var cont = document.getElementById('continue-btn');
    if (saved && saved.chapter && chapters.some(function (c) { return c.n === saved.chapter; })) {
      cont.removeAttribute('aria-disabled');
      var where = chapters.filter(function (c) { return c.n === saved.chapter; })[0];
      cont.href = 'read.html';
      cont.title = 'Chapter ' + saved.chapter + (where ? ': ' + where.title : '');
      cont.appendChild(S.el('small', null, '  Chapter ' + saved.chapter));
    } else {
      cont.setAttribute('aria-disabled', 'true');
      cont.title = 'No saved place yet';
    }

    var byline = document.getElementById('byline');
    if (byline && book.byline) byline.textContent = book.byline;

    [['epub-btn', 'epub'], ['pdf-btn', 'pdf']].forEach(function (pair) {
      var link = document.getElementById(pair[0]);
      var url = book.downloads && book.downloads[pair[1]];
      if (link && url) {
        link.href = url;
        link.removeAttribute('aria-disabled');
      }
    });
  }

  function renderStats(book) {
    var chapters = Array.isArray(book.chapters) ? book.chapters : [];
    var characters = Array.isArray(book.characters) ? book.characters : [];
    var days = chapters.reduce(function (max, c) { return Math.max(max, Number(c.day_end) || 0); }, 0);
    var values = [
      S.fmt(chapters.length),
      S.fmt(book.words_total || 0),
      S.fmt(days),
      S.fmt(characters.filter(function (c) { return c.appeared !== false; }).length)
    ];
    stats.replaceChildren();
    var labels = ['Chapters', 'Words set down', 'Days lived', 'Characters met'];
    values.forEach(function (value, i) {
      var cell = S.el('div', 'stat');
      cell.appendChild(S.el('span', 'num', value));
      cell.appendChild(S.el('span', 'label', labels[i]));
      stats.appendChild(cell);
    });
  }

  function renderArcs(book) {
    var arcsData = Array.isArray(book.arcs) ? book.arcs : [];
    var chapters = Array.isArray(book.chapters) ? book.chapters : [];
    var byNumber = {};
    chapters.forEach(function (c) { byNumber[c.n] = c; });
    arcs.replaceChildren();
    if (!arcsData.length) {
      arcs.appendChild(S.el('p', 'toc-empty', 'The arcs are not yet set out.'));
      return;
    }
    arcsData.forEach(function (arc) {
      var list = (arc.chapters || []).map(function (n) { return byNumber[n]; }).filter(Boolean);
      var item = S.el('section', 'arc-item');
      var heading = S.el('h3', null, 'Arc ' + arc.number + ' — ' + arc.title);
      item.appendChild(heading);
      if (arc.subtitle) item.appendChild(S.el('p', 'arc-sub', arc.subtitle));
      var ul = S.el('ul', 'arc-chapters');
      var shown = 0;
      list.forEach(function (ch) {
        var li = document.createElement('li');
        var a = document.createElement('a');
        a.href = 'read.html#ch=' + ch.n;
        a.title = ch.title;
        a.appendChild(S.el('span', 'num', String(ch.n).padStart(4, '0')));
        a.appendChild(document.createTextNode(ch.title));
        li.appendChild(a);
        if (shown < 12) { ul.appendChild(li); shown++; }
        else { li.hidden = true; ul.appendChild(li); }
      });
      item.appendChild(ul);
      if (list.length > 12) {
        var more = S.el('button', 'arc-more', 'Show all ' + list.length + ' chapters ❧');
        more.type = 'button';
        more.addEventListener('click', function () {
          Array.prototype.forEach.call(ul.children, function (li) { li.hidden = false; });
          more.remove();
        });
        item.appendChild(more);
      }
      arcs.appendChild(item);
    });
  }

  function renderTeasers(book) {
    var cast = document.getElementById('teaser-cast');
    var atlas = document.getElementById('teaser-atlas');
    var codex = document.getElementById('teaser-codex');

    var met = (book.characters || []).filter(function (c) { return c.appeared !== false; });
    cast.appendChild(S.el('h3', null, 'The Cast'));
    cast.appendChild(S.el('span', 'teaser-names', met.slice(0, 4).map(function (c) { return c.name; }).join(' · ')));
    cast.appendChild(S.el('p', null, met.length + ' souls met so far; more wait in the dark of later chapters.'));
    cast.appendChild(link('Meet them', 'cast.html'));

    var maps = book.maps || [];
    if (maps.length && maps[0].image) {
      var img = document.createElement('img');
      img.src = maps[0].image;
      img.alt = 'A map: ' + maps[0].title;
      img.loading = 'lazy';
      atlas.appendChild(img);
    }
    atlas.appendChild(S.el('h3', null, 'The Atlas'));
    atlas.appendChild(S.el('p', null, maps.length + ' surveyed places, inked in the Thin Year. Zoom in; follow the river.'));
    atlas.appendChild(link('Open the atlas', 'atlas.html'));

    var docs = book.codex || [];
    codex.appendChild(S.el('h3', null, 'The Codex of Sarn'));
    codex.appendChild(S.el('span', 'teaser-names', docs.slice(0, 3).map(function (d) { return d.title; }).join(' · ')));
    codex.appendChild(S.el('p', null, 'Work songs, slates, litanies and ordinances, copied out by hands that left their marks.'));
    codex.appendChild(link('Read the documents', 'codex.html'));
  }

  function link(text, href) {
    var a = S.el('a', 'btn btn--quiet', text + ' ❧');
    a.href = href;
    return a;
  }
})();
