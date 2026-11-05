/* ---------------------------------------------------------------------------
   wpds.js — the two behaviours chapter 14's component specimens need.

   The WorkPerks design system's segmented control has no CSS-only resting
   state: the selected label is painted in the inverse ink and a JavaScript
   positioned pill slides underneath it. Without that pill the selected label
   is white on white, so the specimen would show one of its two segments.

   This is the documentation's own `seg` function, trimmed to what a static
   specimen needs, plus click handling for tabs and chips so the states the
   chapter is describing can actually be tried. Nothing else on the page uses
   it, so no other page downloads it.
   ------------------------------------------------------------------------ */
(function () {
  'use strict';

  function all(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }

  /* Segmented control: inject the indicator, then keep it under whichever
     button is selected. A ResizeObserver covers the font swapping in and
     the container reflowing. */
  function segment(el) {
    var ind = el.querySelector('.wp-seg__ind');
    if (!ind) {
      ind = document.createElement('span');
      ind.className = 'wp-seg__ind';
      el.prepend(ind);
    }
    function place() {
      var on = el.querySelector('[aria-selected="true"]');
      if (!on) return;
      ind.style.left = on.offsetLeft + 'px';
      ind.style.width = on.offsetWidth + 'px';
    }
    el.addEventListener('click', function (e) {
      var b = e.target.closest('button');
      if (!b) return;
      all('button', el).forEach(function (x) { x.setAttribute('aria-selected', String(x === b)); });
      place();
    });
    if ('ResizeObserver' in window) new ResizeObserver(place).observe(el);
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(place);
    place();
  }

  /* Tabs and chips carry their state in the attribute the CSS already reads,
     so switching one is a single attribute write. */
  function pickOne(el, attr) {
    el.addEventListener('click', function (e) {
      var b = e.target.closest('button');
      if (!b) return;
      all('button', el).forEach(function (x) { x.setAttribute(attr, String(x === b)); });
    });
  }

  function init() {
    all('.wpds .wp-seg').forEach(segment);
    all('.wpds .wp-tabs').forEach(function (el) { pickOne(el, 'aria-selected'); });
    all('.wpds [data-chips]').forEach(function (el) { pickOne(el, 'aria-pressed'); });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
