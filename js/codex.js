/* The documents, read in the same type as the saga. */
(function () {
  'use strict';
  var S = window.Sarn;
  S.initChrome();

  var nav = document.getElementById('doc-nav');
  var panel = document.getElementById('doc-panel');
  var book = null;
  var loading = 0;

  S.getBook().then(function (b) {
    book = b;
    buildNav();
    var params = S.parseHash();
    var docs = book.codex || [];
    var lore = book.lore || [];
    var doc = docs.filter(function (d) { return d.slug === params.codex; })[0];
    if (doc) selectDoc(doc);
    else if (params.lore !== undefined && lore[Number(params.lore)]) selectLore(Number(params.lore));
    else if (docs.length) selectDoc(docs[0]);
    else if (lore.length) selectLore(0);
    else panel.replaceChildren(S.el('p', 'toc-empty', 'No documents have been copied out yet.'));
  }).catch(function (err) {
    S.fail(document.getElementById('codex-error'), 'The Codex', err, function () { window.location.reload(); });
    nav.replaceChildren();
    panel.replaceChildren();
  });

  function buildNav() {
    nav.replaceChildren();
    var docs = book.codex || [];
    var lore = book.lore || [];
    if (docs.length) {
      nav.appendChild(S.el('h3', null, 'The Codex of Sarn'));
      docs.forEach(function (doc) {
        var a = S.el('a', null, doc.title);
        a.href = '#codex=' + encodeURIComponent(doc.slug);
        a.dataset.codex = doc.slug;
        a.addEventListener('click', function (e) { e.preventDefault(); selectDoc(doc); });
        nav.appendChild(a);
      });
    }
    if (lore.length) {
      nav.appendChild(S.el('h3', null, 'The Compendium'));
      lore.forEach(function (item, i) {
        var a = S.el('a', null, item.title);
        a.href = '#lore=' + i;
        a.dataset.lore = String(i);
        a.addEventListener('click', function (e) { e.preventDefault(); selectLore(i); });
        nav.appendChild(a);
      });
    }
  }

  function markNav(attr, value) {
    Array.prototype.forEach.call(nav.querySelectorAll('a'), function (a) {
      if (a.getAttribute(attr) === String(value)) a.setAttribute('aria-current', 'true');
      else a.removeAttribute('aria-current');
    });
  }

  function selectDoc(doc) {
    if (!doc) return;
    var at = ++loading;
    panel.replaceChildren(S.el('p', 'loading-note', 'Taking a leaf from the book…'));
    markNav('data-codex', doc.slug);
    S.setHash({ codex: doc.slug });
    S.getText(doc.html).then(function (html) {
      if (at !== loading) return;
      var head = S.el('div', 'document-head');
      head.appendChild(S.el('p', 'doc-kind', doc.kind || 'A document of Sarn'));
      head.appendChild(S.el('h1', null, doc.title));
      if (doc.provenance) head.appendChild(S.el('p', 'doc-prov', doc.provenance));
      var prose = S.el('div', 'prose');
      prose.innerHTML = html; /* the press's own transcription */
      panel.replaceChildren(head, prose);
      window.scrollTo(0, 0);
    }).catch(function (err) {
      if (at !== loading) return;
      S.fail(panel, 'This document', err, function () { selectDoc(doc); });
    });
  }

  function selectLore(i) {
    var item = (book.lore || [])[i];
    if (!item) return;
    var at = ++loading;
    panel.replaceChildren(S.el('p', 'loading-note', 'Taking a leaf from the book…'));
    markNav('data-lore', i);
    S.setHash({ lore: i });
    S.getText(item.html).then(function (html) {
      if (at !== loading) return;
      var head = S.el('div', 'document-head');
      head.appendChild(S.el('p', 'doc-kind', 'From the Compendium of Sarn'));
      head.appendChild(S.el('h1', null, item.title));
      var prose = S.el('div', 'prose');
      prose.innerHTML = html;
      panel.replaceChildren(head, prose);
      window.scrollTo(0, 0);
    }).catch(function (err) {
      if (at !== loading) return;
      S.fail(panel, 'This section', err, function () { selectLore(i); });
    });
  }

  window.addEventListener('hashchange', function () {
    if (!book) return;
    var params = S.parseHash();
    var doc = (book.codex || []).filter(function (d) { return d.slug === params.codex; })[0];
    if (doc) { selectDoc(doc); return; }
    if (params.lore !== undefined && (book.lore || [])[Number(params.lore)]) selectLore(Number(params.lore));
  });
})();
