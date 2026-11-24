/* The gallery of faces; a sheet opens at a touch. */
(function () {
  'use strict';
  var S = window.Sarn;
  S.initChrome();

  var wrap = document.getElementById('cast-grid-wrap');
  var grid = null;
  var dialog = document.getElementById('sheet-dialog');
  var sheetBody = document.getElementById('sheet-body');
  var sheetTitle = document.getElementById('sheet-title');
  var toggle = document.getElementById('spoilers');

  dialog.addEventListener('click', function (e) {
    if (e.target === dialog) dialog.close();
  });
  document.getElementById('sheet-close').addEventListener('click', function () { dialog.close(); });
  toggle.addEventListener('change', function () {
    if (!grid) return;
    Array.prototype.forEach.call(grid.querySelectorAll('[data-spoiler="true"]'), function (card) {
      card.hidden = !toggle.checked;
    });
  });

  S.getBook().then(function (book) {
    var people = Array.isArray(book.characters) ? book.characters : [];
    grid = S.el('ul', 'cast-grid');
    people.forEach(function (person) { grid.appendChild(makeCard(person)); });
    wrap.replaceChildren(grid);

    var unseen = people.filter(function (p) { return p.appeared === false; });
    if (unseen.length) document.getElementById('spoiler-label').hidden = false;
  }).catch(function (err) {
    S.fail(wrap, 'The cast', err, function () { window.location.reload(); });
  });

  function makeCard(person) {
    var li = document.createElement('li');
    var card = S.el('button', 'cast-card');
    card.type = 'button';
    if (person.appeared === false) {
      card.hidden = true;
      card.classList.add('is-spoiler');
      card.dataset.spoiler = 'true';
    }

    if (person.image) {
      var img = document.createElement('img');
      img.className = 'portrait';
      img.src = person.image;
      img.alt = 'Portrait of ' + person.name;
      img.loading = 'lazy';
      card.appendChild(img);
    } else {
      var initial = person.name ? person.name.charAt(0) : '❦';
      card.appendChild(S.el('span', 'portrait-initial', initial));
    }

    var body = S.el('span', 'card-body');
    body.appendChild(S.el('span', 'card-name', person.name));
    if (person.epithet) body.appendChild(S.el('span', 'card-epithet', person.epithet));
    if (person.role) body.appendChild(S.el('span', 'card-role', person.role));
    card.appendChild(body);

    card.addEventListener('click', function () { openSheet(person); });
    li.appendChild(card);
    return li;
  }

  function openSheet(person) {
    sheetTitle.textContent = person.name;
    sheetBody.replaceChildren(S.el('p', 'loading-note', 'Finding the sheet…'));
    if (typeof dialog.showModal === 'function') dialog.showModal();
    else dialog.setAttribute('open', 'open');

    if (!person.html) {
      sheetBody.replaceChildren(S.el('p', 'toc-empty', 'No sheet has been written for this person yet.'));
      return;
    }
    S.getText(person.html).then(function (html) {
      var prose = S.el('div', 'prose');
      prose.innerHTML = html; /* a sheet written inside the world */
      if (person.epithet) {
        var note = S.el('p', 'doc-kind', person.epithet);
        note.style.fontFamily = 'var(--font-fell)';
        note.style.fontStyle = 'italic';
        note.style.textAlign = 'center';
        note.style.color = 'var(--muted)';
        prose.insertBefore(note, prose.firstChild);
      }
      sheetBody.replaceChildren(prose);
    }).catch(function (err) {
      S.fail(sheetBody, 'This sheet', err, function () { openSheet(person); });
    });
  }
})();
