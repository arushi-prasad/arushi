/* ---------------------------------------------------------------------------
   lightbox.js — the shared gallery lightbox.

   The tiles are already links to the full-resolution image files, so the page
   works with this script absent: clicking opens the sheet in a new tab. All
   this does is intercept that click and show the same file in a <dialog>
   instead, which keeps the reader on the page.

   <dialog> is used rather than a hand-built overlay because focus trapping,
   Esc-to-close, inertness of the page behind it and the top layer are then
   the browser's job. The only things added here are the image swap, a click
   on the backdrop, and returning focus to the tile that was opened.
   --------------------------------------------------------------------------- */
(function () {
  'use strict';

  var galleries = document.querySelectorAll('[data-lb-gallery]');
  var gallery = galleries[0];
  var dlg = document.querySelector('[data-lb]');
  if (!galleries.length || !dlg || typeof dlg.showModal !== 'function') return;

  var img = dlg.querySelector('img');
  var cap = dlg.querySelector('[data-lb-cap]');
  var opener = null;

  function onClick(e) {
    var tile = e.target.closest('a[data-lb-tile]');
    if (!tile) return;
    /* Let the browser handle the ways a reader asks for a new tab. */
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;
    e.preventDefault();
    opener = tile;
    img.src = tile.getAttribute('href');
    img.alt = tile.querySelector('img').alt;
    cap.textContent = tile.getAttribute('data-lb-tile');
    dlg.showModal();
  }

  Array.prototype.forEach.call(galleries, function (g) { g.addEventListener('click', onClick); });

  /* The backdrop is not a child, so a click lands on the dialog itself only
     when it is outside the figure's box. */
  dlg.addEventListener('click', function (e) {
    if (e.target === dlg) dlg.close();
  });

  dlg.querySelector('[data-lb-close]').addEventListener('click', function () { dlg.close(); });

  dlg.addEventListener('close', function () {
    img.removeAttribute('src');
    if (opener) { opener.focus(); opener = null; }
  });
})();
