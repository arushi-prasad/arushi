/* ===========================================================================
   CAPSULE — two small behaviours for the design-system exhibits.

   Copy-a-token, because the single most useful thing a design-system page can
   do is hand you the value; and the same count-to-the-printed-number used on
   the Leadership page. Both are additive: the swatches are already labelled
   with their hex in the markup, and the counts are already correct.
   ========================================================================= */
(function (win, doc) {
  'use strict';

  var reduced = win.matchMedia ? win.matchMedia('(prefers-reduced-motion: reduce)') : null;
  function noMotion() { return !!(reduced && reduced.matches); }

  /* -------------------------------------------------------------------------
     COPY A TOKEN VALUE
     The swatch is a <button> in the markup, so it is keyboard-reachable
     before this runs. Clipboard access can be refused — when it is, the hex
     is still printed on the swatch, so nothing is lost.
     ---------------------------------------------------------------------- */
  function initCopy() {
    var swatches = Array.prototype.slice.call(doc.querySelectorAll('[data-copy]'));
    if (!swatches.length) return;

    var live = doc.createElement('p');
    live.className = 'sr-only';
    live.setAttribute('role', 'status');
    live.setAttribute('aria-live', 'polite');
    doc.body.appendChild(live);

    swatches.forEach(function (el) {
      el.addEventListener('click', function () {
        var value = el.getAttribute('data-copy');
        function done() {
          el.classList.add('is-copied');
          live.textContent = value + ' copied';
          win.setTimeout(function () { el.classList.remove('is-copied'); }, 900);
        }
        if (win.navigator && win.navigator.clipboard) {
          win.navigator.clipboard.writeText(value).then(done, function () {
            live.textContent = value;   // refused — announce it so it can still be read
          });
        } else {
          live.textContent = value;
        }
      });
    });
  }

  /* -------------------------------------------------------------------------
     COUNTS
     Counts up to the number already printed in the markup, then restores the
     exact original string so a suffix like "+" is never lost.
     ---------------------------------------------------------------------- */
  function countUp(el) {
    var text = el.getAttribute('data-count-text');
    if (text === null) return;
    var digits = text.match(/\d+/);
    if (!digits) return;
    var target = parseInt(digits[0], 10);
    if (!isFinite(target) || target === 0) return;

    var started = null;
    var dur = Math.min(1000, 320 + target * 8);

    function frame(now) {
      if (started === null) started = now;
      var t = Math.min(1, (now - started) / dur);
      var eased = 1 - Math.pow(1 - t, 3);
      el.textContent = text.replace(/\d+/, String(Math.round(target * eased)));
      if (t < 1) win.requestAnimationFrame(frame);
      else el.textContent = text;
    }
    win.requestAnimationFrame(frame);
  }

  function initCounts() {
    var targets = Array.prototype.slice.call(doc.querySelectorAll('[data-count-text]'));
    if (!targets.length) return;
    if (noMotion() || !('IntersectionObserver' in win) || !win.requestAnimationFrame) return;

    var io = new win.IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        io.unobserve(entry.target);
        countUp(entry.target);
      });
    }, { rootMargin: '0px 0px -12% 0px', threshold: 0.4 });

    targets.forEach(function (el) { io.observe(el); });
  }

  function init() { initCopy(); initCounts(); }

  if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', init);
  else init();
})(window, document);
