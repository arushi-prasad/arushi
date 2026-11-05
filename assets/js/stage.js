/* ===========================================================================
   STAGE — the homepage.
     1. The wordmark letters
     2. The design-token controls
     3. The selection box that scales the wordmark
     4. The live token readout
     5. The ruler of years
   Everything that changes a token goes through window.APTokens. Nothing here
   writes a style on anything but the wordmark's own hues.
   ========================================================================= */
(function (win, doc) {
  'use strict';

  var T = win.APTokens;
  var stage = doc.querySelector('.stage');
  if (!stage || !T) return;

  var reduced = win.matchMedia ? win.matchMedia('(prefers-reduced-motion: reduce)') : null;
  function noMotion() { return !!(reduced && reduced.matches); }
  var coarse = win.matchMedia ? win.matchMedia('(hover: none)') : null;
  function isTouch() { return !!(coarse && coarse.matches); }

  /* =========================================================================
     1 · THE NAME
     The cursive "arushi" is the name, permanently. There is no state here any
     more: no hover, no focus swap, no tap toggle, no class, nothing for a
     reset to put back. The capitals behind it are held at zero opacity by the
     stylesheet and are read by this file only as geometry — the portal elbows
     are aimed at the letter each one belongs to, and the selection box is
     drawn around the row they make.

     What used to live here: a pointer leaving .wm restored the capitals, a
     tap toggled them on touch (which has no "leave"), and a palette change
     or a reset put them back. All three were in service of a state that no
     longer exists.
     ====================================================================== */
  var letters = Array.prototype.slice.call(stage.querySelectorAll('.wm__l'));
  var mark = stage.querySelector('.wm');

  /* =========================================================================
     2 · THE DESIGN-TOKEN CONTROLS
     The row of five under the hero is a timeline now. Magic survived it and
     moved into the header, which is outside .stage — so the two elements it
     owns are looked up on the document, not on the stage. The other four
     controls kept their keyboard shortcuts and nothing else; `tools` is
     empty unless a row of them is put back, and everything below works the
     same either way.
     ====================================================================== */
  var tools = Array.prototype.slice.call(stage.querySelectorAll('.tool[data-tool]'));
  var statusLine = stage.querySelector('[data-token-status]');
  var statusTimer = 0;
  var sayLine = doc.querySelector('[data-say]');

  /* Which token each control drives, and the word it says when it does.
     The values come from T.OPTIONS — the same ordered lists the store
     validates against — so there is one definition of what a palette or a
     grid can be, not a second copy living out here. */
  var DRIVES = {
    colour: { key: 'palette' },
    type:   { key: 'type' },
    radius: { key: 'radius' },
    grid:   { key: 'grid' }
  };

  /* -----------------------------------------------------------------------
     The annotation.

     Everything numeric in it is measured off the page after the change has
     landed — never written down here. A hard-coded "6PX" would quietly start
     lying the day somebody edits --radius-k, and the whole point of the
     label is that it reports what is actually on screen.

     Custom properties hold unresolved calc() until something uses them, so
     a probe element is given the token and asked what it came to. The same
     trick reads the accent as a real colour rather than a var() reference.
     -------------------------------------------------------------------- */
  var probe = doc.createElement('span');
  probe.setAttribute('aria-hidden', 'true');
  probe.style.cssText = 'position:absolute;left:-9999px;top:0;width:0;height:0;' +
                        'visibility:hidden;pointer-events:none;';
  stage.appendChild(probe);

  function measurePx(expr) {
    probe.style.width = '0';
    probe.style.width = expr;
    var n = parseFloat(win.getComputedStyle(probe).width);
    return isFinite(n) ? Math.round(n) : 0;
  }

  function measureHex(expr) {
    probe.style.color = expr;
    var c = win.getComputedStyle(probe).color;           // rgb(r, g, b)
    var m = c.match(/(\d+)\s*,\s*(\d+)\s*,\s*(\d+)/);
    if (!m) return '';
    return '#' + [m[1], m[2], m[3]].map(function (v) {
      return ('0' + Number(v).toString(16)).slice(-2);
    }).join('').toUpperCase();
  }

  /* The playful half. Only the names live here; every value beside them is
     read back off the page. */
  var NAMES = {
    palette: { mono: 'Soft Mono', copper: 'Toasted Copper', botanical: 'Moss Club' },
    radius:  { sharp: 'Sharp Edges', subtle: 'Soft Corners', rounded: 'Round Things' },
    grid:    { classic: 'Square Club', dots: 'Dots Everywhere', off: 'Off The Grid' }
  };

  function familyOf(el) {
    var fam = win.getComputedStyle(el).fontFamily || '';
    var first = (fam.split(',')[0] || '').replace(/["']/g, '').trim();
    if (/mono/i.test(first)) return 'Mono';
    if (/iowan|charter|georgia|times|serif/i.test(first)) return 'Serif';
    return 'Sans';
  }

  /* What the label says for each control, built after the change applied. */
  function metaFor(key) {
    var now = T.get()[key];
    if (key === 'palette') {
      return { text: NAMES.palette[now] + ' · ' + measureHex('var(--accent)'),
               dot: 'var(--accent)' };
    }
    if (key === 'type') {
      var el = mark || stage;
      return { text: familyOf(el) + ', ' + Math.round(parseFloat(win.getComputedStyle(el).fontSize)) + 'px' };
    }
    if (key === 'radius') {
      return { text: NAMES.radius[now] + ' · ' + measurePx('var(--radius-md)') + 'px' };
    }
    if (key === 'grid') {
      return { text: NAMES.grid[now] };
    }
    return { text: '' };
  }

  var sayTimer = 0;
  function announce(key) {
    if (!sayLine) return;
    var meta = metaFor(key);
    if (sayTimer) { win.clearTimeout(sayTimer); sayTimer = 0; }

    sayLine.textContent = meta.text;
    if (meta.dot) {
      var i = doc.createElement('i');
      i.className = 'magic__dot';
      i.style.background = meta.dot;
      sayLine.insertBefore(i, sayLine.firstChild);
    }

    // Re-run the entrance even when the label is already showing, so a second
    // press on the same control reads as a fresh annotation.
    sayLine.classList.remove('is-on');
    void sayLine.offsetWidth;
    sayLine.classList.add('is-on');

    sayTimer = win.setTimeout(function () {
      sayTimer = 0;
      sayLine.classList.remove('is-on');
    }, 3200);
  }

  /* One click, one step along that control's list, wrapping at the end.
     There is nothing to open: the change itself is the response. */
  function cycle(tool) {
    var plan = DRIVES[tool];
    if (!plan) return;
    var list = (T.OPTIONS && T.OPTIONS[plan.key]) || [];
    if (!list.length) return;

    var now = T.get()[plan.key];
    var at = -1;
    for (var i = 0; i < list.length; i++) { if (list[i].id === now) { at = i; break; } }
    var next = list[(at + 1) % list.length];

    T.set(plan.key, next.id);
    announce(plan.key);
    say(next.label + ' ' + plan.key + '.', 4000);
  }

  tools.forEach(function (btn) {
    btn.addEventListener('click', function () { cycle(btn.getAttribute('data-tool')); });
  });

  /* =========================================================================
     3 · MAGIC
     One button in the header, and one job: five personal details out across
     the hero, or away again. Nothing else.

     It used to do more. A press also set a palette, a grid and a corner
     radius, which meant "a little more me" repainted the whole site — and
     repainted over whatever the visitor had chosen for themselves on the way
     past. Those three belong to them. This control no longer has an opinion
     about any of them, and the button itself no longer changes either: same
     icon, same name, same hint, pressed or not. What changed is the page,
     which is where a visitor was looking.

     The state lives in two strings and nowhere else: a class on the stage,
     which the stylesheet reads to stand the four secondary links and the
     career timeline down, and a class on the sticker layer, which the
     stylesheet reads to bring the set in. Those two are the whole of what a
     press does — no styles are written from here, nothing is built, nothing
     is cloned and nothing is thrown away, so the twentieth press costs
     exactly what the first one did and leaves exactly five stickers on the
     page.

     Nothing that goes away is taken out of the flow: the links and the
     timeline keep their boxes and lose only their opacity and their
     visibility, so the page under them never moves and both come back to the
     pixel they left.
     ====================================================================== */
  var surpriseBtn = doc.querySelector('[data-surprise]');
  var magicOn = false;

  /* Filled in by the peek section further down. A press that stands the
     links down has to put away whatever one of them was previewing: a group
     of images left open around the name would be floating beside a link that
     is no longer there. Declared here as a no-op, so neither section has to
     care which of them is read first. */
  var hidePeek = function () {};

  /* -----------------------------------------------------------------------
     THE STICKERS
     Five illustrations that live in the markup from the first frame and are
     never built, cloned or destroyed. A press adds one class and takes it
     off again. That is the whole of it, which is why pressing the button
     twenty times leaves exactly five stickers on the page rather than a
     hundred, and why they land in the same five places every time.

     Two things are worth measuring rather than declaring. The art is fetched
     on first use, so a visitor who never presses the button never pays for
     it. And the flight is read off the laid-out page: each sticker is told
     the vector from where it is about to land back to the button in the
     header, so the set is genuinely thrown from the control rather than
     fading up where it stands. Both are cheap, and both are the difference
     between a trick and a thing that behaves.
     -------------------------------------------------------------------- */
  var stickerLayer = stage.querySelector('[data-stickers]');
  var stickerItems = stickerLayer
    ? Array.prototype.slice.call(stickerLayer.querySelectorAll('.sticker'))
    : [];

  function stickerLoad() {
    stickerItems.forEach(function (fig) {
      var img = fig.querySelector('.sticker__art');
      var src = img && img.getAttribute('data-src');
      if (!src) return;
      img.src = src;
      img.removeAttribute('data-src');
    });
  }

  /* Where each one is about to land, taken from the layer's own box and the
     percentage the stylesheet holds for it — not from the figure's current
     rectangle, which is still wearing the last flight's transform and would
     measure the journey from itself.

     Written inline, which is the whole reason stickerHome() exists: an
     inline custom property outranks every rule in the stylesheet, so a
     vector left on the element would hold the sticker at the button and no
     landed state could ever pull it off. It is the start of a journey, not
     a position — so it is taken off again the moment the browser has seen
     it. */
  function stickerAim() {
    if (!stickerLayer || !surpriseBtn) return;
    /* Asked for stillness: there is no journey to aim, and a vector left on
       the element would jump the set to the button on the way out. */
    if (noMotion()) { stickerHome(); return; }
    var layer = stickerLayer.getBoundingClientRect();
    var btn = surpriseBtn.getBoundingClientRect();
    var bx = btn.left + btn.width / 2;
    var by = btn.top + btn.height / 2;

    stickerItems.forEach(function (fig) {
      var cs = win.getComputedStyle(fig);
      if (cs.display === 'none') return;            // stood down at this width
      var x = parseFloat(cs.getPropertyValue('--x'));
      var y = parseFloat(cs.getPropertyValue('--y'));
      if (!isFinite(x) || !isFinite(y)) return;
      var cx = layer.left + layer.width * x / 100;
      var cy = layer.top + layer.height * y / 100;
      fig.style.setProperty('--fx', Math.round(bx - cx) + 'px');
      fig.style.setProperty('--fy', Math.round(by - cy) + 'px');
    });
  }

  /* Hand the vector back to the stylesheet. */
  function stickerHome() {
    stickerItems.forEach(function (fig) {
      fig.style.removeProperty('--fx');
      fig.style.removeProperty('--fy');
    });
  }

  function stickerDrop() {
    if (!stickerLayer) return;
    stickerLoad();

    stickerLayer.classList.remove('is-in');
    void stickerLayer.offsetWidth;                  // the drop has to land
    stickerAim();

    /* The start of the journey has to be a style the browser has actually
       seen, or there is nothing for the transition to run from and the set
       simply appears. Reading a layout property flushes the offsets written
       just above; the vector then comes off and the class goes on in the
       same breath, which makes the resting place the target. A frame
       callback would do the same job and not run at all in a tab that is
       not being painted — this cannot be deferred to a frame that may never
       come. */
    void stickerLayer.offsetWidth;
    stickerHome();
    stickerLayer.classList.add('is-in');
  }

  /* They leave the way they came, captions with them. Aiming and dropping
     the class happen in one go, so the browser sees a single change — from
     where they are resting to small, faded and back at the button — and runs
     it as one exit rather than two. */
  function stickerClear() {
    if (!stickerLayer) return;
    stickerAim();
    stickerLayer.classList.remove('is-in');
  }

  /* -----------------------------------------------------------------------
     The toggle itself.

     aria-pressed is what carries the state, so the accessible name can stay
     one fixed phrase that says what the button does. A control that renames
     itself halfway through is two controls wearing one pill, and a visitor
     who presses it twice has to work out which one they just used.

     Written as set-to-a-value rather than flip-a-flag, so the one other
     caller — the restart, which has to be able to say "off" whatever is on
     screen — cannot get it the wrong way round.
     -------------------------------------------------------------------- */
  function magicSet(on) {
    magicOn = !!on;
    if (surpriseBtn) surpriseBtn.setAttribute('aria-pressed', magicOn ? 'true' : 'false');
    stage.classList.toggle('is-magic', magicOn);

    if (magicOn) {
      hidePeek();
      /* A keyboard visitor can be standing on one of the four links, or on a
         milestone in the timeline, when the shortcut fires. visibility:hidden
         would drop their place back to the top of the document, so focus is
         handed to the control that did it — which is also the control that
         undoes it. */
      var at = doc.activeElement;
      if (surpriseBtn && at && at.closest && at.closest('.portals, .portals-flat, .arc')) {
        surpriseBtn.focus();
      }
      stickerDrop();
      say('a little more ME \u2014 five stickers across the hero. The four ' +
          'section links and the timeline are resting while they are up.', 5000);
    } else {
      stickerClear();
      say('Stickers away. The section links and the timeline are back.', 4000);
    }
  }

  function magicToggle() { magicSet(!magicOn); }

  if (surpriseBtn) surpriseBtn.addEventListener('click', magicToggle);

  /* Keyboard shortcuts: 1–4 step a control, 5 is the Magic button — the
     same toggle the press is, both ways — and 0 resets. Suppressed whenever
     the visitor is typing or using a control. */
  doc.addEventListener('keydown', function (e) {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    var t = e.target;
    var tag = t && t.tagName;
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || (t && t.isContentEditable)) return;

    var map = { '1': 'colour', '2': 'type', '3': 'radius', '4': 'grid' };
    if (map[e.key]) { e.preventDefault(); cycle(map[e.key]); }
    if (e.key === '5') { e.preventDefault(); magicToggle(); }
    if (e.key === '0') { e.preventDefault(); restart(); }
  });

  /* =========================================================================
     4 · SELECTION BOX
     The Type tool draws a selection box around the wordmark. Dragging a
     handle scales the mark; so do the arrow keys when a handle has focus.
     Home returns it to 1×.

     The wordmark's container reserves the largest footprint the scale can
     reach, so nothing below it moves while this is happening.
     ====================================================================== */
  var wm = stage.querySelector('.wm');
  var handles = Array.prototype.slice.call(stage.querySelectorAll('.sel__h'));
  var readout = stage.querySelector('[data-scale-readout]');
  var LIM = T.LIMITS.scale;

  function axisFor(node) {
    if (node === 't' || node === 'b') return 'y';
    if (node === 'l' || node === 'r') return 'x';
    return 'both';
  }

  handles.forEach(function (h) {
    var node = h.getAttribute('data-node');
    var axis = axisFor(node);
    var drag = null;

    h.addEventListener('pointerdown', function (e) {
      if (!wm) return;
      e.preventDefault();
      var r = wm.getBoundingClientRect();
      var cx = r.left + r.width / 2;
      var cy = r.top + r.height / 2;
      var dx = e.clientX - cx, dy = e.clientY - cy;
      var d0 = axis === 'x' ? Math.abs(dx)
             : axis === 'y' ? Math.abs(dy)
             : Math.sqrt(dx * dx + dy * dy);
      if (d0 < 8) return; // too close to the centre for a stable ratio
      drag = { cx: cx, cy: cy, d0: d0, s0: T.get().scale };
      h.setPointerCapture(e.pointerId);
      wm.classList.add('is-dragging');
    });

    h.addEventListener('pointermove', function (e) {
      if (!drag) return;
      var dx = e.clientX - drag.cx, dy = e.clientY - drag.cy;
      var d = axis === 'x' ? Math.abs(dx)
            : axis === 'y' ? Math.abs(dy)
            : Math.sqrt(dx * dx + dy * dy);
      T.set('scale', drag.s0 * (d / drag.d0), { transient: true });
    });

    function end(e) {
      if (!drag) return;
      drag = null;
      if (wm) wm.classList.remove('is-dragging');
      try { h.releasePointerCapture(e.pointerId); } catch (err) { /* already released */ }
      T.set('scale', T.get().scale); // commit the final value to storage
    }
    h.addEventListener('pointerup', end);
    h.addEventListener('pointercancel', end);

    h.addEventListener('keydown', function (e) {
      var s = T.get().scale, step = e.shiftKey ? 0.1 : 0.02, moved = true;
      if (e.key === 'ArrowUp' || e.key === 'ArrowRight') T.set('scale', s + step);
      else if (e.key === 'ArrowDown' || e.key === 'ArrowLeft') T.set('scale', s - step);
      else if (e.key === 'Home') T.set('scale', 1);
      else if (e.key === 'End') T.set('scale', LIM[1]);
      else moved = false;
      if (moved) e.preventDefault();
    });
  });

  /* =========================================================================
     5 · RENDER
     One function paints every control from the store. Called on boot and on
     every change, so the UI can never disagree with the tokens.
     ====================================================================== */
  function render() {
    var s = T.get();


    // Scale readout
    if (readout) readout.textContent = s.scale.toFixed(2) + '×';
    handles.forEach(function (h) {
      h.setAttribute('aria-valuenow', s.scale.toFixed(2));
    });

  }

  T.subscribe(render);
  render();

  /* A note for anyone who reaches the page with a stored preference set. */
  if (!T.isDefault() && statusLine) {
    say('Your saved token settings were restored.', 4000);
  }

  /* =========================================================================
     6 · THE CONNECTORS
     Each portal is tied to one letter of the name by a hairline line: off the
     top of that letter, up through the open space, and into the pill it
     belongs to. Every line has two ends that are both on something — a
     marker a few pixels above the ink at the bottom, the pill's own edge at
     the top — so none of them floats.

     They used to be aimed at the six capitals, which is where the geometry
     still comes from: the capitals are the row the page is laid out against.
     But the capitals are invisible now, and a line that stops at the top of
     an invisible letter stops in open space above the script — pointing at
     nothing, from nothing. So the anchors are measured off the cursive word
     itself. See scriptAnchors() below for why that takes a canvas as well as
     a Range.

     Measured, not hard-coded. The mark is fluid (--wm-w), the Type control
     scales it, the Spacing control moves the portals, and a late webfont
     changes every width — so the only reliable source of these coordinates
     is the laid-out page. Everything that can move calls scheduleWires().

     Decorative: hidden from assistive technology, and dimmed by Contrast.
     ====================================================================== */
  var wireLayer = stage.querySelector('.portal-wires');
  var canvas = stage.querySelector('.stage__canvas');

  /* The four markers. Tiny, hairline, and drawn from the same stroke weight
     as the lines, so each link gets a character of its own without becoming
     an icon set. Sized for roughly 11px across. */
  var MARKS = {
    sparkle:  '<path class="mark mark--fill" d="M0 -5.5 L1.3 -1.3 L5.5 0 L1.3 1.3 L0 5.5 L-1.3 1.3 L-5.5 0 L-1.3 -1.3 Z"/>',
    asterisk: '<path class="mark" d="M0 -5 V5 M-4.3 -2.5 L4.3 2.5 M-4.3 2.5 L4.3 -2.5"/>',
    plus:     '<path class="mark" d="M0 -4.8 V4.8 M-4.8 0 H4.8"/>',
    ring:     '<circle class="mark" cx="0" cy="0" r="4"/><circle class="mark mark--fill" cx="0" cy="0" r="1.1"/>'
  };

  /* Which letter of ARUSHI each station reaches down to, and roughly where
     it sits across the width of the mark. A=0 R=1 U=2 S=3 H=4 I=5. Each pill
     is placed almost directly over its own letter, which is what keeps the
     connectors short and nearly straight. */
  var MIN_HEADROOM = 12;   // breathing room between the top tier and the nav
  var MAX_DROP = 220;      // a ceiling, so a strange layout cannot run away

  /* Which letter of "arushi" each station comes down on. a=0 r=1 u=2 s=3
     h=4 i=5. Each pill is placed directly over its own letter, which is what
     keeps the connectors short and vertical; x is the fallback position,
     used only if the word cannot be measured. */
  /* The tiers are not decoration. A pill on the upper tier drops its line
     through the band the lower tier sits in, so the two on each side have to
     be stacked in the order that leaves that drop clear: on the left the
     outer letter (a) is above and the inner one (r) below, and on the right
     it is the other way round, because the two letters there are the h and
     the dot of the i — barely a pill's width apart, with the wider label on
     the h. Put About above and its line would come down straight through
     Experiments. */
  /* The left pair, and why they are shaped the way they are.

     Fun stuff is pulled out past the start of the word by about as much as
     About passes the end of it, so the name has a shoulder on both sides
     rather than one. It is the only pill not overhead, and its connector is
     the only elbow: out of the left flank of the a, along, and up into it.

     Writing used to come down on the r, pulled left by a share of the word.
     That pull had almost nothing left in it. A drop stays a plain vertical
     only while the letter it lands on is still inside the pill's own width,
     and at 1440 the r's centre sat at x 662.5 against a pill spanning
     585-673 — about four pixels of travel. Asked for more, 0.145 was tried
     and the connector hooked, exactly as that rule predicts.

     So it comes down on the a instead, which is where the room actually is:
     a hundred and ten pixels further left, and the drop is a plain vertical
     again because the pill is back over its own letter. Fun stuff stays on
     the tier above, so the two never meet, and the elbow's rise passes to
     the left of this pill rather than through it. */
  var STATIONS = {
    ul: { letter: 0, x: 0.06, tier: 1, elbow: true },
    ll: { letter: 0, x: 0.10, tier: 0 },
    lr: { letter: 4, x: 0.69, tier: 1 },
    ur: { letter: 5, x: 0.94, tier: 0 }
  };

  var EDGE_RAIL = 14;   // a pill is never placed closer than this to the edge
  var TIP = 8;          // where a line stops short of the ink it points at
  /* The elbow's horizontal run, as a share of the word's width — so it is
     the same gesture whatever the name is scaled to. It is also what sets
     how far out the pill goes, the two being the same number. */
  var ELBOW_RUN = 0.06;

  /* Where the letters of the cursive word actually are.

     Two measurements, because one is not enough. A Range over the text node
     gives each character its own box — that is the horizontal half, and it
     is exact. But the vertical half is not in that box: a script face sets a
     tall line box with the glyphs sitting low inside it, so the top of a
     character's box is a long way above the top of the letter. Stop a line
     there and it ends in mid-air with a visible gap under it, which is the
     one thing these lines must not do.

     So the ink is measured too. The canvas 2D context, given the same font,
     reports actualBoundingBoxAscent — the real distance from the baseline to
     the top of that glyph's ink, which is different for the a and the h and
     is exactly what makes the difference worth measuring. The baseline is
     found from the box: the font's own ascent and descent sit centred in the
     line box, so half the leading is the offset into it.

     Everything degrades rather than breaks: no canvas, or a browser without
     the ink metrics, and the character's box top is used instead. */
  /* Where the letters of the cursive word actually are.

     The horizontal half is a Range over the text node: each character gets
     its own advance box, and that is exact. The vertical half cannot come
     from that box, and neither can the horizontal one be used on its own,
     for the same reason — this face leans. A script glyph sits low in a tall
     line box and leans out of its own advance, so the top of a character's
     box is both far above the letter and several pixels to the left of the
     stroke that actually reaches up there. Aim a line with those numbers and
     it ends in mid-air over the wrong letter; the h and the dot of the i are
     where that goes most visibly wrong.

     So the ink is measured, by drawing the word once into a canvas at its
     natural size and reading back, for every column of it, the first row
     that has paint in it. That profile answers both questions at once: given
     a letter's span, which column in it reaches highest (where the line
     should come down), and how high (where it should stop). It is taken in
     the word's own units and mapped onto wherever the word currently is, so
     the Type control scaling the name costs nothing — the profile is only
     rebuilt when the font itself changes.

     Everything here degrades rather than breaks: no canvas, no image data, a
     tainted or empty read, and the caller falls back to the capitals' boxes,
     which is where this all used to be measured from. */
  var inkCache = null;

  function inkProfile(sc, text, cs) {
    var font = cs.fontStyle + ' ' + cs.fontWeight + ' ' + cs.fontSize + ' ' + cs.fontFamily;
    var key = font + '|' + text;
    if (inkCache && inkCache.key === key) return inkCache.ok ? inkCache : null;

    var res = { key: key, ok: false };
    inkCache = res;
    try {
      var cv = doc.createElement('canvas');
      var ctx = cv.getContext('2d', { willReadFrequently: true });
      if (!ctx) return null;
      ctx.font = font;
      var m = ctx.measureText(text);
      var adv = m.width;
      var fAsc = m.fontBoundingBoxAscent, fDesc = m.fontBoundingBoxDescent;
      if (!(adv > 0) || !isFinite(fAsc) || !isFinite(fDesc)) return null;

      /* The box the DOM gives this text, in the same units: its line box is
         taller than the font, with the difference split above and below. */
      var natLine = sc.getBoundingClientRect().height;        // scaled
      var scale = sc.getBoundingClientRect().width / adv;     // transform, if any
      if (!(scale > 0)) return null;
      natLine = natLine / scale;

      var pad = Math.ceil(parseFloat(cs.fontSize) || 0) + 4;   // the lean's overhang
      var w = Math.max(1, Math.ceil(adv) + pad * 2);
      var h = Math.max(1, Math.ceil(natLine));
      cv.width = w; cv.height = h;
      ctx.font = font;                       // a resize clears the context
      ctx.textBaseline = 'alphabetic';
      ctx.fillStyle = '#fff';
      var baseY = (natLine - (fAsc + fDesc)) / 2 + fAsc;

      /* One glyph at a time, each on a cleared canvas, each at the pen
         position it has in the word. Drawing the whole word and reading
         columns off it looks equivalent and is not: this hand joins and
         leans, so the h's ascender passes clean over the top of the i, and a
         column read inside the i's advance would report the h. Isolating the
         glyph is what makes "the top of this letter" mean the letter. */
      var tops = [];
      for (var gi = 0; gi < text.length; gi++) {
        var penX = pad + ctx.measureText(text.slice(0, gi)).width;
        ctx.clearRect(0, 0, w, h);
        ctx.fillText(text.charAt(gi), penX, baseY);

        var gm = ctx.measureText(text.charAt(gi));
        var x0 = Math.max(0, Math.floor(penX - (gm.actualBoundingBoxLeft || 0) - 2));
        var x1 = Math.min(w - 1, Math.ceil(penX + (gm.actualBoundingBoxRight || gm.width) + 2));
        var strip = ctx.getImageData(x0, 0, Math.max(1, x1 - x0 + 1), h).data;
        var sw = Math.max(1, x1 - x0 + 1);

        /* Column by column, and only ever upward: once a column has been
           found with paint at row r, no later column needs looking at below
           r — it cannot win. The bound is the strip's own height, which is
           the whole of the point: an empty column with an unbounded limit
           walks to infinity and takes the frame with it. */
        var bestRow = h, bestCol = -1;
        for (var x = 0; x < sw; x++) {
          for (var y = 0; y < bestRow; y++) {
            if (strip[(y * sw + x) * 4 + 3] > 24) { bestRow = y; bestCol = x0 + x; break; }
          }
        }

        /* And the glyph's own box: the first column with any paint in it,
           and the lowest row any column reaches. The scan above answers
           "how high does this letter reach, and where" and stops the
           moment it can; this one has to look at every column, so it is
           kept separate rather than folded in and made to slow the common
           question down. Walking each column from the bottom means the
           first hit is that column's lowest paint, so one pass does both.

           It is what lets a line leave a letter from its side at its
           middle, rather than only from over the top of it. */
        var inkCol = -1, inkBot = -1;
        for (var x3 = 0; x3 < sw; x3++) {
          for (var y3 = h - 1; y3 >= 0; y3--) {
            if (strip[(y3 * sw + x3) * 4 + 3] > 24) {
              if (inkCol < 0) inkCol = x0 + x3;
              if (y3 > inkBot) inkBot = y3;
              break;
            }
          }
        }
        tops.push(bestCol < 0 ? null :
          { col: bestCol, row: bestRow, left: inkCol, bot: inkBot });
      }

      res.tops = tops; res.w = w; res.h = h; res.adv = adv; res.pad = pad; res.ok = true;
      return res;
    } catch (e) { return null; }
  }

  /* One anchor per letter: the column inside that letter's advance where its
     ink reaches highest, and the height it reaches. That is the point the
     pill is placed over and the line comes down on, which is why the line
     lands on the tip of the h and on the dot of the i rather than beside
     them. */
  function scriptAnchors() {
    var sc = mark && mark.querySelector('.wm__script');
    var node = sc && sc.firstChild;
    if (!node || node.nodeType !== 3 || !node.nodeValue) return null;

    var text = node.nodeValue;
    var scRect = sc.getBoundingClientRect();
    if (!scRect.width || !scRect.height) return null;

    var prof = inkProfile(sc, text, win.getComputedStyle(sc));
    var range = doc.createRange();
    var out = [];

    for (var i = 0; i < text.length; i++) {
      range.setStart(node, i);
      range.setEnd(node, i + 1);
      var r = range.getBoundingClientRect();
      if (!r.width && !r.height) { out.push(null); continue; }

      var anchor = { cx: r.left + r.width / 2, top: r.top };
      var g = prof && prof.tops[i];
      if (g) {
        /* The profile is in the word's own units, drawn with a pad either
           side; the word on the page is the same thing scaled and moved. */
        var k = scRect.width / prof.adv;
        anchor.cx = scRect.left + (g.col + 0.5 - prof.pad) * k;
        anchor.top = scRect.top + g.row * k;
        /* The flank and the middle of the ink, for a line that leaves the
           letter sideways instead of from above. Both from the same
           profile as everything else here, so a line drawn to them lands
           on the letter as it is actually painted. */
        if (g.left >= 0 && g.bot >= 0) {
          anchor.inkLeft = scRect.left + (g.left - prof.pad) * k;
          anchor.mid = scRect.top + ((g.row + g.bot) / 2) * k;
        }
      }
      out.push(anchor);
    }
    if (range.detach) range.detach();
    return out;
  }

  function drawWires() {
    if (!wireLayer || !canvas || !wm) return;
    // Below the wide breakpoint the arranged portals are hidden and the flat
    // row takes over, so there is nothing to place or connect.
    if (win.innerWidth < 1024) {
      wireLayer.innerHTML = '';
      stage.style.removeProperty('--stage-drop');
      Array.prototype.forEach.call(stage.querySelectorAll('.portal-slot'), function (s) {
        s.style.left = s.style.top = s.style.right = s.style.bottom = '';
      });
      return;
    }

    var base = canvas.getBoundingClientRect();
    var m = wm.getBoundingClientRect();
    /* Nothing here means anything without a laid-out page — a hidden tab, a
       display:none ancestor, a measurement taken before the first layout. In
       that state every rect is zero, and the headroom correction below would
       read a shortfall that is not real and keep asking for more room. Wait
       for a real measurement instead. */
    if (!base.width || !base.height || !m.height) return;
    var greet = stage.querySelector('.wm__greet');
    var g = greet ? greet.getBoundingClientRect() : m;

    wireLayer.setAttribute('viewBox', '0 0 ' + Math.round(base.width) + ' ' + Math.round(base.height));

    var mLeft = m.left - base.left;
    var mTop  = m.top - base.top;
    /* The script's width, not the mark's: the pull and the elbow below are
       measured against the word they are arranged around, and .wm is wider
       than the word it contains. */
    var scEl = stage.querySelector('.wm__script');
    var scR = scEl ? scEl.getBoundingClientRect() : null;
    var wordW = (scR && scR.width) ? scR.width : m.width;

    /* The anchors, and the floor they imply. The lower tier stops short of
       whichever comes first: the greeting, or the highest ink in the word —
       the h and the dot of the i climb well above the row the capitals
       occupy, and a pill parked on the capitals' box would sit on top of
       them. Measuring the ink is what keeps the two apart at every size the
       name is fluid across, rather than at the one size this was drawn at. */
    var anchors = scriptAnchors();
    var inkTop = Infinity;
    if (anchors) {
      for (var ai = 0; ai < anchors.length; ai++) {
        if (anchors[ai]) inkTop = Math.min(inkTop, anchors[ai].top);
      }
    }
    var floorY = (g.top - base.top) - 12;
    if (isFinite(inkTop)) {
      /* At the size the name is laid out at, not the size it is currently
         painted at. The Type control scales the mark with a transform, which
         moves the ink but moves nothing in layout — and the promise that
         control makes is that dragging it shifts nothing else on the page.
         Read the painted ink here and that promise breaks: the floor would
         rise with the drag, the pills would follow it, and the balance below
         would push the whole hero down under the pointer.

         The transform is a uniform scale about the mark's centre, so undoing
         it is one division. The connectors still aim at the painted ink —
         they are drawn on the word as it actually is. */
      var scaleNow = parseFloat(T.get().scale) || 1;
      var midY = m.top + m.height / 2;
      var inkLayout = midY + (inkTop - midY) / scaleNow;
      floorY = Math.min(floorY, (inkLayout - base.top) - 14);
    }

    var slots = Array.prototype.slice.call(stage.querySelectorAll('.portal-slot'));
    var tallest = 0;
    slots.forEach(function (slot) { tallest = Math.max(tallest, slot.getBoundingClientRect().height); });

    var out = '';
    slots.forEach(function (slot) {
      var portal = slot.querySelector('.portal');
      var plan = STATIONS[slot.getAttribute('data-at')];
      if (!portal || !plan) return;

      var sRect = slot.getBoundingClientRect();
      var pRect = portal.getBoundingClientRect();
      var inset = pRect.top - sRect.top;          // the note above the pill
      var pillBottom = floorY - plan.tier * (tallest + 14);

      /* Directly over the letter it comes down on, so the connector is a
         plain vertical and has no reason to bend. The fraction of the
         capitals' row is the fallback for the frame before the word can be
         measured. Clamped to the canvas: a pill pushed off the edge would
         take its images and its connector with it. */
      var a = anchors && anchors[plan.letter];
      var centre = a ? (a.cx - base.left) : (mLeft + plan.x * m.width);
      var half = pRect.width / 2;

      /* The slot is a column with the note above the pill and both centred
         in it, and the note is the wider of the two — so the slot's middle
         is not the pill's. For the three stations placed over their letter
         that difference is a few pixels of an already approximate thing and
         it is left alone. The elbow cannot afford it: its rise has to pass
         to the left of the word, and a pill a dozen pixels right of where it
         was asked to be is a line through the a. So that one station places
         the pill itself, and carries the slot's own offset through the clamp
         with it. */
      var insetX = 0;
      if (plan.elbow && a && isFinite(a.inkLeft)) {
        insetX = pRect.left - sRect.left;
        /* Far enough past the word for the elbow to have a run, and no
           further — the run and the overhang are the same measurement seen
           twice, which is what keeps the drawing and the placing agreeing. */
        centre = (a.inkLeft - base.left) - TIP - ELBOW_RUN * wordW;
      } else if (plan.pull) {
        centre -= plan.pull * wordW;
      }
      centre = Math.max(EDGE_RAIL + half + insetX,
                        Math.min(base.width - EDGE_RAIL - half - insetX, centre));

      slot.style.right = 'auto';
      slot.style.bottom = 'auto';
      slot.style.left = Math.round(centre - half - insetX) + 'px';
      slot.style.top  = Math.round(pillBottom - pRect.height - inset) + 'px';
    });

    /* Where the composition sits in the canvas.

       The flow content — the name and the two lines under it — is centred by
       the stylesheet, but the composition is taller than the flow: the pills
       hang above the name and are placed out of flow, so half of what the
       eye reads as "the hero" is invisible to the centring. Left alone it
       sits high, with the air pooling underneath.

       So the block is measured, top of the highest pill to the bottom of the
       last line, and the free space left over is split evenly above and
       below it. The stylesheet turns --stage-drop into a downward shift of
       exactly that size, and because the whole block moves together the
       correction lands in a single pass.

       MIN_HEADROOM is the floor, not the target it used to be: on a short
       viewport there is no slack to share out, and the only thing that
       matters is that the top tier clears the navigation. Nothing is drawn
       on the pass that moves the floor, so no line is ever drawn against
       geometry that is about to change. */
    var minTop = Infinity;
    var measured = false;
    slots.forEach(function (slot) {
      var r = slot.getBoundingClientRect();
      if (!r.height) return;              // same reasoning as above
      measured = true;
      minTop = Math.min(minTop, r.top - base.top);
    });
    /* The correction below assumes a fixed-height stage: there, doubling the
       canvas's top padding moves the centred block down by exactly half of
       it, which is what makes one pass converge. With a panel open the stage
       is height:auto, the same padding moves the content by the whole amount,
       and the correction over-shoots then under-shoots for ever. So it is
       only computed while the stage is in its one-screen state; the value
       already found is simply held. */
    if (measured && isFinite(minTop) && stage.getAttribute('data-tool') === 'none') {
      /* The bottom of the composition is the last line under the name. The
         timeline is not part of this: it is outside the canvas, and the
         space this is balancing is the space between the two. */
      var tail = stage.querySelector('.stage__years') ||
                 stage.querySelector('.stage__lede') ||
                 stage.querySelector('.wm-wrap');
      var tailR = tail ? tail.getBoundingClientRect() : null;
      var want = MIN_HEADROOM;
      if (tailR && tailR.height) {
        var blockBottom = tailR.bottom - base.top;
        var free = base.height - (blockBottom - minTop);
        if (free > MIN_HEADROOM * 2) want = free / 2;
      }
      var cur = parseFloat(stage.style.getPropertyValue('--stage-drop')) || 0;
      var next = Math.max(0, Math.min(cur + (want - minTop), MAX_DROP));
      if (Math.abs(next - cur) > 0.5) {
        stage.style.setProperty('--stage-drop', next.toFixed(1) + 'px');
        scheduleWires();
        return;
      }
    }

    /* Re-read after placing: the lines must be drawn against where the pills
       actually ended up, not where they were asked to go.

       Two shapes, and nothing else. Straight, when the pill is overhead,
       which after the placement above is the ordinary case: one vertical
       from the marker up into the pill's underside. L-shaped, when the pill
       had to be clamped away from its letter at the edge of the canvas: up
       the side of the word, then in to the pill's near edge at its middle.
       Both end exactly on the pill's own box — not near it — and both start
       at the marker, which sits a breath above the ink of the letter. */
    slots.forEach(function (slot) {
      var portal = slot.querySelector('.portal');
      var plan = STATIONS[slot.getAttribute('data-at')];
      if (!portal || !plan) return;

      var a = anchors && anchors[plan.letter];
      var letter = letters[plan.letter];
      if (!a && !letter) return;

      var p = portal.getBoundingClientRect();
      var ax, ay;
      if (a) {
        ax = a.cx - base.left;
        ay = a.top - base.top;                      // the top of the ink
      } else {
        var l = letter.getBoundingClientRect();
        ax = l.left - base.left + l.width / 2;
        ay = l.top - base.top + 3;
      }

      var pb = p.bottom - base.top;
      var pcy = p.top - base.top + p.height / 2;
      var pl = p.left - base.left, pr = p.right - base.left;

      /* Where the line starts, which for three of the four is a breath above
         the highest ink in the letter. */
      var nx = ax, ny = ay - TIP;
      var drawn = false;

      /* The elbow. Out of the left flank of the letter at the middle of its
         ink, along to under the middle of the pill, and up into its
         underside — the one connector that is not a drop, because its pill
         is not overhead. Drawn only if the pill really did end up left of
         the letter and above it; if the clamp has taken it somewhere else,
         this falls through to the two shapes below rather than drawing a
         line that doubles back on itself. */
      if (plan.elbow && a && isFinite(a.inkLeft) && isFinite(a.mid)) {
        var ex = (a.inkLeft - base.left) - TIP;
        var ey = a.mid - base.top;
        var rise = pl + p.width / 2;
        if (rise < ex - 4 && pb < ey - 4) {
          out += '<path class="wire" d="M' + ex.toFixed(1) + ' ' + ey.toFixed(1) +
                 ' H' + rise.toFixed(1) + ' V' + pb.toFixed(1) + '"/>';
          nx = ex; ny = ey; drawn = true;
        }
      }

      if (!drawn) {
        var tipY = ay - TIP;                        // where the line stops
        if (pb >= tipY - 2) return;                 // no room: draw nothing

        if (ax > pl + 6 && ax < pr - 6) {
          out += '<path class="wire" d="M' + ax.toFixed(1) + ' ' + tipY.toFixed(1) +
                 ' V' + pb.toFixed(1) + '"/>';
        } else {
          var edge = ax < pl ? pl : pr;
          out += '<path class="wire" d="M' + ax.toFixed(1) + ' ' + tipY.toFixed(1) +
                 ' V' + pcy.toFixed(1) +
                 ' H' + edge.toFixed(1) + '"/>';
        }
      }
      /* The marker sits on the end of its own line, so the line reads as
         ending somewhere rather than stopping. */
      out += '<g class="node" transform="translate(' + nx.toFixed(1) + ' ' + ny.toFixed(1) + ')">' +
             (MARKS[slot.getAttribute('data-mark')] || MARKS.ring) + '</g>';
    });

    wireLayer.innerHTML = out;
  }

  /* Assigned by the peek section below. The columns the images stand in can
     only be measured once the pills have been placed, which is the last thing
     drawWires does — so the two are measured together, off the same layout,
     and nothing has to guess what the other one decided. */
  var placePeek = null;

  var raf = 0;
  function scheduleWires() {
    if (raf) win.cancelAnimationFrame(raf);
    raf = win.requestAnimationFrame(function () {
      raf = 0;
      drawWires();
      if (placePeek) placePeek();
    });
  }

  win.addEventListener('resize', scheduleWires);
  T.subscribe(scheduleWires);
  /* The Type control changes the name's size through a transform, and a
     transform transitions. Measuring on the token change alone reads the size
     the name is leaving, not the one it is going to — so measure again when
     it has arrived. During a drag there is no transition to wait for, and the
     per-move passes keep up on their own. */
  if (wm) {
    wm.addEventListener('transitionend', function (e) {
      if (e.propertyName === 'transform' && e.target === wm) scheduleWires();
    });
  }
  if (doc.fonts && doc.fonts.ready) doc.fonts.ready.then(scheduleWires);
  scheduleWires();

  /* =========================================================================
     7 · THE INTRO, AND RESTARTING IT
     The stage assembles itself on arrival — greeting, letters, dots, portals,
     lede, hint. stage.css owns the choreography; this owns the lifecycle.

     Replaying a finished CSS animation needs the declarations to be dropped
     and reinstated, not merely re-applied: setting the same class twice is a
     no-op to the engine. data-intro="off" drops them, one forced reflow makes
     the drop real, and clearing it starts a genuinely new run from zero.

     States, written to data-intro so they are visible in the inspector and
     assertable from a test: (unset) first run · playing · done · off.
     ====================================================================== */
  var INTRO_MS = 1850;   // the last run to finish is the flat portal row
  var introTimer = 0;

  function say(msg, clearAfter) {
    if (!statusLine) return;
    if (statusTimer) { win.clearTimeout(statusTimer); statusTimer = 0; }
    statusLine.textContent = msg;
    if (clearAfter) {
      statusTimer = win.setTimeout(function () {
        statusTimer = 0;
        statusLine.textContent = '';
      }, clearAfter);
    }
  }

  function finishIntro() {
    introTimer = 0;
    stage.setAttribute('data-intro', 'done');
    // The portals were mid-translate while the intro ran, so the leader dots
    // measured during it are wrong. Draw them against the settled layout.
    scheduleWires();
  }

  function playIntro() {
    if (introTimer) { win.clearTimeout(introTimer); introTimer = 0; }

    if (noMotion()) { finishIntro(); return; }

    stage.setAttribute('data-intro', 'off');
    void stage.offsetWidth;                 // the cancellation has to land
    stage.setAttribute('data-intro', 'playing');
    introTimer = win.setTimeout(finishIntro, INTRO_MS);
  }

  /* The full restart. Everything the visitor can have changed goes back, in
     an order that leaves nothing half-applied: stop, reset, close, replay. */
  function restart() {
    // 1 · stop whatever is in flight, including a pending status wipe.
    if (introTimer) { win.clearTimeout(introTimer); introTimer = 0; }
    if (statusTimer) { win.clearTimeout(statusTimer); statusTimer = 0; }

    // 2 · tokens, scale included, back to their defaults.
    T.reset();

    // 3 · clear the contextual label, and put the stickers away. The Magic
    //     control owns nothing else now — no palette, no grid, no corners —
    //     so one call off is the whole of its share of a restart, and the
    //     four secondary links come back with the same transition a second
    //     press would have given them.
    if (sayLine) { sayLine.classList.remove('is-on'); sayLine.textContent = ''; }
    magicSet(false);

    /* The name used to need putting back here — it could be left in its
       cursive form by a hover or a tap. It is the cursive form now, in every
       state, so there is nothing to restore. */

    // 4 · replay from the first frame.
    playIntro();

    say('Restarted. Every token is back to its default.', 4000);
  }

  /* First run. The CSS plays it unprompted, so the stage still animates with
     this file absent; all that happens here is the bookkeeping. */
  if (noMotion()) {
    stage.setAttribute('data-intro', 'done');
  } else {
    stage.setAttribute('data-intro', 'playing');
    introTimer = win.setTimeout(finishIntro, INTRO_MS);
  }

  /* Coming back through the bfcache must not restore a half-played intro. */
  win.addEventListener('pageshow', function (e) {
    if (!e.persisted) return;
    if (introTimer) { win.clearTimeout(introTimer); introTimer = 0; }
    finishIntro();
    /* Nor a half-held Magic. Coming back to the homepage through the history
       must not land on stickers out and four links missing: the interaction
       is a thing you do while you are here, not a setting you leave behind. */
    magicSet(false);
  });

  /* =========================================================================
     7 · THE PEEK
     Each destination keeps a group of images in the page. Pointing at a link,
     tabbing to it, or tapping it once brings that group out around the name.

     Which group is showing is one attribute on the stage, and the stylesheet
     reads it. That is the whole state: there is no per-group bookkeeping to
     fall out of step, so moving quickly between links can only ever swap one
     attribute value for another — the group being left starts its exit in the
     same frame the next one starts its entrance, and nothing can be stranded.

     The images carry data-src rather than src. A visitor who never goes near
     a link never downloads them; the first sign of interest loads all twelve
     at once, so the second link is already warm.
     ====================================================================== */
  var peek = stage.querySelector('.peek');
  if (peek) {
    /* Both rows of links — the arranged one and the flat one below the wide
       breakpoint — are the same four destinations, and only one row is ever
       on screen, so both can be wired without them disagreeing. */
    var portals = Array.prototype.slice.call(stage.querySelectorAll('.portal'));
    var SECTION = { 'fun/': 'fun', 'writing/': 'writing',
                    'experiments/': 'experiments', 'about/': 'about' };

    var leaveTimer = null;   // the grace period between one link and the next
    var tapTimer = null;     // how long a touch preview stays up on its own
    var armed = null;        // the section a first tap has opened, if any
    var warmed = false;

    function sectionOf(a) { return SECTION[a.getAttribute('href')] || ''; }

    function warm() {
      if (warmed) return;
      warmed = true;
      stage.removeEventListener('pointermove', warmOnIntent);
      Array.prototype.forEach.call(peek.querySelectorAll('img[data-src]'), function (img) {
        img.src = img.getAttribute('data-src');
        img.removeAttribute('data-src');
      });
    }

    /* The first sign of a pointer anywhere on the stage is enough to start
       the downloads — it buys them the time it takes to travel to a link,
       which is usually the difference between a group arriving complete and
       a group arriving as three empty plates. Someone who never moves a
       mouse over it never fetches any of them. */
    function warmOnIntent(e) {
      if (e.pointerType === 'touch') return;     // a tap opens a group anyway
      warm();
    }
    stage.addEventListener('pointermove', warmOnIntent, { passive: true });

    function show(key) {
      if (leaveTimer) { win.clearTimeout(leaveTimer); leaveTimer = null; }
      warm();
      stage.setAttribute('data-peek', key);
      portals.forEach(function (a) {
        a.classList.toggle('is-peeking', sectionOf(a) === key);
      });
    }

    function hide() {
      if (leaveTimer) { win.clearTimeout(leaveTimer); leaveTimer = null; }
      if (tapTimer) { win.clearTimeout(tapTimer); tapTimer = null; }
      armed = null;
      stage.removeAttribute('data-peek');
      /* Put the drift back to centre as the group leaves, so the next one
         does not arrive already leaning wherever the pointer last was. */
      peek.style.removeProperty('--px');
      peek.style.removeProperty('--py');
      portals.forEach(function (a) { a.classList.remove('is-peeking'); });
    }

    /* The Magic control stands these four links down, so it needs to be able
       to put away whatever one of them had open. This is the only wire
       between the two sections, and it points this way on purpose: the peek
       knows nothing about Magic. */
    hidePeek = hide;

    /* Leaving a pill is not the same as leaving the interaction: the gap
       between two links is a few pixels of nothing. Without this pause the
       group would flash out and straight back in on the way across. */
    function hideSoon() {
      if (leaveTimer) win.clearTimeout(leaveTimer);
      leaveTimer = win.setTimeout(hide, 90);
    }

    portals.forEach(function (a) {
      var key = sectionOf(a);
      if (!key) return;

      a.addEventListener('pointerenter', function (e) {
        if (e.pointerType === 'touch') return;   // touch has its own path, below
        show(key);
      });
      a.addEventListener('pointerleave', function (e) {
        if (e.pointerType === 'touch') return;
        hideSoon();
      });

      /* Keyboard. Tabbing through the links walks the same compositions, so
         the preview is not something only a mouse can reach. */
      a.addEventListener('focus', function () { show(key); });
      a.addEventListener('blur', function () { hideSoon(); });

      /* Touch has no hover to borrow. The first tap opens the group and holds
         the link back; a second tap on the same link follows it. Another link
         moves the preview, a tap anywhere else puts it away, and so does a
         few seconds of nothing — so a visitor can never be stuck looking at
         pictures with no way through to the page. */
      a.addEventListener('click', function (e) {
        if (!isTouch()) return;
        if (armed === key) return;               // second tap: let the link work
        e.preventDefault();
        show(key);
        armed = key;
        if (tapTimer) win.clearTimeout(tapTimer);
        tapTimer = win.setTimeout(hide, 3200);
      });
    });

    doc.addEventListener('click', function (e) {
      if (!armed) return;
      var hit = e.target && e.target.closest ? e.target.closest('.portal') : null;
      if (!hit) hide();
    });

    /* How much room there actually is beside the name.

       The stylesheet could approximate this — the name is min(68vw, 62svh)
       wide and sits in the middle — but the approximation is wrong in the two
       cases that matter. The Type control scales the name between 0.6 and 1.4,
       and the two upper pills are hung off its ends and are as wide as their
       own labels: drag the name small and they reach a long way out past it,
       into exactly the space an image was about to use.

       So it is measured, from the same laid-out page the connectors are drawn
       from, and against the real obstacles — the name and all four pills. The
       narrower of the two columns is used for both, so the composition stays
       even. If what is left is too thin to hold a picture, the layer stands
       down rather than showing a sliver: the links still work, and nothing is
       only reachable through the images.  */
    var RAIL = 12;     // kept clear at the edge of the screen
    var CLEAR = 10;    // kept clear between an image and the nearest pill
    var MIN_COL = 150; // below this there is no composition worth showing

    placePeek = function () {
      var vw = doc.documentElement.clientWidth;   // excludes the scrollbar
      if (vw < 1024 || !wm) {
        /* Below the wide breakpoint the images sit in the band above the name
           and the columns mean nothing. Hand the stylesheet back its own. */
        stage.removeAttribute('data-peek-room');
        peek.style.removeProperty('--peek-col');
        peek.style.left = peek.style.right = peek.style.width = '';
        return;
      }

      var m = wm.getBoundingClientRect();
      if (!m.width) return;                       // not laid out yet
      var inL = m.left, inR = m.right;
      Array.prototype.forEach.call(stage.querySelectorAll('.portal-slot'), function (s) {
        var r = s.getBoundingClientRect();
        if (!r.width) return;
        if (r.left < inL) inL = r.left;
        if (r.right > inR) inR = r.right;
      });

      var col = Math.min(inL - RAIL - CLEAR, (vw - RAIL) - inR - CLEAR);

      /* Widen the layer from the shell to the window, so a figure can be
         placed against the edge of the screen rather than the edge of the
         column of text. Measured off the canvas, not the layer: they share
         an edge, and a pass that found no room has already hidden the layer
         — a display:none box measures as zeroes, and the next pass would
         place everything against a left edge of nothing. */
      var pr = canvas.getBoundingClientRect();
      peek.style.left = (-pr.left).toFixed(1) + 'px';
      peek.style.right = 'auto';
      peek.style.width = vw + 'px';
      peek.style.setProperty('--peek-col', Math.max(0, col).toFixed(1) + 'px');
      stage.setAttribute('data-peek-room', col >= MIN_COL ? 'yes' : 'no');
    };
    placePeek();

    /* A very little parallax — a few pixels at the edge of the canvas, and
       a different amount per image, which is enough to say "these are at
       different depths" and not enough to make the page feel unsteady. The
       numbers are written once a frame; the stylesheet does the rest. */
    var driftFrame = 0;
    var drift = null;

    function applyDrift() {
      driftFrame = 0;
      if (!drift || !stage.hasAttribute('data-peek')) return;
      peek.style.setProperty('--px', drift[0].toFixed(3));
      peek.style.setProperty('--py', drift[1].toFixed(3));
    }

    if (canvas) {
      canvas.addEventListener('pointermove', function (e) {
        if (e.pointerType !== 'mouse') return;
        if (noMotion() || !stage.hasAttribute('data-peek')) return;
        var r = canvas.getBoundingClientRect();
        if (!r.width || !r.height) return;
        drift = [ (e.clientX - r.left) / r.width * 2 - 1,
                  (e.clientY - r.top) / r.height * 2 - 1 ];
        if (!driftFrame) driftFrame = win.requestAnimationFrame(applyDrift);
      });
    }

    /* Leaving the page with a group open would otherwise bring it back on the
       way in from the back button. */
    win.addEventListener('pagehide', hide);
    doc.addEventListener('visibilitychange', function () {
      if (doc.hidden) hide();
    });
  }


  /* =========================================================================
     8 · THE ARC
     Seven milestones on a ruler of years. Where each one sits is declared in
     the markup as a percentage of the 2010–2026 span, and every state it can
     be in is a selector — hover and focus are stage.css's, start to finish.

     What is left for this file is the part a stylesheet cannot hold: which
     milestone stays open after the pointer has gone.

     One tab stop, not seven. The selected milestone is the one in the tab
     order and the arrow keys walk the row from there, which is how a row of
     related controls is expected to behave — and it keeps six stops out of
     the way of a visitor who is only passing through on their way to a link.
     ====================================================================== */
  var arc = doc.querySelector('.arc');
  if (arc) {
    var arcBtns = Array.prototype.slice.call(arc.querySelectorAll('.arc__btn'));
    var arcScroll = arc.querySelector('.arc__scroll');

    function arcSelect(i, move) {
      arcBtns.forEach(function (btn, n) {
        var on = n === i;
        btn.setAttribute('aria-pressed', on ? 'true' : 'false');
        btn.tabIndex = on ? 0 : -1;
      });
      if (move) arcBtns[i].focus();
    }

    arcBtns.forEach(function (btn, i) {
      // A press selects. None of the seven has anywhere to go — inventing a
      // destination for a date is how a timeline becomes a résumé — so being
      // read is the whole of what happens.
      btn.addEventListener('click', function () { arcSelect(i); });

      btn.addEventListener('keydown', function (e) {
        var step = 0;
        if (e.key === 'ArrowRight' || e.key === 'ArrowDown') step = 1;
        else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') step = -1;
        else if (e.key === 'Home') { e.preventDefault(); arcSelect(0, true); return; }
        else if (e.key === 'End') { e.preventDefault(); arcSelect(arcBtns.length - 1, true); return; }
        if (!step) return;
        e.preventDefault();
        arcSelect((i + step + arcBtns.length) % arcBtns.length, true);
      });
    });

    /* A narrow window cannot hold sixteen years at a readable size, so the
       rail is wider than the screen and scrolls inside its own strip. It
       opens at the right-hand end, on the milestone that is already
       selected: 2026 is where the story is, and the years scrub backwards
       from it. Set without smooth behaviour — this is the first frame, not
       a journey.

       Whether that is happening is written onto the scroller, because the
       stylesheet cannot ask. It is what the fade at each end hangs off: a
       label cut by a hard edge reads as a bug, and the same fade over a
       rail that fits would dim 2010 for no reason. */
    var arcFit = 0;
    function arcMeasure() {
      arcFit = 0;
      if (!arcScroll) return;
      var over = arcScroll.scrollWidth > arcScroll.clientWidth + 1;
      arcScroll.setAttribute('data-scroll', over ? 'yes' : 'no');
    }
    if (arcScroll) {
      arcMeasure();
      if (arcScroll.getAttribute('data-scroll') === 'yes') {
        arcScroll.scrollLeft = arcScroll.scrollWidth;
      }
      win.addEventListener('resize', function () {
        if (arcFit) return;
        arcFit = win.requestAnimationFrame(arcMeasure);
      });
    }
  }


})(window, document);
