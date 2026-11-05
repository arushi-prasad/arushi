/* ===========================================================================
   SITE — the behaviour every page shares.
   Reveal on scroll · mobile navigation · copy buttons.

   Navigation is left to the browser. There was a three-layer curtain here
   that swept up over the outgoing page and away from the incoming one —
   two sweeps for one navigation, with the link held for the length of the
   first before the document was allowed to change. Clicking a link now
   does what clicking a link does.
   ========================================================================= */
(function (win, doc) {
  'use strict';

  var reduced = win.matchMedia ? win.matchMedia('(prefers-reduced-motion: reduce)') : null;
  function noMotion() { return !!(reduced && reduced.matches); }

  doc.documentElement.classList.add('js');

  /* -------------------------------------------------------------------------
     REVEAL
     One observer for the whole page. Elements are revealed once and then
     released, so nothing keeps observing after it has been seen.
     ---------------------------------------------------------------------- */
  function initReveal() {
    var targets = doc.querySelectorAll('[data-reveal]');
    if (!targets.length) return;

    if (noMotion() || !('IntersectionObserver' in win)) {
      for (var i = 0; i < targets.length; i++) targets[i].classList.add('is-in');
      return;
    }

    var io = new win.IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var el = entry.target;
        var delay = Number(el.getAttribute('data-reveal-delay')) || 0;
        if (delay) el.style.transitionDelay = delay + 'ms';
        el.classList.add('is-in');
        io.unobserve(el);
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });

    for (var j = 0; j < targets.length; j++) io.observe(targets[j]);
  }

  /* -------------------------------------------------------------------------
     MOBILE NAVIGATION
     A real dialog-ish sheet: focus moves in, Escape and the backdrop close
     it, and focus returns to the control that opened it.
     ---------------------------------------------------------------------- */
  function initNav() {
    var burger = doc.querySelector('[data-nav-open]');
    var sheet = doc.getElementById('nav-sheet');
    if (!burger || !sheet) return;
    var closeBtn = sheet.querySelector('[data-nav-close]');

    function open() {
      sheet.setAttribute('data-open', 'true');
      burger.setAttribute('aria-expanded', 'true');
      doc.body.style.overflow = 'hidden';
      // One frame so the display change lands before the opacity transition.
      win.requestAnimationFrame(function () { sheet.classList.add('is-in'); });
      var first = sheet.querySelector('a, button');
      if (first) first.focus();
    }

    function close() {
      sheet.classList.remove('is-in');
      sheet.setAttribute('data-open', 'false');
      burger.setAttribute('aria-expanded', 'false');
      doc.body.style.overflow = '';
      burger.focus();
    }

    burger.addEventListener('click', open);
    if (closeBtn) closeBtn.addEventListener('click', close);

    doc.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && sheet.getAttribute('data-open') === 'true') close();
    });

    // Keep focus inside the sheet while it is open.
    sheet.addEventListener('keydown', function (e) {
      if (e.key !== 'Tab') return;
      var items = sheet.querySelectorAll('a[href], button:not([disabled])');
      if (!items.length) return;
      var first = items[0], last = items[items.length - 1];
      if (e.shiftKey && doc.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && doc.activeElement === last) { e.preventDefault(); first.focus(); }
    });

    // A width change that restores the desktop bar should not leave the
    // sheet open behind it.
    if (win.matchMedia) {
      var wide = win.matchMedia('(min-width: 961px)');
      var onWide = function (e) {
        if (e.matches && sheet.getAttribute('data-open') === 'true') close();
      };
      if (wide.addEventListener) wide.addEventListener('change', onWide);
      else if (wide.addListener) wide.addListener(onWide);
    }
  }

  /* -------------------------------------------------------------------------
     COPY BUTTONS
     ---------------------------------------------------------------------- */
  function initCopy() {
    var buttons = doc.querySelectorAll('[data-copy]');
    Array.prototype.forEach.call(buttons, function (btn) {
      var original = btn.getAttribute('aria-label') || 'Copy';
      var live = btn.parentNode.querySelector('[data-copy-status]');

      btn.addEventListener('click', function () {
        var text = btn.getAttribute('data-copy');
        var done = function (ok) {
          btn.classList.toggle('is-done', ok);
          btn.setAttribute('aria-label', ok ? 'Copied' : 'Copy failed — select the address instead');
          if (live) live.textContent = ok ? 'Address copied' : 'Copy unavailable — select the address instead';
          win.setTimeout(function () {
            btn.classList.remove('is-done');
            btn.setAttribute('aria-label', original);
            if (live) live.textContent = '';
          }, 2200);
        };

        if (win.navigator.clipboard && win.navigator.clipboard.writeText) {
          win.navigator.clipboard.writeText(text).then(function () { done(true); }, function () { done(false); });
        } else {
          done(false);
        }
      });
    });
  }


  /* Filters for the generated allocation sheet. The rows and their filter
     values are rendered server-side; this only hides and counts them, so the
     table is complete and readable with JavaScript switched off. */
  function initSheets() {
    var tables = doc.querySelectorAll('[data-sheet]');
    if (!tables.length) return;

    Array.prototype.forEach.call(tables, function (table) {
      var scope = table.closest('section') || doc;
      var selects = scope.querySelectorAll('[data-filter]');
      var count = scope.querySelector('[data-sheet-count]');
      var empty = scope.querySelector('[data-sheet-empty]');
      var rows = table.querySelectorAll('tbody tr');
      if (!selects.length || !rows.length) return;

      function apply() {
        var want = {};
        Array.prototype.forEach.call(selects, function (sel) {
          if (sel.value) want[sel.getAttribute('data-filter')] = sel.value;
        });

        var shown = 0;
        Array.prototype.forEach.call(rows, function (row) {
          var ok = true;
          for (var k in want) {
            if (row.getAttribute('data-' + k) !== want[k]) { ok = false; break; }
          }
          row.hidden = !ok;
          if (ok) shown++;
        });

        var total = rows.length;
        if (count) {
          count.textContent = shown === total
            ? total + ' work items'
            : shown + ' of ' + total + ' work items';
        }
        if (empty) empty.hidden = shown !== 0;
      }

      Array.prototype.forEach.call(selects, function (sel) {
        sel.addEventListener('change', apply);
      });
      apply();
    });
  }


  /* Two small tab groups on the design-quality page: the evaluation dimensions
     and the critique frameworks. Both are progressive — every panel is in the
     served HTML and only gets hidden once this runs, so the page is complete
     without JavaScript. */
  function initTabs() {
    var groups = [
      { root: '[data-questions]', tab: '.qtab', key: 'dim', panel: '[data-dim]' },
      { root: '[data-frameworks]', tab: '.ftab', key: 'fw', panel: '[data-fw]' }
    ];

    groups.forEach(function (g) {
      Array.prototype.forEach.call(doc.querySelectorAll(g.root), function (root) {
        var tabs = root.querySelectorAll(g.tab);
        if (!tabs.length) return;
        var panels = Array.prototype.filter.call(
          root.querySelectorAll(g.panel),
          function (el) { return !el.matches(g.tab); });

        function show(val) {
          Array.prototype.forEach.call(tabs, function (t) {
            var on = t.dataset[g.key] === val;
            t.classList.toggle('is-on', on);
            t.setAttribute('aria-pressed', on ? 'true' : 'false');
          });
          panels.forEach(function (p) { p.hidden = p.dataset[g.key] !== val; });
        }

        Array.prototype.forEach.call(tabs, function (t, i) {
          t.addEventListener('click', function () { show(t.dataset[g.key]); });
          /* Left/right arrows walk the group, the way a tab list should. */
          t.addEventListener('keydown', function (ev) {
            var step = ev.key === 'ArrowRight' ? 1 : (ev.key === 'ArrowLeft' ? -1 : 0);
            if (!step) return;
            ev.preventDefault();
            var next = tabs[(i + step + tabs.length) % tabs.length];
            next.focus();
            show(next.dataset[g.key]);
          });
        });

        show(tabs[0].dataset[g.key]);
      });
    });
  }


  /* The AI page's two controls: the seven-layer stack and the workflow switch.
     Both are progressive — every panel ships in the HTML and is only hidden once
     this runs, so the page reads completely with JavaScript off. */
  function initOS() {
    var os = doc.querySelector('[data-layers]');
    if (os) {
      var tabs = os.querySelectorAll('.stack__layer');
      var panels = os.querySelectorAll('.lay[data-layer]');

      var showLayer = function (val) {
        Array.prototype.forEach.call(tabs, function (t) {
          var on = t.dataset.layer === val;
          t.classList.toggle('is-on', on);
          t.setAttribute('aria-pressed', on ? 'true' : 'false');
        });
        Array.prototype.forEach.call(panels, function (p) {
          p.hidden = p.dataset.layer !== val;
        });
      };

      Array.prototype.forEach.call(tabs, function (t, i) {
        t.addEventListener('click', function () { showLayer(t.dataset.layer); });
        t.addEventListener('keydown', function (ev) {
          var step = (ev.key === 'ArrowDown' || ev.key === 'ArrowRight') ? 1
                   : (ev.key === 'ArrowUp' || ev.key === 'ArrowLeft') ? -1 : 0;
          if (!step) return;
          ev.preventDefault();
          var next = tabs[(i + step + tabs.length) % tabs.length];
          next.focus();
          showLayer(next.dataset.layer);
        });
      });
      if (tabs.length) showLayer(tabs[0].dataset.layer);
    }

    /* The workflow switch dims the other rail rather than hiding it, so the
       comparison the section is making stays on screen. */
    var flows = doc.querySelector('[data-flows]');
    if (!flows) return;
    var btns = flows.querySelectorAll('.fswitch');
    var rails = flows.querySelectorAll('.rail');

    function showFlow(val) {
      Array.prototype.forEach.call(btns, function (b) {
        var on = b.dataset.flow === val;
        b.classList.toggle('is-on', on);
        b.setAttribute('aria-pressed', on ? 'true' : 'false');
      });
      Array.prototype.forEach.call(rails, function (r) {
        r.classList.toggle('is-on', r.dataset.flow === val);
      });
      flows.classList.add('is-focus');
    }

    Array.prototype.forEach.call(btns, function (b) {
      b.addEventListener('click', function () { showFlow(b.dataset.flow); });
    });
  }

  function boot() {
    initReveal();
    initNav();
    initCopy();
    initSheets();
    initTabs();
    initOS();
  }

  if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', boot);
  else boot();
})(window, document);
