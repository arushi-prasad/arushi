/* ===========================================================================
   CASE — the three live pieces: which section you are in, how far through
   you are, and on a phone, the contents panel.

   Everything else about the layout is CSS. This file adds no behaviour the
   page needs in order to work: the rail is a list of anchors, the anchors
   clear the fixed nav through scroll-margin-top, and the browser scrolls
   them smoothly on its own. With this script switched off the case study
   still reads and still navigates — it simply stops saying where you are,
   and on a phone the contents panel is served open, because a panel that
   only a script can open is a panel nobody can open.

   Reading position is measured, not observed. An IntersectionObserver is
   the usual answer and it is the wrong one here: sections are wildly
   different heights, two can be on screen at once, and the observer then
   flickers between them as the reader scrolls. Comparing each section's top
   against one line across the viewport gives exactly one answer at a time.
   ========================================================================= */
(function (win, doc) {
  'use strict';

  /* The fixed nav's height in pixels, however --nav-height is written. */
  function navHeight() {
    var raw = win.getComputedStyle(doc.documentElement).getPropertyValue('--nav-height');
    var n = parseFloat(raw) || 84;
    if (/rem/.test(raw)) n *= parseFloat(win.getComputedStyle(doc.documentElement).fontSize) || 16;
    return n;
  }

  function init() {
    var rail = doc.querySelector('[data-case-rail]');
    if (!rail) return;

    var titleTick = handoff(rail);
    if (titleTick) {
      var tq = false;
      var onTitle = function () {
        if (tq) return;
        tq = true;
        win.requestAnimationFrame(function () { tq = false; titleTick(); });
      };
      win.addEventListener('scroll', onTitle, { passive: true });
      win.addEventListener('resize', onTitle, { passive: true });
      titleTick();
      /* Fonts land after first paint and move the hero, same as the marker. */
      if (doc.fonts && doc.fonts.ready) doc.fonts.ready.then(titleTick);
    }

    var links = Array.prototype.slice.call(rail.querySelectorAll('[data-case-link]'));
    if (!links.length) return;


    var list = rail.querySelector('.case__list');

    /* Each link's section, resolved once. A link whose target is missing is
       dropped rather than left to throw on every frame. */
    var items = [];
    links.forEach(function (link) {
      var el = doc.getElementById(link.getAttribute('data-case-link'));
      if (el) items.push({ link: link, el: el });
    });
    if (!items.length) return;

    var current = null;

    /* The progress line. Measured against the reading column, not the
       document: the document also holds the nav, the footer and whatever
       sits below the case study, and a line that is still at 80% when the
       reader has finished reading is measuring the wrong thing.

       The reading position is the BOTTOM of the viewport, so the line
       fills as the last section comes into view and lands on 1 exactly
       when the column's last pixel does.

       The bar is missing on any page that predates it, so every use is
       guarded rather than assumed. */
    var bar = doc.querySelector('[data-case-prog-bar]');
    var main = doc.querySelector('.case__main');

    /* The contents button and the one line on it that changes. Both are
       absent on a page built before them, so both are guarded. */
    var toc = rail.querySelector('[data-case-toc]');
    var now = rail.querySelector('[data-case-now]');
    var nav = rail.querySelector('.case__nav');

    function progress() {
      if (!bar || !main) return;
      var box = main.getBoundingClientRect();
      var top = box.top + win.scrollY;
      /* The span the reader actually travels: the column's height less one
         viewport, because the last screenful needs no scrolling to be
         read. A column shorter than the window is already fully read. */
      var span = box.height - win.innerHeight;
      var p = span > 0 ? (win.scrollY - top) / span : 1;
      if (p < 0) p = 0;
      if (p > 1) p = 1;
      bar.style.transform = 'scaleX(' + p + ')';
    }

    /* The line the reading position is measured against: just under the
       fixed nav, a third of the way down. A section counts as current from
       the moment its heading crosses it. --case-top is the same token the
       rail sticks to and anchors scroll to, so the three cannot drift. */
    function markLine() {
      return navHeight() + win.innerHeight * 0.28;
    }

    function update() {
      progress();

      var line = markLine();

      /* The last section whose top has passed the line. Falling back to the
         first means the rail is never blank at the top of the page. */
      var active = items[0];
      for (var i = 0; i < items.length; i++) {
        if (items[i].el.getBoundingClientRect().top <= line) active = items[i];
      }

      /* The foot of the page can be unreachable for the last section if it
         is short — nothing ever crosses the line — so the bottom of the
         scroll always selects the last item. */
      if (win.innerHeight + win.scrollY >= doc.documentElement.scrollHeight - 2) {
        active = items[items.length - 1];
      }

      if (active !== current) {
        if (current) {
          current.link.classList.remove('is-on');
          current.link.removeAttribute('aria-current');
        }
        active.link.classList.add('is-on');
        active.link.setAttribute('aria-current', 'true');
        current = active;
        keepVisible(active.link);
        say(active.link);
      }
    }

    /* The button's second line is the section being read. It is taken from
       the rail's own item rather than from the section's heading, so the
       button, the contents and the page can only ever say one thing. */
    function say(link) {
      if (!now) return;
      var label = link.querySelector('.case__label');
      if (label) now.textContent = label.textContent;
    }

    /* A long contents list scrolls inside the rail, and the active item is
       often outside the part of it that is showing. Scroll it into view —
       but only along the axis that actually overflows, and only inside the
       box that owns that overflow, which is why this is not
       scrollIntoView(): that one walks up the ancestors and will scroll the
       window as well, dragging the reader away from what they were reading.

       Which box scrolls depends on the layout, so it is asked rather than
       assumed: the contents column on the desktop, the panel on a phone,
       and on an older build the list itself along its own x axis. */
    function scroller() {
      var boxes = [nav, rail.querySelector('.case__rail-in'), list];
      for (var i = 0; i < boxes.length; i++) {
        var b = boxes[i];
        if (!b) continue;
        if (b.scrollHeight > b.clientHeight + 1) return b;
        if (b.scrollWidth > b.clientWidth + 1) return b;
      }
      return null;
    }

    function keepVisible(link) {
      var box = scroller();
      if (!box) return;
      var l = link.getBoundingClientRect(), r = box.getBoundingClientRect();
      if (box.scrollHeight > box.clientHeight + 1) {
        if (l.top < r.top + 8) box.scrollBy({ top: l.top - r.top - 24, behavior: 'smooth' });
        else if (l.bottom > r.bottom - 8) box.scrollBy({ top: l.bottom - r.bottom + 24, behavior: 'smooth' });
        return;
      }
      if (l.left < r.left + 8) box.scrollBy({ left: l.left - r.left - 16, behavior: 'smooth' });
      else if (l.right > r.right - 8) box.scrollBy({ left: l.right - r.right + 16, behavior: 'smooth' });
    }

    /* ---- the contents panel ---------------------------------------------
       A disclosure, not a dialog. Focus stays on the button: there is one
       control, it says what it does, and the panel it opens is the next
       thing in the tab order anyway, so moving focus for the reader would
       only take away the choice of whether to go in.

       The panel is CLOSED on arrival on the narrow layout and open on the
       wide one, and neither state is written here — CSS decides which it
       is from the width. All this owns is the flag. */
    function setOpen(open) {
      rail.setAttribute('data-open', open ? 'true' : 'false');
      if (toc) toc.setAttribute('aria-expanded', open ? 'true' : 'false');
      /* Opening it is the moment the active item has to be in view, and
         until it is open it has no height to measure against. */
      if (open && current) win.requestAnimationFrame(function () { keepVisible(current.link); });
    }
    function isOpen() { return rail.getAttribute('data-open') === 'true'; }

    if (toc) {
      toc.addEventListener('click', function () { setOpen(!isOpen()); });

      /* Escape closes it and leaves focus on the control that opened it,
         which is where a reader's hands already are. */
      doc.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && isOpen()) { setOpen(false); toc.focus(); }
      });

      /* A press anywhere outside closes it. pointerdown rather than click,
         so the panel is gone before the thing underneath it reacts. */
      doc.addEventListener('pointerdown', function (e) {
        if (isOpen() && !rail.contains(e.target)) setOpen(false);
      });
    }

    /* One read per frame at most. Scroll fires far more often than the page
       can paint, and every handler here measures layout. */
    var queued = false;
    function onScroll() {
      if (queued) return;
      queued = true;
      win.requestAnimationFrame(function () { queued = false; update(); });
    }

    win.addEventListener('scroll', onScroll, { passive: true });
    win.addEventListener('resize', onScroll, { passive: true });

    /* A click scrolls the window itself rather than letting the browser
       follow the anchor, for two reasons.

       The marker is the smaller one: moving it on click, rather than when
       the scroll arrives, stops a 600ms smooth scroll from spending its
       whole length pointing at the previous section.

       The larger one is that the native jump is not safe on these pages. A
       section holding one of the wide artefacts — an allocation sheet three
       times the column's width, inside its own scroll box — makes Chrome
       grow the document's scrollable width to reach it, and the page can
       then be dragged a few hundred pixels sideways into empty space.
       Measured on the planning page: jumping to two sections took the
       document from 1440 to 1913. Scrolling the window by a computed Y
       never touches the X axis, so the page stays where it is. Plain
       scrolling never triggered it; only the jump did.

       The offset comes from the same scroll-margin-top the stylesheet sets,
       so the two cannot disagree. */
    function offsetFor(el) {
      var m = parseFloat(win.getComputedStyle(el).scrollMarginTop);
      return isFinite(m) ? m : 0;
    }

    links.forEach(function (link) {
      link.addEventListener('click', function (e) {
        var id = link.getAttribute('data-case-link');
        var item = null;
        for (var i = 0; i < items.length; i++) {
          if (items[i].el.id === id) { item = items[i]; break; }
        }
        if (!item) return;                       // let the anchor do its thing

        e.preventDefault();

        var y = item.el.getBoundingClientRect().top + win.pageYOffset - offsetFor(item.el);
        var smooth = !(win.matchMedia && win.matchMedia('(prefers-reduced-motion: reduce)').matches);
        if (win.scrollTo && smooth) win.scrollTo({ top: y, behavior: 'smooth' });
        else win.scrollTo(0, y);

        /* The address bar should still carry the section, so the link can be
           copied and shared — but without the browser jumping again. */
        if (win.history && win.history.replaceState) win.history.replaceState(null, '', '#' + id);

        /* Keyboard focus follows the link, the way a real anchor would move
           it, and preventScroll keeps that from undoing the scroll above. */
        if (!item.el.hasAttribute('tabindex')) item.el.setAttribute('tabindex', '-1');
        try { item.el.focus({ preventScroll: true }); } catch (err) { /* older browsers */ }

        if (current) {
          current.link.classList.remove('is-on');
          current.link.removeAttribute('aria-current');
        }
        link.classList.add('is-on');
        link.setAttribute('aria-current', 'true');
        current = item;
        say(link);
        /* The panel has done its job. Closing it here rather than on the
           scroll's arrival means the reader sees the page they asked for
           rather than the panel they are finished with. */
        setOpen(false);
        keepVisible(link);
      });
    });

    update();
    /* Fonts land after first paint and change every section's position. */
    if (doc.fonts && doc.fonts.ready) doc.fonts.ready.then(update);
  }

  /* ---- the title handoff -------------------------------------------------
     The project's name is set twice on a case study: once in the hero, at
     full size, and once at the top of the rail. Only one of them is ever
     on the screen. The hero has it to begin with; the rail's copy is a
     collapsed grid row until the hero's has scrolled clear of the window,
     and then it opens in its place.

     An IntersectionObserver is the right tool here and not the wrong one,
     unlike the reading marker above: there is one element, it has one
     threshold, and the question is binary. The rootMargin pulls the top of
     the observed area down past the fixed nav, so the handover happens when
     the hero title disappears UNDER THE NAV rather than a nav's height
     later.

     boundingClientRect.top < 0 is what distinguishes gone-upwards from
     not-yet-arrived: a hero below the fold is also not intersecting, and
     without the test the rail would carry the title before the reader had
     ever seen the hero — on a deep link straight to a section, for one.

     No observer, no hero: the row simply opens, because the alternative is
     a rail with no name on it at all. */
  function handoff(rail) {
    var hero = doc.querySelector('.page-hero__title');
    var titled = null;

    function on(v) {
      v = !!v;
      if (v === titled) return;              // one write per change, not per frame
      titled = v;
      rail.setAttribute('data-case-titled', v ? 'true' : 'false');
    }

    /* No hero to hand over from, so the rail keeps its name from the start:
       the alternative is a rail with nothing naming it. */
    if (!hero) { on(true); return null; }

    on(false);

    /* Measured against the nav, not observed. An IntersectionObserver was
       the first version of this and it was the wrong tool for the same
       reason it is wrong for the reading marker above: it reports a change
       in intersection, and on these pages it did not always report one —
       measured on four of the eight case studies at 390px, the hero could
       be 2364px above the window with the observer never having fired a
       second entry. A comparison against one line gives the same answer
       every frame, from any scroll position, including a deep link that
       lands halfway down the page having never crossed the hero at all. */
    return function () {
      on(hero.getBoundingClientRect().bottom <= navHeight());
    };
  }

  if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', init);
  else init();
})(window, document);
