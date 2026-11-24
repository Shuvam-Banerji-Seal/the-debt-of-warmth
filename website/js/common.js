/* ============================================================
   Shared readings of the data, settings and small courtesies.
   Classic script; every page loads this one first.
   ============================================================ */
(function (global) {
  'use strict';

  var S = {};
  var KEY_SETTINGS = 'sarn.reader.settings';
  var KEY_POSITION = 'sarn.reader.position';
  var DEFAULTS = { theme: 'parchment', face: 'garamond', fontSize: 19, lineHeight: 1.62, textWidth: 38 };
  var cache = {};

  S.KEY_SETTINGS = KEY_SETTINGS;
  S.KEY_POSITION = KEY_POSITION;

  /* ---------- storage (private browsing must not break us) ---------- */
  S.store = {
    get: function (key, fallback) {
      try {
        var raw = global.localStorage.getItem(key);
        return raw ? JSON.parse(raw) : fallback;
      } catch (e) { return fallback; }
    },
    set: function (key, value) {
      try { global.localStorage.setItem(key, JSON.stringify(value)); } catch (e) { /* no memory, no harm */ }
    },
    remove: function (key) {
      try { global.localStorage.removeItem(key); } catch (e) { /* no memory, no harm */ }
    }
  };

  function clamp(value, lo, hi, fallback) {
    var n = Number(value);
    if (!isFinite(n)) return fallback;
    return Math.min(hi, Math.max(lo, n));
  }

  function cleanSettings(raw) {
    raw = raw && typeof raw === 'object' ? raw : {};
    var themes = ['parchment', 'sepia', 'night'];
    return {
      theme: themes.indexOf(raw.theme) >= 0 ? raw.theme : DEFAULTS.theme,
      face: raw.face === 'imfell' ? 'imfell' : 'garamond',
      fontSize: clamp(raw.fontSize, 14, 30, DEFAULTS.fontSize),
      lineHeight: clamp(raw.lineHeight, 1.3, 2.1, DEFAULTS.lineHeight),
      textWidth: clamp(raw.textWidth, 26, 54, DEFAULTS.textWidth)
    };
  }

  S.settings = cleanSettings(S.store.get(KEY_SETTINGS, {}));

  S.applySettings = function () {
    var r = document.documentElement;
    r.setAttribute('data-theme', S.settings.theme);
    r.setAttribute('data-face', S.settings.face);
    r.style.setProperty('--read-size', S.settings.fontSize + 'px');
    r.style.setProperty('--read-leading', String(S.settings.lineHeight));
    r.style.setProperty('--read-width', S.settings.textWidth + 'rem');
    var toggle = document.querySelector('[data-theme-toggle]');
    if (toggle) {
      var next = S.settings.theme === 'night' ? 'Parchment' : 'Night';
      toggle.textContent = S.settings.theme === 'night' ? '☀' : '☾';
      toggle.setAttribute('aria-label', 'Change paper: switch to ' + next + ' theme');
      toggle.title = 'Switch to ' + next + ' theme';
    }
  };

  S.saveSettings = function (patch) {
    S.settings = cleanSettings(Object.assign({}, S.settings, patch || {}));
    S.store.set(KEY_SETTINGS, S.settings);
    S.applySettings();
    return S.settings;
  };

  S.resetSettings = function () {
    S.settings = cleanSettings(DEFAULTS);
    S.store.set(KEY_SETTINGS, S.settings);
    S.applySettings();
    return S.settings;
  };

  /* ---------- fetching, with a friendly failure ---------- */
  function request(path, asText) {
    if (Object.prototype.hasOwnProperty.call(cache, path)) return cache[path];
    var promise = fetch(path).then(function (response) {
      if (!response.ok) throw new Error('the press returned ' + response.status);
      return asText ? response.text() : response.json();
    }).catch(function (err) {
      delete cache[path];
      throw err;
    });
    cache[path] = promise;
    return promise;
  }

  S.getJSON = function (path) { return request(path, false); };
  S.getText = function (path) { return request(path, true); };
  S.getBook = function () { return S.getJSON('data/book.json'); };

  S.el = function (tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = String(text);
    return node;
  };

  S.fail = function (container, what, err, retry) {
    if (!container) return;
    var box = S.el('div', 'fetch-error');
    box.setAttribute('role', 'alert');
    box.appendChild(S.el('p', 'err-mark', '❦'));
    var p = document.createElement('p');
    p.appendChild(S.el('strong', null, 'The page will not open. '));
    var detail = err && err.message ? ' (' + err.message + ')' : '';
    p.appendChild(document.createTextNode(what + ' could not be brought up' + detail + '. Perhaps the press is still setting type.'));
    box.appendChild(p);
    if (typeof retry === 'function') {
      var btn = S.el('button', 'btn', 'Try again');
      btn.type = 'button';
      btn.addEventListener('click', retry);
      box.appendChild(btn);
    }
    container.replaceChildren(box);
  };

  S.fmt = function (n) {
    var v = Number(n);
    return isFinite(v) ? Math.round(v).toLocaleString('en-US') : '0';
  };

  /* ---------- hash routes ---------- */
  S.parseHash = function () {
    var out = {};
    var raw = global.location.hash.replace(/^#/, '');
    if (!raw) return out;
    raw.split('&').forEach(function (pair) {
      if (!pair) return;
      var bits = pair.split('=');
      var key = bits.shift();
      var value = bits.join('=');
      try { out[decodeURIComponent(key)] = decodeURIComponent(value); }
      catch (e) { out[key] = value; }
    });
    return out;
  };

  S.makeHash = function (params) {
    var parts = [];
    Object.keys(params || {}).forEach(function (key) {
      if (params[key] === null || params[key] === undefined || params[key] === '') return;
      parts.push(encodeURIComponent(key) + '=' + encodeURIComponent(params[key]));
    });
    return parts.length ? '#' + parts.join('&') : '#';
  };

  S.setHash = function (params) {
    var hash = S.makeHash(params);
    if (global.location.hash !== hash) {
      global.history.replaceState(null, '', hash);
    }
  };

  /* ---------- the common chrome ---------- */
  S.initChrome = function () {
    S.applySettings();

    document.querySelectorAll('[data-repo-link]').forEach(function (a) {
      S.getBook().then(function (book) {
        if (!book.repository) { a.hidden = true; return; }
        a.href = book.repository;
        a.textContent = 'the repository';
      }).catch(function () { /* the anchor keeps its plain text */ });
    });

    document.querySelectorAll('[data-updated]').forEach(function (node) {
      S.getBook().then(function (book) {
        if (book.updated) node.textContent = 'Type set ' + String(book.updated).slice(0, 10);
      }).catch(function () { /* leave the line unspoken */ });
    });

    var here = global.location.pathname.split('/').pop() || 'index.html';
    document.querySelectorAll('.nav-links a[data-page]').forEach(function (a) {
      if (a.getAttribute('data-page') === here) a.setAttribute('aria-current', 'page');
    });

    var toggle = document.querySelector('[data-theme-toggle]');
    if (toggle) {
      toggle.addEventListener('click', function () {
        S.saveSettings({ theme: S.settings.theme === 'night' ? 'parchment' : 'night' });
      });
    }
  };

  global.Sarn = S;
})(window);
