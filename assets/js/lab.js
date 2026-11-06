/* ===========================================================================
   LAB — the experiments, the snippets, and the plant.
   Each block below finds its own markup and does nothing if that markup is
   not on the page, so one file serves three routes without branching on URL.
   Every demo works with a pointer, a finger and a keyboard.
   ========================================================================= */
(function (win, doc) {
  'use strict';

  var T = win.APTokens;
  var reduced = win.matchMedia ? win.matchMedia('(prefers-reduced-motion: reduce)') : null;
  function noMotion() { return !!(reduced && reduced.matches); }
  function $(sel, root) { return (root || doc).querySelector(sel); }
  function $$(sel, root) { return Array.prototype.slice.call((root || doc).querySelectorAll(sel)); }
  function cssVar(name) {
    return getComputedStyle(doc.documentElement).getPropertyValue(name).trim();
  }

  /* =========================================================================
     SHARED OPTION GROUPS
     The experiments page uses the same radiogroup contract as the homepage
     toolbar, against the same store. Two pages, one behaviour.
     ====================================================================== */
  function initGroups() {
    if (!T) return;
    var groups = $$('[role="radiogroup"][data-group]');
    if (!groups.length) return;

    groups.forEach(function (group) {
      var key = group.getAttribute('data-group');
      var opts = $$('[role="radio"]', group);

      opts.forEach(function (opt, i) {
        opt.addEventListener('click', function () { T.set(key, opt.getAttribute('data-value')); });
        opt.addEventListener('keydown', function (e) {
          var dir = 0;
          if (e.key === 'ArrowRight' || e.key === 'ArrowDown') dir = 1;
          else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') dir = -1;
          else return;
          e.preventDefault();
          var n = opts[(i + dir + opts.length) % opts.length];
          T.set(key, n.getAttribute('data-value'));
          n.focus();
        });
      });
    });

    function paint() {
      var s = T.get();
      groups.forEach(function (group) {
        var key = group.getAttribute('data-group');
        $$('[role="radio"]', group).forEach(function (opt) {
          var on = opt.getAttribute('data-value') === s[key];
          opt.setAttribute('aria-checked', String(on));
          opt.tabIndex = on ? 0 : -1;
        });
      });

      var typeOut = $('[data-type-readout]');
      if (typeOut) {
        typeOut.textContent = s.type.charAt(0).toUpperCase() + s.type.slice(1) +
          ' · ' + cssVar('--weight-display') + ' · ' + cssVar('--track-display');
      }
      var radOut = $('[data-radius-readout]');
      if (radOut) radOut.textContent = '×' + cssVar('--radius-k');
    }

    T.subscribe(paint);
    paint();
  }

  /* =========================================================================
     TOKEN EXPLORER
     Reads values back off the document rather than repeating them, so the
     table cannot drift from the stylesheet.
     ====================================================================== */
  function initTokenTable() {
    var table = $('[data-token-table]');
    if (!table || !T) return;
    var body = table.querySelector('tbody');

    var ROWS = [
      ['--accent', true], ['--accent-light', true], ['--text-primary', true],
      ['--surface-page', true], ['--border-default', true],
      ['--density', false], ['--step-4', false], ['--step-16', false],
      ['--radius-k', false], ['--radius-md', false], ['--radius-full', false],
      ['--deco-opacity', false], ['--type-scale', false],
      ['--weight-display', false], ['--track-display', false]
    ];

    function paint() {
      var html = '';
      ROWS.forEach(function (row) {
        var name = row[0], isColour = row[1];
        var value = cssVar(name) || '·';
        var chip = isColour
          ? '<span class="tokens__chip" style="background:' + value + '"></span>'
          : '';
        html += '<tr><th scope="row">' + name + '</th><td>' + chip + value + '</td></tr>';
      });
      body.innerHTML = html;
    }

    T.subscribe(paint);
    paint();
  }

  /* =========================================================================
     BEFORE / AFTER
     Pointer drag, and a real slider for the keyboard.
     ====================================================================== */
  function initBeforeAfter() {
    var ba = $('[data-ba]');
    if (!ba) return;
    var handle = $('[data-ba-handle]', ba);
    var pct = 50;

    function set(next) {
      pct = Math.min(100, Math.max(0, next));
      ba.style.setProperty('--split', pct + '%');
      handle.setAttribute('aria-valuenow', String(Math.round(pct)));
      handle.setAttribute('aria-valuetext', Math.round(pct) + ' per cent');
    }

    function fromClientX(x) {
      var r = ba.getBoundingClientRect();
      if (!r.width) return;
      set(((x - r.left) / r.width) * 100);
    }

    var dragging = false;
    handle.addEventListener('pointerdown', function (e) {
      dragging = true;
      handle.setPointerCapture(e.pointerId);
      e.preventDefault();
    });
    handle.addEventListener('pointermove', function (e) {
      if (dragging) fromClientX(e.clientX);
    });
    function stop(e) {
      if (!dragging) return;
      dragging = false;
      try { handle.releasePointerCapture(e.pointerId); } catch (err) { /* already released */ }
    }
    handle.addEventListener('pointerup', stop);
    handle.addEventListener('pointercancel', stop);

    // Tapping anywhere in the frame moves the split there — on a phone that
    // is a much easier target than a 2px line.
    ba.addEventListener('click', function (e) {
      if (e.target === handle) return;
      fromClientX(e.clientX);
    });

    handle.addEventListener('keydown', function (e) {
      var step = e.shiftKey ? 10 : 2;
      if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') set(pct - step);
      else if (e.key === 'ArrowRight' || e.key === 'ArrowUp') set(pct + step);
      else if (e.key === 'Home') set(0);
      else if (e.key === 'End') set(100);
      else return;
      e.preventDefault();
    });

    set(50);
  }

  /* =========================================================================
     SNIPPET 01 — hover-responsive typography
     ====================================================================== */
  function initHoverType() {
    var el = $('[data-hover-type]');
    if (!el) return;
    var spans = $$('span', el);

    function clear() { spans.forEach(function (s) { s.classList.remove('is-near', 'is-close'); }); }

    function lightFrom(x) {
      spans.forEach(function (s) {
        var r = s.getBoundingClientRect();
        var d = Math.abs(x - (r.left + r.width / 2));
        s.classList.toggle('is-near', d < r.width * 0.9);
        s.classList.toggle('is-close', d >= r.width * 0.9 && d < r.width * 2.2);
      });
    }

    el.addEventListener('pointermove', function (e) { lightFrom(e.clientX); });
    el.addEventListener('pointerleave', clear);
    // Touch: a tap lights the nearest letter and then releases it, so the
    // behaviour is demonstrated rather than switched off.
    el.addEventListener('pointerdown', function (e) {
      if (e.pointerType !== 'touch') return;
      lightFrom(e.clientX);
      win.setTimeout(clear, 900);
    });
  }

  /* =========================================================================
     SNIPPET 02 — text reveal
     ====================================================================== */
  function initRevealLines() {
    var box = $('[data-reveal-lines]');
    if (!box) return;
    var btn = $('[data-reveal-play]');

    function play() {
      box.classList.remove('is-on');
      // Force a reflow so the animation can be restarted from the top.
      void box.offsetWidth;
      box.classList.add('is-on');
    }

    if (btn) btn.addEventListener('click', play);

    if ('IntersectionObserver' in win) {
      var io = new win.IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (!en.isIntersecting) return;
          play();
          io.unobserve(en.target);
        });
      }, { threshold: 0.4 });
      io.observe(box);
    } else {
      play();
    }
  }

  /* =========================================================================
     SNIPPET 03 — colour transition
     Auto runs one cycle and stops. Nothing here animates forever.
     ====================================================================== */
  function initHueStrip() {
    var strip = $('[data-hue-strip]');
    if (!strip) return;
    var cells = $$('i', strip);
    var stepBtn = $('[data-hue-step]');
    var autoBtn = $('[data-hue-auto]');
    var out = $('[data-hue-readout]');
    var RING = ['--letter-1', '--letter-2', '--letter-3', '--letter-4', '--letter-5', '--letter-6'];
    var at = 0;
    var timer = null;

    function paint() {
      cells.forEach(function (c, i) {
        var name = RING[(at + i) % RING.length];
        // The stagger is what makes it read as a wave rather than a flash.
        win.setTimeout(function () { c.style.setProperty('--c', 'var(' + name + ')'); },
                       noMotion() ? 0 : i * 70);
      });
      if (out) out.textContent = RING[at % RING.length].replace('--', '');
    }

    function step() { at = (at + 1) % RING.length; paint(); }

    function stopAuto() {
      if (timer) { win.clearInterval(timer); timer = null; }
      if (autoBtn) autoBtn.setAttribute('aria-pressed', 'false');
    }

    if (stepBtn) stepBtn.addEventListener('click', function () { stopAuto(); step(); });

    if (autoBtn) {
      autoBtn.addEventListener('click', function () {
        if (timer) { stopAuto(); return; }
        autoBtn.setAttribute('aria-pressed', 'true');
        var left = RING.length;
        timer = win.setInterval(function () {
          step();
          if (--left <= 0) stopAuto();   // one full cycle, then it stops itself
        }, 900);
      });
    }

    // A palette change should land on the strip immediately.
    if (T) T.subscribe(paint);
    paint();
  }

  /* =========================================================================
     SNIPPET 05 — stepper
     ====================================================================== */
  function initStepper() {
    var box = $('[data-stepper]');
    if (!box) return;
    var LABELS = ['Define', 'Design', 'Build', 'Ship'];
    var dots = $$('.stepper__dot', box);
    var fill = $('.stepper__fill', box);
    var label = $('[data-stepper-label]');
    var prev = $('[data-stepper-prev]');
    var next = $('[data-stepper-next]');
    var out = $('[data-stepper-readout]');
    var status = $('[data-stepper-status]');
    var at = 0;

    function paint(announce) {
      dots.forEach(function (d, i) {
        d.setAttribute('data-on', String(i <= at));
        d.setAttribute('data-current', String(i === at));
      });
      fill.style.setProperty('--p', (at / (dots.length - 1)) * 100 + '%');
      if (label) label.textContent = LABELS[at];
      if (out) out.textContent = (at + 1) + ' / ' + dots.length;
      // The disabled states are real, not decorative.
      if (prev) prev.disabled = at === 0;
      if (next) next.disabled = at === dots.length - 1;
      if (announce && status) status.textContent = 'Step ' + (at + 1) + ' of ' + dots.length + ', ' + LABELS[at];
    }

    if (prev) prev.addEventListener('click', function () { if (at > 0) { at--; paint(true); } });
    if (next) next.addEventListener('click', function () { if (at < dots.length - 1) { at++; paint(true); } });
    paint(false);
  }

  /* =========================================================================
     THE PLANT — Fun stuff
     ====================================================================== */
  function initPlant() {
    var box = $('[data-plant]');
    if (!box) return;
    var leaves = $$('.plant__leaf', box);
    var water = $('[data-plant-water]', box);
    var reset = $('[data-plant-reset]', box);
    var count = $('[data-plant-count]', box);
    var status = $('[data-plant-status]', box);
    var grown = 0;

    function paint(announce) {
      leaves.forEach(function (l, i) { l.setAttribute('data-grown', String(i < grown)); });
      if (count) count.textContent = String(grown);
      if (water) water.disabled = grown >= leaves.length;
      if (reset) reset.disabled = grown === 0;
      if (announce && status) {
        status.textContent = grown >= leaves.length
          ? 'Fully grown: five leaves.'
          : 'Leaf ' + grown + ' of ' + leaves.length + '.';
      }
    }

    if (water) water.addEventListener('click', function () {
      if (grown < leaves.length) { grown++; paint(true); }
    });
    if (reset) reset.addEventListener('click', function () { grown = 0; paint(true); });

    // The plant itself is a target too — tapping the pot waters it.
    var svg = $('.plant__svg', box);
    if (svg) {
      svg.style.cursor = 'pointer';
      svg.addEventListener('click', function () {
        if (grown < leaves.length) { grown++; paint(true); }
        else { grown = 0; paint(true); }
      });
    }

    paint(false);
  }

  function boot() {
    initGroups();
    initTokenTable();
    initBeforeAfter();
    initHoverType();
    initRevealLines();
    initHueStrip();
    initStepper();
    initPlant();
  }

  if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', boot);
  else boot();
})(window, document);
