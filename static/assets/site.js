/* SERAFIX site script: menu, language, search, quote list, forms, cookie consent. */
(function () {
  var body = document.body;
  var lang = document.documentElement.lang || 'en';
  var T = {};
  try { T = JSON.parse(body.getAttribute('data-i18n') || '{}'); } catch (e) {}
  var store = {
    get: function (k, d) { try { var v = localStorage.getItem(k); return v === null ? d : JSON.parse(v); } catch (e) { return d; } },
    set: function (k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
  };

  // ---------- mobile menu
  var menuBtn = document.querySelector('.menu-btn');
  var nav = document.getElementById('mainnav');
  if (menuBtn && nav) {
    menuBtn.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      menuBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    nav.addEventListener('click', function (e) { if (e.target.closest('a')) { nav.classList.remove('open'); menuBtn.setAttribute('aria-expanded', 'false'); } });
  }

  // ---------- hero product slideshow
  var hs = document.querySelector('[data-hs]');
  if (hs) {
    var slides = Array.prototype.slice.call(hs.querySelectorAll('.hs-slide'));
    var info = []; try { info = JSON.parse(hs.querySelector('[data-hs-data]').textContent); } catch (e) {}
    var cap = hs.querySelector('[data-hs-cap]'), nm = hs.querySelector('[data-hs-name]'), ct = hs.querySelector('[data-hs-cat]'), cnt = hs.querySelector('[data-hs-count]');
    var cur = 0, timer = null, reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
    var show = function (i) {
      if (!slides.length) return;
      i = (i + slides.length) % slides.length;
      slides[cur].hidden = true; slides[i].hidden = false; slides[i].classList.remove('hs-in'); void slides[i].offsetWidth; slides[i].classList.add('hs-in');
      cur = i;
      var d = info[i] || {};
      if (nm) nm.textContent = d.n || ''; if (ct) ct.textContent = d.c || ''; if (cap) cap.href = d.u || cap.href;
      if (cnt) cnt.textContent = (i + 1) + ' / ' + slides.length;
      var nx = slides[(i + 1) % slides.length].querySelector('img'); if (nx) nx.loading = 'eager';
    };
    var play = function () { if (reduce || slides.length < 2) return; stop(); timer = setInterval(function () { show(cur + 1); }, 3500); };
    var stop = function () { if (timer) clearInterval(timer); timer = null; };
    var rtl = document.documentElement.dir === 'rtl';
    hs.querySelector('[data-hs-next]').addEventListener('click', function () { show(cur + 1); play(); });
    hs.querySelector('[data-hs-prev]').addEventListener('click', function () { show(cur - 1); play(); });
    hs.addEventListener('mouseenter', stop); hs.addEventListener('mouseleave', play);
    hs.addEventListener('focusin', stop); hs.addEventListener('focusout', play);
    document.addEventListener('visibilitychange', function () { if (document.hidden) stop(); else play(); });
    play();
  }

  // ---------- language menu
  document.querySelectorAll('details.lang a[hreflang]').forEach(function (a) {
    a.addEventListener('click', function () { store.set('sf_lang', a.getAttribute('hreflang')); });
  });
  document.addEventListener('click', function (e) {
    document.querySelectorAll('details.lang[open]').forEach(function (d) { if (!d.contains(e.target)) d.removeAttribute('open'); });
  });

  // ---------- product search on list pages (?q=...)
  var grid = document.getElementById('grid');
  var input = document.getElementById('ara');
  if (grid && input && /\/products\//.test(location.pathname)) {
    var cards = Array.prototype.slice.call(grid.querySelectorAll('[data-s]'));
    var none = document.getElementById('noresult');
    var run = function () {
      var q = input.value.trim().toLocaleLowerCase(lang);
      var n = 0;
      cards.forEach(function (c) { var ok = !q || c.getAttribute('data-s').indexOf(q) !== -1; c.hidden = !ok; if (ok) n++; });
      if (none) none.hidden = n !== 0 || cards.length === 0;
    };
    try { var q0 = new URLSearchParams(location.search).get('q'); if (q0) input.value = q0; } catch (e) {}
    input.addEventListener('input', run);
    if (input.form) input.form.addEventListener('submit', function (e) { e.preventDefault(); run(); });
    run();
  }

  // ---------- quote list (stored only in this browser)
  var QK = 'sf_quote';
  var list = store.get(QK, []);
  if (!Array.isArray(list)) list = [];
  var save = function () { store.set(QK, list); render(); };
  var has = function (id) { return list.some(function (x) { return x.id === id; }); };
  var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); };

  function render() {
    document.querySelectorAll('[data-qcount]').forEach(function (el) { el.textContent = list.length; el.hidden = list.length === 0; });
    document.querySelectorAll('.addq').forEach(function (b) {
      var d; try { d = JSON.parse(b.getAttribute('data-q')); } catch (e) { return; }
      var on = has(d.id);
      b.setAttribute('aria-pressed', on ? 'true' : 'false');
      var label = b.querySelector('span');
      if (label) label.textContent = on ? (T.qAdded || 'In list') : (b.classList.contains('addq-row') ? (T.qAddShort || 'Add') : (T.qAdd || 'Add'));
      b.title = on ? (T.qAdded || '') : (T.qAdd || '');
    });
    var box = document.getElementById('qlist');
    if (box) {
      box.hidden = list.length === 0;
      var ul = box.querySelector('[data-qitems]');
      ul.innerHTML = list.map(function (x, i) {
        return '<li style="display:flex;gap:12px;align-items:center;background:#fff;border:1px solid #E3E8E4;padding:8px 10px">' +
          (x.i ? '<img src="' + esc(x.i) + '" alt="" width="44" height="44" style="width:44px;height:44px;object-fit:contain;flex:none">' : '') +
          '<span style="flex:1;min-width:0;font-size:14px;line-height:1.4"><a href="' + esc(x.u) + '" style="font-weight:700;color:#11261C;text-decoration:none">' + esc(x.n) + '</a><br><span style="color:#5B6660;font-size:12px;direction:ltr;unicode-bidi:isolate">' + esc(x.c) + '</span></span>' +
          '<label style="display:flex;flex-direction:column;font-size:11px;color:#5B6660;gap:2px">' + esc(T.qQty || 'Qty') +
          '<input type="number" min="1" inputmode="numeric" data-qqty="' + i + '" value="' + esc(x.qty || '') + '" style="width:84px;height:34px;padding:0 8px;border:1.5px solid #C7D3CC;font:inherit"></label>' +
          '<button type="button" data-qdel="' + i + '" aria-label="' + esc(T.qRemove || 'Remove') + ': ' + esc(x.n) + '" style="width:34px;height:34px;border:none;background:none;color:#5B6660;font-size:20px;cursor:pointer">×</button></li>';
      }).join('');
    }
    var hidden = document.querySelector('input[name=quote_list]');
    if (hidden) hidden.value = list.map(function (x) { return (x.qty ? x.qty + ' × ' : '') + x.n + ' [' + x.c + ']'; }).join('\n');
  }

  document.addEventListener('click', function (e) {
    var b = e.target.closest('.addq');
    if (b) {
      e.preventDefault();
      var d; try { d = JSON.parse(b.getAttribute('data-q')); } catch (err) { return; }
      if (has(d.id)) list = list.filter(function (x) { return x.id !== d.id; }); else list.push(d);
      save();
      return;
    }
    var del = e.target.closest('[data-qdel]');
    if (del) { list.splice(+del.getAttribute('data-qdel'), 1); save(); return; }
    if (e.target.closest('[data-qclear]')) { list = []; save(); }
  });
  document.addEventListener('change', function (e) {
    var q = e.target.getAttribute && e.target.getAttribute('data-qqty');
    if (q !== null && q !== undefined && list[+q]) { list[+q].qty = e.target.value; store.set(QK, list); render(); }
  });
  render();

  // ---------- "ask for price" etc. fill the product field of the contact form
  document.querySelectorAll('[data-product]').forEach(function (a) {
    a.addEventListener('click', function () {
      var f = document.getElementById('f-product');
      if (f) { f.value = a.getAttribute('data-product'); setTimeout(function () { f.focus({ preventScroll: true }); }, 450); }
    });
  });

  // ---------- lead forms: POST to configured endpoint (Formspree-compatible) or fall back to email
  document.querySelectorAll('form.lead').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      render();
      var box = form.parentNode.querySelector('.sentbox');
      var done = function () {
        form.hidden = true;
        if (box) box.hidden = false;
        if (form.getAttribute('data-kind') === 'contact') { list = []; store.set(QK, list); render(); }
      };
      var action = form.getAttribute('action');
      var data = new FormData(form);
      if (!action) {
        var to = form.getAttribute('data-mailto') || '';
        var lines = [];
        data.forEach(function (v, k) { if (k.charAt(0) !== '_' && typeof v === 'string' && v) lines.push(k + ': ' + v); });
        location.href = 'mailto:' + to + '?subject=' + encodeURIComponent(data.get('_subject') || 'SERAFIX') + '&body=' + encodeURIComponent(lines.join('\n'));
        return;
      }
      var btn = form.querySelector('[type=submit]'); if (btn) btn.disabled = true;
      fetch(action, { method: 'POST', body: data, headers: { Accept: 'application/json' } })
        .then(function (r) { if (!r.ok) throw new Error(r.status); done(); })
        .catch(function () { if (btn) btn.disabled = false; alert('Error. Please email us.'); });
    });
  });

  // ---------- analytics only after consent
  var ga = body.getAttribute('data-ga');
  if (ga) {
    var bar = document.getElementById('cookiebar');
    var load = function () {
      if (window.__gaLoaded) return; window.__gaLoaded = true;
      var s = document.createElement('script'); s.async = true; s.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(ga);
      document.head.appendChild(s);
      window.dataLayer = window.dataLayer || [];
      window.gtag = function () { window.dataLayer.push(arguments); };
      window.gtag('js', new Date()); window.gtag('config', ga, { anonymize_ip: true });
    };
    var choice = store.get('sf_consent', null);
    if (choice === 'yes') load(); else if (choice === null && bar) bar.hidden = false;
    if (bar) bar.addEventListener('click', function (e) {
      var b = e.target.closest('[data-consent]'); if (!b) return;
      var v = b.getAttribute('data-consent'); store.set('sf_consent', v); bar.hidden = true;
      if (v === 'yes') load();
      else document.cookie.split(';').forEach(function (c) { var n = c.split('=')[0].trim(); if (/^_ga/.test(n)) document.cookie = n + '=; Max-Age=0; path=/; domain=' + location.hostname.replace(/^www\./, '.'); });
    });
    document.querySelectorAll('[data-cookie-settings]').forEach(function (b) { b.addEventListener('click', function () { if (bar) bar.hidden = false; }); });
  }
})();
