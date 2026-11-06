/* ---------------------------------------------------------------------------
   globe.js — the rotating photo sphere on the About page.

   Tiles are placed with a Fibonacci spiral, which is the cheap way to spread
   N points evenly over a sphere: latitude steps uniformly through the sine,
   longitude advances by the golden angle. A naive lat/lon grid bunches
   everything at the poles; this does not.

   The photographs are reused as many times as the sphere needs. Each tile
   gets its own width, a small roll and a radius jitter so a repeat does not
   read as a duplicate of the one above it.

   Per frame this writes two custom properties and nothing else: --spin on
   the stage, and --vis per tile. No layout is read or written in the loop.

   Dragging: pointer events, so mouse, touch and pen are one code path. Auto
   rotation stops on grab and eases back in on release.
   --------------------------------------------------------------------------- */
(function () {
  'use strict';

  var root = document.querySelector('[data-globe]');
  var stage = root && root.querySelector('[data-globe-stage]');
  if (!root || !stage) return;

  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)');

  var SRC = root.getAttribute('data-globe-src');
  var POOL = parseInt(root.getAttribute('data-globe-count'), 10) || 1;
  /* More tiles than photographs, on purpose: the brief asks for a filled
     sphere and accepts repeats. */
  var N = 46;
  var GOLDEN = Math.PI * (3 - Math.sqrt(5));

  var tiles = [];
  var frag = document.createDocumentFragment();

  for (var i = 0; i < N; i++) {
    /* y from +1 to -1, then the ring radius at that height. */
    var y = 1 - (i / (N - 1)) * 2;
    var lat = Math.asin(y) * 180 / Math.PI;
    var lon = (i * GOLDEN) * 180 / Math.PI;

    /* Deterministic jitter — same every load, so the composition is a
       decision rather than a lottery. */
    var j = Math.sin(i * 12.9898) * 43758.5453;
    j = j - Math.floor(j);

    var el = document.createElement('span');
    el.className = 'ab-globe__i';
    el.style.setProperty('--lon', lon.toFixed(2) + 'deg');
    el.style.setProperty('--lat', (-lat).toFixed(2) + 'deg');
    /* Radius against the frame: perspective magnifies the near face by
       about 1.25x, so a 240px radius drew a ~590px sphere inside a 608px
       box and clipped along the bottom. 196 leaves it room to turn. */
    el.style.setProperty('--r', (196 + j * 20).toFixed(0) + 'px');
    el.style.setProperty('--w', (4.2 + j * 2.6).toFixed(2) + 'rem');
    el.style.setProperty('--tiltz', ((j - 0.5) * 9).toFixed(1) + 'deg');

    var img = document.createElement('img');
    /* Walk the pool with a stride that is coprime with it, so neighbouring
       tiles are never the same photograph. */
    img.src = SRC + 'fun-' + String(((i * 7) % POOL) + 1).padStart(2, '0') + '.jpg';
    /* Not lazy. A tile on a sphere is moved by a 3D transform, and the
       viewport test a lazy image uses does not account for that — 30 of the
       64 never loaded at all. There are only 27 distinct files behind these
       64 tiles and they are already on disk from the Fun page, so the repeats
       come out of cache and eager costs almost nothing. */
    img.loading = 'eager';
    img.decoding = 'async';
    img.alt = '';
    img.setAttribute('aria-hidden', 'true');
    img.draggable = false;
    el.appendChild(img);

    frag.appendChild(el);
    tiles.push({ el: el, lon: lon, lat: lat });
  }
  stage.appendChild(frag);

  var spin = 0;            // degrees
  var speed = 0.055;       // degrees per millisecond-ish, scaled by dt
  var drag = null;         // { x, spin } while held
  var momentum = 0;
  var last = 0;

  /* Fade the far hemisphere. cos of the angle between the tile's outward
     normal and the viewer gives a clean front-to-back ramp. */
  function paint() {
    stage.style.setProperty('--spin', spin.toFixed(2) + 'deg');
    for (var i = 0; i < tiles.length; i++) {
      var t = tiles[i];
      var a = (t.lon + spin) * Math.PI / 180;
      var facing = Math.cos(a) * Math.cos(t.lat * Math.PI / 180);
      /* -1 (behind) .. 1 (front) -> 0.12 .. 1 */
      t.el.style.setProperty('--vis', (0.12 + (facing + 1) / 2 * 0.88).toFixed(3));
    }
  }

  function frame(now) {
    var dt = last ? Math.min(now - last, 64) : 16;
    last = now;
    if (!drag) {
      if (momentum) {
        spin += momentum * dt;
        momentum *= 0.94;
        if (Math.abs(momentum) < 0.004) momentum = 0;
      } else if (!reduced.matches) {
        spin += speed * dt * 0.06;
      }
      if (spin > 360) spin -= 360;
      if (spin < -360) spin += 360;
      paint();
    }
    requestAnimationFrame(frame);
  }

  root.addEventListener('pointerdown', function (e) {
    drag = { x: e.clientX, spin: spin };
    momentum = 0;
    root.setAttribute('data-dragging', 'yes');
    root.setPointerCapture(e.pointerId);
  });

  root.addEventListener('pointermove', function (e) {
    if (!drag) return;
    var dx = e.clientX - drag.x;
    var next = drag.spin + dx * 0.32;
    momentum = (next - spin) * 0.03;
    spin = next;
    paint();
  });

  function release(e) {
    if (!drag) return;
    drag = null;
    root.removeAttribute('data-dragging');
    try { root.releasePointerCapture(e.pointerId); } catch (err) {}
  }
  root.addEventListener('pointerup', release);
  root.addEventListener('pointercancel', release);

  paint();
  requestAnimationFrame(frame);
})();
