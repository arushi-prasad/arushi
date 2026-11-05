/* ===========================================================================
   MESH — the hero's grid, made to answer a pointer.

   The page grid is two CSS background-images on body::before and ::after:
   hairlines on a 44px cell, or dots on the same cell, at --grid-deco, fixed
   to the viewport. A background-image cannot bend, and a grid of elements
   would be nine hundred divs. So this is one canvas, the width of the window
   and the height of the hero, sitting under everything in the stage and over
   the page grid — and it paints nothing at all until a pointer arrives.

   What it does, in a window about 200px across, is lift the straight lines
   out and put bent ones back:

     1 · stroke the straight lines in the page colour — the grid, locally,
         is gone
     2 · lay down the light
     3 · stroke the same lines again, displaced, in the grid's own colour at
         the grid's own opacity
     4 · stroke them a third time through a radial gradient, so the ones
         nearest the pointer carry a little more light than the rest
     5 · put a lit disc on every crossing in the window, through the same
         kind of gradient, because the crossings are where the eye goes
     6 · and switch a few of them on and off again, one at a time, as the
         hand moves — each on its own clock, so the ones the pointer has
         already left finish fading by themselves

   The window's edge is the thing that makes this invisible: displacement
   falls to exactly zero there, so step 3 puts the line back precisely where
   step 1 took it from. There is no disc, no mask and no seam — outside the
   window the canvas is empty and the real grid shows through it.

   Step 6 is the only part that outlives the window: a spark is a grid
   index and a clock, not a mark on a trail layer, so the afterglow is just
   the tail of an envelope and the canvas is provably empty about a second
   after the last movement.

   Everything it reads — cell, hairline, colour, opacity, which of the two
   layers is up — is read off the live computed styles, so the Grid, Colour
   and Opacity controls go on owning the grid exactly as they did.
   ========================================================================= */
(function (win, doc) {
  'use strict';

  var stage = doc.querySelector('.stage');
  if (!stage || !win.requestAnimationFrame || typeof win.Path2D !== 'function') return;

  /* ---- The shape of the gesture ----------------------------------------
     R is how far the hand reaches; AMP is how far the furthest intersection
     travels, in pixels, which is the whole brief: a few. SOFT keeps the
     points directly under the pointer from being pulled onto it — without
     it the field has a singularity there and the mesh pinches. */
  var R = 185;          /* reach of the displacement, px                   */
  var AMP = 13;         /* the most any intersection moves, px             */
  var SOFT = 20;        /* near-field taper, px                            */
  var PAD = 26;         /* how far past R the lines are drawn              */
  var SEG = 5;          /* samples per cell along each line                */

  /* Steps 2 and 4 through 6 all add ivory with 'lighter', so they are not
     four independent decisions — they are one budget, and the ceiling is the
     only hard rule in this file. The page colour is #14130F, so red 20; the
     name above it is --ink-100, red 251. A background detail may not go
     anywhere near that, and a channel that reaches 255 has clamped, which is
     a white point rather than a lit one and reads as glitter however briefly
     it is on screen. Added up on the worst pixel there is — a spark at its
     peak, on a crossing, on a lit line, at the centre of the glow — these
     come to about 225, and they are chosen in that order:

         ground lifted by the glow         20 ->  31
         + the line light, on a line       31 ->  59   (ambient line: 31)
         + the crossing, core and halo     59 -> 120
         + a spark at the top of its arc  120 -> 225

     So the window reads as three steps of contrast rather than one wash:
     a lit line is twice its ambient self, a crossing is twice that again,
     and a spark is twice that again for about a second. Nothing clamps,
     nothing is within fifty levels of the wordmark, and the diffused light
     stays small enough that the erase in step 1 cannot be seen doing its
     job. */
  var GLOW_R = 300;     /* the diffused light, px                          */
  var GLOW_A = 0.045;   /* ...at this much ivory, at full strength         */
  var BRIGHT_A = 0.110; /* the light carried along the lines themselves    */

  /* The crossings. Two discs on the same point: a core small enough to stay
     a point at any zoom, and a halo wide enough that it has no edge. */
  var NODE_A = 0.190;   /* the core, at full strength                      */
  var NODE_HALO = 0.052;/* ...and the ring around it                       */
  var NODE_R = 1.5;     /* core radius, px                                 */
  var NODE_H = 3.4;     /* halo radius, px                                 */

  /* The points of light. SPARK_MAX and the two rates together are the whole
     of "elegant, not glittery": about one new point per 54px of travel and
     one per 420ms while the hand is moving, which at a walking pace is two
     or three a second, and never more than twelve alight at once. Each is
     drawn from a ring well inside the reach — never under the cursor, never
     out at the edge where the window is already fading. */
  var SPARK_MAX = 12;   /* alight at once                                  */
  var SPARK_LIFE = 620; /* ms, at the shortest                             */
  var SPARK_VARY = 340; /* ...and up to this much longer                   */
  var SPARK_ATK = 0.26; /* share of a life spent switching on              */
  /* On top of the crossing rather than instead of it. Replacing it would be
     the truer picture — one light, not two — but a spark dimmer than the
     node it stood in for would punch a hole in the grid on the way down and
     pop back when it died. Adding cannot do that: the crossing is a floor
     the spark rises from and settles back onto. */
  var SPARK_CORE = 0.330;/* the lit point                                  */
  var SPARK_HALO = 0.100;/* ...and the glow it sits in                     */
  var SPARK_C = 1.7;    /* core radius, px                                 */
  var SPARK_R = 7;      /* halo radius, px                                 */
  var SPARK_IN = 0.16;  /* the ring they are drawn from, as a share of R   */
  var SPARK_OUT = 0.62;
  var SPARK_PX = 54;    /* one point of light per this much travel, px     */
  var SPARK_MS = 420;   /* ...and one per this long, ms                    */
  var SPARK_GATE = 0.22;/* under this amplitude nothing new is lit         */

  var IDLE = 700;       /* a pointer that has not moved for this long has
                           stopped, and the mesh relaxes under it          */
  var EASE_P = 0.20;    /* how hard the mesh chases the pointer            */
  var EASE_IN = 0.14;   /* how fast it swells — fast enough that the first
                           flick of the mouse is answered inside a quarter
                           second, slow enough to still be a swell          */
  var EASE_OUT = 0.12;  /* ...and how fast it lets go, which is quicker:
                           arriving should be felt, leaving should not be
                           waited for                                      */
  var STOP = 0.01;      /* below this the mesh is home, and the canvas is
                           cleared rather than left holding a copy of the
                           grid nobody can tell from the real one          */

  var TAU = Math.PI * 2;

  var fineMQ = win.matchMedia ? win.matchMedia('(hover: hover) and (pointer: fine)') : null;
  var motionMQ = win.matchMedia ? win.matchMedia('(prefers-reduced-motion: reduce)') : null;

  /* Asked on every move rather than once at load, so an OS setting changed
     in another window takes effect here without a reload — and so a machine
     with both a trackpad and a touchscreen is judged by the pointer that is
     actually being used. */
  function allowed(e) {
    if (motionMQ && motionMQ.matches) return false;
    if (fineMQ && !fineMQ.matches) return false;
    return !e || !e.pointerType || e.pointerType === 'mouse' || e.pointerType === 'pen';
  }

  var cv = null, ctx = null, probe = null;
  var dpr = 1, cw = 0, ch = 0;

  /* The pointer as reported, and the pointer the mesh believes in — which
     lags it, which is what gives the thing weight. */
  var rawX = 0, rawY = 0, rawAt = 0, seen = false;
  var sx = 0, sy = 0, amp = 0;
  var raf = 0, last = 0, paint = null, paintAt = 0;
  /* The sparks alight, and the fraction of the next one earned so far. */
  var live = [], owed = 0;

  /* ---- Reading the grid off the page ------------------------------------
     --grid-deco is a calc() on an unregistered custom property, so it comes
     back as the unevaluated expression. The opacity of the two pseudo
     elements is the same number already resolved — and it carries the Grid
     control's crossfade and the Opacity control with it, for free. */
  function colour(value) {
    probe.fillStyle = '#000';
    probe.fillStyle = value.trim();
    var hex = probe.fillStyle;
    if (hex.charAt(0) !== '#' || hex.length !== 7) return [0, 0, 0];
    return [parseInt(hex.substr(1, 2), 16),
            parseInt(hex.substr(3, 2), 16),
            parseInt(hex.substr(5, 2), 16)];
  }

  function rgba(c, a) {
    return 'rgba(' + c[0] + ',' + c[1] + ',' + c[2] + ',' + a + ')';
  }

  function mix(a, b, t) {
    return [Math.round(a[0] + (b[0] - a[0]) * t),
            Math.round(a[1] + (b[1] - a[1]) * t),
            Math.round(a[2] + (b[2] - a[2]) * t)];
  }

  function readPaint() {
    var root = win.getComputedStyle(doc.documentElement);
    var before = win.getComputedStyle(doc.body, '::before');
    var after = win.getComputedStyle(doc.body, '::after');
    var v = function (n) { return root.getPropertyValue(n); };
    var ivory = colour(v('--ink-100') || '#FBF7EF');
    return {
      cell: parseFloat(v('--grid-cell')) || 44,
      hair: parseFloat(v('--hair')) || 1,
      page: colour(v('--surface-page') || '#14130F'),
      ivory: ivory,
      line: colour(v('--border-default') || '#2B2822'),
      dot: colour(v('--border-strong') || '#7E776C'),
      /* The points of light: warm ivory leaned a little toward
         --hue-ochre-light, which lands around #F2E7C9 — candlelight on the
         charcoal rather than a colour accent. Taken from the hue ring so it
         is a token rather than a literal, but deliberately not from
         --accent: the Colour control re-orders the wordmark and the links,
         and it has no business turning the background gold. The same
         reasoning --hue-signal is outside the palettes for. */
      spark: mix(ivory, colour(v('--hue-ochre-light') || '#E8D49A'), 0.45),
      lineA: parseFloat(before.opacity) || 0,
      dotA: parseFloat(after.opacity) || 0
    };
  }

  /* ---- The field --------------------------------------------------------
     A pull toward the pointer. (1 - t²)² is one at the centre and reaches
     zero at R with zero slope, so the mesh arrives at the untouched grid
     smoothly rather than at an edge; d/(d+SOFT) takes it back to nothing in
     the last few pixels, so nothing is ever dragged onto the cursor. */
  /* The pull at distance d, as a multiplier on the vector from the point to
     the pointer. Zero at and beyond R, and zero at d = 0, so the one
     expression covers the lines, the dots, the crossings and the sparks and
     they cannot drift apart. */
  function pull(d, k) {
    if (d >= R || d <= 0.001) return 0;
    var t = d / R, f = 1 - t * t;
    return k * f * f * (d / (d + SOFT)) / d;
  }

  function run(path, x0, y0, x1, y1, step, px, py, k) {
    var dx = x1 - x0, dy = y1 - y0;
    var n = Math.max(2, Math.round(Math.sqrt(dx * dx + dy * dy) / step));
    var ux = dx / n, uy = dy / n;
    for (var i = 0; i <= n; i++) {
      var x = x0 + ux * i, y = y0 + uy * i;
      var ax = px - x, ay = py - y;
      var m = pull(Math.sqrt(ax * ax + ay * ay), k);
      x += ax * m; y += ay * m;
      if (i === 0) path.moveTo(x, y); else path.lineTo(x, y);
    }
  }

  /* Both paths over the same spans: the lines as the page drew them, and the
     lines as the pointer leaves them. */
  function lines(lx, ly, rect, p, k) {
    var flat = new win.Path2D(), bent = new win.Path2D();
    var W = R + PAD, cell = p.cell, half = p.hair / 2;
    var step = cell / SEG;
    var vx = lx + rect.left, vy = ly + rect.top;
    var i, c;

    for (i = Math.ceil((vx - W) / cell); i <= Math.floor((vx + W) / cell); i++) {
      c = i * cell - rect.left + half;
      flat.moveTo(c, ly - W); flat.lineTo(c, ly + W);
      run(bent, c, ly - W, c, ly + W, step, lx, ly, k);
    }
    for (i = Math.ceil((vy - W) / cell); i <= Math.floor((vy + W) / cell); i++) {
      c = i * cell - rect.top + half;
      flat.moveTo(lx - W, c); flat.lineTo(lx + W, c);
      run(bent, lx - W, c, lx + W, c, step, lx, ly, k);
    }
    return { flat: flat, bent: bent };
  }

  /* The dots sit at the centre of each cell, which is where a radial-gradient
     with no position puts them. */
  function dots(lx, ly, rect, p, k) {
    var flat = new win.Path2D(), bent = new win.Path2D();
    var W = R + PAD, cell = p.cell, r = p.hair * 1.1;
    var i, j, x, y, ax, ay, m, nx, ny;

    for (i = Math.ceil((lx + rect.left - W) / cell - 0.5);
         i <= Math.floor((lx + rect.left + W) / cell - 0.5); i++) {
      for (j = Math.ceil((ly + rect.top - W) / cell - 0.5);
           j <= Math.floor((ly + rect.top + W) / cell - 0.5); j++) {
        x = (i + 0.5) * cell - rect.left;
        y = (j + 0.5) * cell - rect.top;
        flat.moveTo(x + r + 1, y); flat.arc(x, y, r + 1, 0, TAU);
        ax = lx - x; ay = ly - y;
        m = pull(Math.sqrt(ax * ax + ay * ay), k);
        nx = x + ax * m; ny = y + ay * m;
        bent.moveTo(nx + r, ny); bent.arc(nx, ny, r, 0, TAU);
      }
    }
    return { flat: flat, bent: bent };
  }

  /* ---- The crossings ----------------------------------------------------
     Where the lines cross — or, under the dots layer, where the dots sit.
     One pass builds two paths over the same points, a core and a halo, and
     both are filled through a radial gradient centred on the pointer: the
     disc is the same everywhere and the gradient decides how much of it is
     lit, so the whole set falls off with the window for the price of two
     fills rather than two per crossing.

     R, not R + PAD: past the reach the gradient is at zero and the fill
     would be free of ink anyway. */
  /* Which lattice the crossings are on: the dots sit at the centre of a
     cell and the line crossings on its corner, so during the Grid control's
     crossfade this has to be one answer for both the nodes and the sparks or
     they land half a cell apart for a frame. */
  function centred(p) { return p.dotA > p.lineA; }

  function nodes(lx, ly, rect, p, k, mid) {
    var core = new win.Path2D(), halo = new win.Path2D();
    var cell = p.cell, o = mid ? 0.5 : 0, h = mid ? 0 : p.hair / 2;
    var vx = lx + rect.left, vy = ly + rect.top;
    var i, j, x, y, ax, ay, m;

    for (i = Math.ceil((vx - R) / cell - o); i <= Math.floor((vx + R) / cell - o); i++) {
      for (j = Math.ceil((vy - R) / cell - o); j <= Math.floor((vy + R) / cell - o); j++) {
        x = (i + o) * cell + h - rect.left;
        y = (j + o) * cell + h - rect.top;
        ax = lx - x; ay = ly - y;
        m = pull(Math.sqrt(ax * ax + ay * ay), k);
        x += ax * m; y += ay * m;
        core.moveTo(x + NODE_R, y); core.arc(x, y, NODE_R, 0, TAU);
        halo.moveTo(x + NODE_H, y); halo.arc(x, y, NODE_H, 0, TAU);
      }
    }
    return { core: core, halo: halo };
  }

  /* ---- The points of light ----------------------------------------------
     A spark is a grid index and a clock. Not a position: it is resolved
     through pull() every frame like everything else, so it stays on its
     crossing while the pointer bends the grid under it. And not a mark on
     a trail layer: it is drawn additively over whatever the canvas already
     holds, which is why one lit on the way past can outlive the window
     that lit it and finish fading on the untouched grid.

     That tail is the whole of the afterglow. Nothing accumulates, nothing
     has to be cleaned up, and SPARK_LIFE + SPARK_VARY after the last
     movement the list is empty and the canvas is cleared. */
  function smooth(x) {
    if (x <= 0) return 0;
    if (x >= 1) return 1;
    return x * x * (3 - 2 * x);
  }

  /* Quick on, slower off, with zero slope at both ends — a point of light
     switching on, never a frame of white. */
  function envelope(u) {
    return u < SPARK_ATK ? smooth(u / SPARK_ATK) : smooth((1 - u) / (1 - SPARK_ATK));
  }

  function alight(i, j) {
    for (var n = 0; n < live.length; n++) {
      if (live[n].i === i && live[n].j === j) return true;
    }
    return false;
  }

  /* Somewhere in the ring between SPARK_IN and SPARK_OUT of the reach. The
     sqrt() spreads the draw evenly over the ring's area instead of crowding
     it against the inside edge, and rounding to an index is what puts the
     light on a crossing rather than between four of them. A crossing
     already alight is skipped rather than retried: the budget it came from
     is spent, which thins the set out exactly where it is densest. */
  function ignite(lx, ly, rect, p, mid) {
    var a = Math.random() * TAU;
    var r = R * (SPARK_IN + (SPARK_OUT - SPARK_IN) * Math.sqrt(Math.random()));
    var cell = p.cell, o = mid ? 0.5 : 0, h = mid ? 0 : p.hair / 2;
    var i = Math.round((lx + rect.left + Math.cos(a) * r - h) / cell - o);
    var j = Math.round((ly + rect.top + Math.sin(a) * r - h) / cell - o);
    if (alight(i, j)) return;
    live.push({
      i: i, j: j, mid: mid, t: 0,
      life: SPARK_LIFE + Math.random() * SPARK_VARY,
      /* Not every one as bright as the last, or the set reads as a pattern
         rather than as light. */
      gain: 0.68 + Math.random() * 0.32
    });
  }

  /* Age the list, then earn new ones. The gate is the amplitude and not the
     pointer: a window that is standing down — at the canvas edge, idle,
     under reduced motion, or let go of — lights nothing new, and whatever
     is already alight fades on its own clock instead of being cut off. */
  function sparks(dt, lx, ly, rect, p, moved, want) {
    var i = 0, n = 0;
    while (i < live.length) {
      live[i].t += dt;
      if (live[i].t >= live[i].life) live.splice(i, 1); else i++;
    }
    if (p.lineA <= 0.004 && p.dotA <= 0.004) { live.length = 0; return; }
    if (want <= 0 || amp < SPARK_GATE) return;

    owed += moved / SPARK_PX + dt / SPARK_MS;
    while (owed >= 1 && n < 2 && live.length < SPARK_MAX) {
      owed -= 1; n++;
      ignite(lx, ly, rect, p, centred(p));
    }
    /* A flick across the hero earns twenty of these. Capped, or the budget
       keeps paying out points of light after the hand has stopped. */
    if (owed > 2) owed = 2;
  }

  function shine(rect, p, k) {
    var i, sp, o, h, x, y, ax, ay, m, e, g;
    for (i = 0; i < live.length; i++) {
      sp = live[i];
      e = envelope(sp.t / sp.life) * sp.gain;
      if (e <= 0.003) continue;
      o = sp.mid ? 0.5 : 0; h = sp.mid ? 0 : p.hair / 2;
      x = (sp.i + o) * p.cell + h - rect.left;
      y = (sp.j + o) * p.cell + h - rect.top;
      ax = sx - x; ay = sy - y;
      m = pull(Math.sqrt(ax * ax + ay * ay), k);
      x += ax * m; y += ay * m;

      g = ctx.createRadialGradient(x, y, 0, x, y, SPARK_R);
      g.addColorStop(0, rgba(p.spark, e * SPARK_HALO));
      g.addColorStop(1, rgba(p.spark, 0));
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.arc(x, y, SPARK_R, 0, TAU); ctx.fill();

      ctx.fillStyle = rgba(p.spark, e * SPARK_CORE);
      ctx.beginPath(); ctx.arc(x, y, SPARK_C, 0, TAU); ctx.fill();
    }
  }

  /* ---- The canvas -------------------------------------------------------
     Full-bleed across the window and exactly as tall as the hero: the grid
     it is standing in for runs the whole width of the page, and .stage is
     a .shell, which does not. */
  function build() {
    cv = doc.createElement('canvas');
    cv.className = 'stage__mesh';
    cv.setAttribute('aria-hidden', 'true');
    stage.insertBefore(cv, stage.firstChild);
    ctx = cv.getContext('2d');
    probe = doc.createElement('canvas').getContext('2d');
    paint = readPaint();

    if (win.ResizeObserver) new win.ResizeObserver(function () { cw = 0; }).observe(stage);
    win.addEventListener('resize', function () { cw = 0; });
    if (win.APTokens && win.APTokens.subscribe) {
      win.APTokens.subscribe(function () { paintAt = 0; });
    }
  }

  function size(rect) {
    var d = Math.min(2, win.devicePixelRatio || 1);
    var w = Math.max(1, Math.round(rect.width)), h = Math.max(1, Math.round(rect.height));
    if (w === cw && h === ch && d === dpr) return;
    cw = w; ch = h; dpr = d;
    cv.width = Math.round(w * d); cv.height = Math.round(h * d);
  }

  /* The light would cut off at a straight line if the pointer reached the
     canvas's own edge, so the whole effect stands down as it gets there. */
  function edge(lx, ly, rect) {
    var m = Math.min(lx, ly, rect.width - lx, rect.height - ly);
    var t = m / (R * 0.75);
    if (t <= 0) return 0;
    if (t >= 1) return 1;
    return t * t * (3 - 2 * t);
  }

  function draw(rect) {
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, cw, ch);
    if (!paint) return;

    var p = paint, k = AMP * amp;
    var L = p.lineA > 0.004, D = p.dotA > 0.004;
    if (!L && !D) return;            /* the Grid control is off: so is this */
    /* Nothing bent and nothing alight: the clear above is the whole frame.
       Checked after the Grid control — which has already dropped the list,
       so there is no chance of a handful left burning on nothing. */
    if (amp <= 0 && !live.length) return;

    if (amp > 0) drawWindow(rect, p, k, L, D);

    /* 6 · the points of light, additive and each on its own clock. Outside
           the block above on purpose: this is what runs on after the window
           has moved off them or closed altogether, and it is the only step
           that paints when amp is zero. */
    if (live.length) {
      ctx.globalCompositeOperation = 'lighter';
      shine(rect, p, k);
      ctx.globalCompositeOperation = 'source-over';
    }
  }

  function drawWindow(rect, p, k, L, D) {
    var pl = L ? lines(sx, sy, rect, p, k) : null;
    var pd = D ? dots(sx, sy, rect, p, k) : null;

    /* 1 · lift the straight grid out of the window. A shade wider than the
           hairline, so none of its edge is left behind. */
    ctx.strokeStyle = rgba(p.page, 1);
    ctx.fillStyle = ctx.strokeStyle;
    ctx.lineWidth = p.hair + 1.2;
    ctx.lineCap = 'butt';
    if (pl) ctx.stroke(pl.flat);
    if (pd) ctx.fill(pd.flat);

    /* 2 · the light, under the grid the way light behind a thing is. It is
           also what keeps step 1 from reading as dark hairlines: the lines
           that were lifted out are lit exactly like the ground beside them. */
    var g = ctx.createRadialGradient(sx, sy, 0, sx, sy, GLOW_R);
    g.addColorStop(0, rgba(p.ivory, GLOW_A * amp));
    g.addColorStop(0.5, rgba(p.ivory, GLOW_A * amp * 0.3));
    g.addColorStop(1, rgba(p.ivory, 0));
    ctx.fillStyle = g;
    ctx.fillRect(sx - GLOW_R, sy - GLOW_R, GLOW_R * 2, GLOW_R * 2);

    /* 3 · the grid back in, bent — its own colour, its own opacity, its own
           hairline. Beyond R nothing has moved, so this lands on top of the
           erasure and the window has no edge to see. */
    ctx.lineWidth = p.hair;
    if (pl) { ctx.strokeStyle = rgba(p.line, p.lineA); ctx.stroke(pl.bent); }
    if (pd) { ctx.fillStyle = rgba(p.dot, p.dotA); ctx.fill(pd.bent); }

    /* 4 · and a little of that light along the lines themselves. A gradient
           as the stroke, so the falloff costs one more stroke rather than a
           stroke per segment. */
    var b = ctx.createRadialGradient(sx, sy, 0, sx, sy, R * 1.15);
    b.addColorStop(0, rgba(p.ivory, BRIGHT_A * amp));
    b.addColorStop(1, rgba(p.ivory, 0));
    ctx.globalCompositeOperation = 'lighter';
    if (pl) { ctx.strokeStyle = b; ctx.stroke(pl.bent); }
    if (pd) { ctx.fillStyle = b; ctx.fill(pd.bent); }

    /* 5 · the crossings, which is where the eye reads a grid. This is the
           step that makes the window findable without a brighter wash: a
           lit point on an already-lit line is contrast, and contrast is
           cheaper to see than luminance. Through the two gradients, so it
           is two fills for the lot of them. */
    var nd = nodes(sx, sy, rect, p, k, centred(p));
    var nh = ctx.createRadialGradient(sx, sy, 0, sx, sy, R);
    nh.addColorStop(0, rgba(p.ivory, NODE_HALO * amp));
    nh.addColorStop(1, rgba(p.ivory, 0));
    ctx.fillStyle = nh; ctx.fill(nd.halo);

    var nc = ctx.createRadialGradient(sx, sy, 0, sx, sy, R);
    nc.addColorStop(0, rgba(p.ivory, NODE_A * amp));
    nc.addColorStop(0.55, rgba(p.ivory, NODE_A * amp * 0.45));
    nc.addColorStop(1, rgba(p.ivory, 0));
    ctx.fillStyle = nc; ctx.fill(nd.core);

    ctx.globalCompositeOperation = 'source-over';
  }

  function frame(now) {
    raf = 0;
    var dt = Math.min(64, last ? now - last : 16) || 16;
    last = now;

    var rect = cv.getBoundingClientRect();
    size(rect);

    var lx = rawX - rect.left, ly = rawY - rect.top;
    var wasX = sx, wasY = sy, cold = amp === 0;
    /* Tested here rather than in the listener, so scrolling the hero out
       from under a motionless pointer lets go of it too. */
    var over = seen && lx >= 0 && ly >= 0 && lx <= rect.width && ly <= rect.height;
    var want = (over && now - rawAt < IDLE && allowed(null)) ? edge(lx, ly, rect) : 0;

    var kp = 1 - Math.pow(1 - EASE_P, dt / 16.667);
    var ka = 1 - Math.pow(1 - (want > amp ? EASE_IN : EASE_OUT), dt / 16.667);
    /* Arriving from cold, the mesh starts where the pointer is. Lerping from
       wherever it was last would drag a wave across the hero to meet it.
       amp is only ever exactly zero at a full stop, so this cannot fire in
       the middle of a release. */
    if (amp === 0 && want > 0) { sx = lx; sy = ly; }
    else { sx += (lx - sx) * kp; sy += (ly - sy) * kp; }
    amp += (want - amp) * ka;
    /* Home. Snapped before the draw below, not after it: step 1 of the draw
       strokes the page colour over the real grid at full opacity whatever
       the amplitude is, so a last frame at amp=0.004 would leave the canvas
       holding a pixel copy of the grid for as long as the pointer stayed
       away. At exactly zero the draw paints nothing but the sparks, which
       are additive and sit on the real grid. */
    if (want === 0 && amp < STOP) amp = 0;

    if (now - paintAt > 180) { paint = readPaint(); paintAt = now; }

    /* Driven by the distance the mesh's own pointer covered rather than the
       raw one: the lag is already a smoothing, so the rate inherits it and a
       flicked mouse lights a few points instead of a line of them. The frame
       the mesh arrives on is skipped — sx was snapped across the hero on it,
       and that is not travel. */
    sparks(dt, sx, sy, rect, paint,
           cold ? 0 : Math.sqrt((sx - wasX) * (sx - wasX) + (sy - wasY) * (sy - wasY)),
           want);

    draw(rect);

    if (amp > 0 || want > 0 || live.length) {
      raf = win.requestAnimationFrame(frame);
    } else {
      /* Settled. The pass above cleared the canvas, so there is nothing on
         screen and nothing running until a pointer comes back. */
      last = 0;
    }
  }

  function wake() {
    if (!raf) raf = win.requestAnimationFrame(frame);
  }

  win.addEventListener('pointermove', function (e) {
    if (!allowed(e)) return;
    rawX = e.clientX; rawY = e.clientY; rawAt = win.performance ? win.performance.now() : Date.now();
    seen = true;
    if (!cv) {
      /* Nothing is built on a touch screen, or under reduced motion, or
         before the first mouse has moved. */
      build();
      sx = rawX - cv.getBoundingClientRect().left;
      sy = rawY - cv.getBoundingClientRect().top;
    }
    wake();
  }, { passive: true });

  /* The pointer leaving the window stops reporting, so say so rather than
     waiting out the idle timer. */
  function drop() { seen = false; if (cv) wake(); }
  doc.documentElement.addEventListener('pointerleave', drop);
  win.addEventListener('blur', drop);

})(window, document);
