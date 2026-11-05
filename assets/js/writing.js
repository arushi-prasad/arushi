/* ===========================================================================
   WRITING — the Articles / Notes tabs.

   The whole index is already in the document; this only decides which of the
   two panels is shown. No request, no re-render, no transition — switching a
   tab is one [hidden] attribute moving across.

   Pattern: WAI-ARIA tabs with a manual-activation fallback that is actually
   automatic — arrow keys both move focus and select, which is the expected
   behaviour when selecting a tab costs nothing and loads nothing.
   ========================================================================= */
(function (win, doc) {
  'use strict';

  var list = doc.querySelector('.w-tabs[role="tablist"]');
  if (!list) return;

  var tabs = [].slice.call(list.querySelectorAll('[role="tab"]'));
  if (!tabs.length) return;

  function panelFor(tab) {
    return doc.getElementById(tab.getAttribute('aria-controls'));
  }

  /* The slug a tab is addressed by in the URL: "w-tab-notes" -> "notes". */
  function slugFor(tab) {
    return tab.id.replace(/^w-tab-/, '');
  }

  /* An empty panel says so rather than showing a blank gap. The message is
     the panel's own, from data-empty, so each tab can word it for itself. */
  function fillEmpty(panel) {
    if (!panel || panel.querySelector('.w-empty')) return;
    var items = panel.querySelectorAll('.w-list > li');
    if (items.length) return;
    var label = panel.getAttribute('data-empty');
    if (!label) return;
    var p = doc.createElement('p');
    p.className = 'w-empty';
    p.textContent = label;
    panel.appendChild(p);
  }

  function select(tab, moveFocus, writeHash) {
    tabs.forEach(function (t) {
      var on = t === tab;
      t.setAttribute('aria-selected', on ? 'true' : 'false');
      /* Roving tabindex: the set is one stop in the page's tab order. */
      if (on) { t.removeAttribute('tabindex'); } else { t.setAttribute('tabindex', '-1'); }
      var p = panelFor(t);
      if (p) { p.hidden = !on; }
    });
    if (moveFocus) tab.focus();

    /* The hash is the only routing this static site has, and it is enough:
       /writing/#notes opens on Notes. replaceState rather than a hash
       assignment, so switching tabs does not fill the back button with
       states the reader never navigated to. Only a reader's own choice writes
       it: the first paint leaves the URL exactly as it arrived. */
    if (writeHash && win.history && win.history.replaceState) {
      win.history.replaceState(null, '',
        win.location.pathname + win.location.search + '#' + slugFor(tab));
    }
  }

  list.addEventListener('click', function (e) {
    var tab = e.target.closest ? e.target.closest('[role="tab"]') : null;
    if (!tab || tabs.indexOf(tab) < 0) return;
    select(tab, false, true);
  });

  list.addEventListener('keydown', function (e) {
    var i = tabs.indexOf(doc.activeElement);
    if (i < 0) return;
    var next = -1;
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown')     next = (i + 1) % tabs.length;
    else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp')   next = (i - 1 + tabs.length) % tabs.length;
    else if (e.key === 'Home')                               next = 0;
    else if (e.key === 'End')                                next = tabs.length - 1;
    if (next < 0) return;
    e.preventDefault();
    select(tabs[next], true, true);
  });

  tabs.forEach(function (t) { fillEmpty(panelFor(t)); });

  /* Articles is the default. A hash that names the other tab opens on it;
     anything else in the hash — #main from the skip link, say — is ignored
     and leaves the default alone. Focus is not moved on load. */
  var want = (win.location.hash || '').replace(/^#/, '');
  var match = want && tabs.filter(function (t) { return slugFor(t) === want; })[0];
  select(match || tabs[0], false, false);

})(window, document);
