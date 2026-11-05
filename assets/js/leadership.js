/* ===========================================================================
   LEADERSHIP — the two pieces of behaviour this page adds.

   Neither of them is load-bearing. The career tracks are ordinary markup,
   fully expanded, before this file runs: the script collapses them so the
   chapter is skimmable, and gives back a keyboard-operable toggle. The
   numbers are already correct in the HTML: the script only counts up to the
   value that is printed there. Switch this file off and the page is longer
   and stiller, and says exactly the same things.
   ========================================================================= */
(function (win, doc) {
  'use strict';

  var reduced = win.matchMedia ? win.matchMedia('(prefers-reduced-motion: reduce)') : null;
  function noMotion() { return !!(reduced && reduced.matches); }

  /* -------------------------------------------------------------------------
     CAREER TRACKS
     An accordion that keeps one track open. The first is left open so the
     chapter never presents the reader with five closed doors and no example
     of what is behind them.
     ---------------------------------------------------------------------- */
  function initTracks() {
    var heads = Array.prototype.slice.call(doc.querySelectorAll('[data-track-toggle]'));
    if (!heads.length) return;

    function panel(head) {
      return doc.getElementById(head.getAttribute('aria-controls'));
    }

    function setOpen(head, open) {
      var p = panel(head);
      if (!p) return;
      head.setAttribute('aria-expanded', open ? 'true' : 'false');
      if (open) p.removeAttribute('hidden');
      else p.setAttribute('hidden', '');
    }

    // Collapse everything the markup left open, except the first.
    heads.forEach(function (head, i) { setOpen(head, i === 0); });

    heads.forEach(function (head) {
      head.addEventListener('click', function () {
        var isOpen = head.getAttribute('aria-expanded') === 'true';
        // Clicking the open track closes it: a reader who wants the whole
        // chapter collapsed is allowed to have that.
        heads.forEach(function (other) { setOpen(other, false); });
        setOpen(head, !isOpen);
      });
    });
  }

  /* -------------------------------------------------------------------------
     COUNTING NUMBERS
     Two flavours, because the page has two kinds of figure. `data-count` is a
     plain integer. `data-count-text` is a printed string that may carry a
     suffix or a per-cent sign — "24+", "100%" — so the digits are counted and
     everything around them is preserved exactly as written.

     The element's text is never replaced by anything the HTML did not already
     say: at the end of the run it is reset to the original string.
     ---------------------------------------------------------------------- */
  function countUp(el, finish) {
    var raw = el.getAttribute('data-count-text');
    var text = raw === null ? el.getAttribute('data-count') : raw;
    if (text === null) return;

    var digits = text.match(/\d+/);
    if (!digits) return;
    var target = parseInt(digits[0], 10);
    if (!isFinite(target) || target === 0) return;

    var started = null;
    var dur = Math.min(1100, 340 + target * 26);

    function frame(now) {
      if (started === null) started = now;
      var t = Math.min(1, (now - started) / dur);
      // Ease out: fast at first, settling on the number rather than
      // arriving at it abruptly.
      var eased = 1 - Math.pow(1 - t, 3);
      var value = Math.round(target * eased);
      el.textContent = text.replace(/\d+/, String(value));
      if (t < 1) win.requestAnimationFrame(frame);
      else { el.textContent = text; if (finish) finish(); }
    }
    win.requestAnimationFrame(frame);
  }

  function initCounts() {
    var targets = Array.prototype.slice.call(
      doc.querySelectorAll('[data-count], [data-count-text]')
    );
    if (!targets.length) return;

    // Without motion, or without an observer, the printed values stand. They
    // are already the right numbers — that is the whole point of counting to
    // what the HTML says.
    if (noMotion() || !('IntersectionObserver' in win) || !win.requestAnimationFrame) return;

    var io = new win.IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var el = entry.target;
        io.unobserve(el);
        countUp(el);
      });
    }, { rootMargin: '0px 0px -12% 0px', threshold: 0.4 });

    targets.forEach(function (el) { io.observe(el); });
  }

  function init() {
    initTracks();
    initCounts();
  }

  if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', init);
  else init();
})(window, document);
