/* ===========================================================================
   TOKENS — one piece of shared state for the whole site.

   The five homepage controls do not each do their own thing. They all write
   into this store, the store writes to the document element once, and CSS
   does the rest. That is the entire mechanism, and it is why a control added
   later cannot drift from the others.

   PERSISTENCE
   Preferences are stored in localStorage and therefore survive a reload and
   a return visit. The reasoning: these controls are a demonstration of a
   token system, and a token system that forgets its values on every page
   navigation would demonstrate the opposite. A visible Reset returns every
   value to its default in one action. If localStorage is unavailable — a
   hardened browser, private mode in some engines — the store falls back to
   memory for the session and nothing else changes.

   Loaded without `defer`, before first paint, so a stored preference is
   applied to <html> before the page renders and never flashes a default.
   ========================================================================= */
(function (win, doc) {
  'use strict';

  // v2: the default palette changed from copper to mono. Anyone who had
  // already visited carried a stored 'copper' and would have kept seeing
  // the old default forever, so the key is bumped to retire those entries.
  var KEY = 'arushi.tokens.v2';

  var DEFAULTS = {
    palette: 'mono',
    type:    'editorial',
    density: 'comfortable',
    radius:  'subtle',
    grid:    'classic',
    opacity: 0.6,
    scale:   1
  };

  /* The allowed values. Anything not in here is rejected on read and on
     write, so a hand-edited localStorage entry cannot put the UI into a
     state the CSS has no rule for. */
  var OPTIONS = {
    palette: [
      { id: 'mono',      label: 'Mono',           note: 'Default. No hue — the neutral ramp only.' },
      { id: 'copper',    label: 'Warm Copper',    note: 'The whole ramp swung to amber.' },
      { id: 'botanical', label: 'Botanical Green',note: 'The whole ramp swung to deep green.' }
    ],
    type: [
      { id: 'editorial', label: 'Editorial Sans', note: 'Inter Tight, tight tracking, display weight.' },
      { id: 'serif',     label: 'Elegant Serif',  note: 'An old-style serif, opened up.' },
      { id: 'mono',      label: 'Monospaced',     note: 'Geist Mono headings over a sans body.' }
    ],
    density: [
      { id: 'compact',     label: 'Compact',     note: 'Every spacing step at 0.72×.' },
      { id: 'comfortable', label: 'Comfortable', note: 'Default. Every spacing step at 1×.' }
    ],
    radius: [
      { id: 'sharp',   label: 'Sharp',   note: 'Squared off. 0px.' },
      { id: 'subtle',  label: 'Subtle',  note: 'Default. 6px at the middle step.' },
      { id: 'rounded', label: 'Rounded', note: '16px at the middle step.' }
    ],
    grid: [
      { id: 'classic', label: 'Classic', note: 'Default. Hairline squares behind everything.' },
      { id: 'dots',    label: 'Dots',    note: 'The same spacing, marked at the corners only.' },
      { id: 'off',     label: 'Off',     note: 'No grid. The page colour is untouched.' }
    ]
  };

  var OPACITY_MIN = 0.15;
  var OPACITY_MAX = 1;
  var SCALE_MIN = 0.6;
  var SCALE_MAX = 1.4;

  var listeners = [];
  var memoryOnly = false;
  var state;

  function clamp(n, lo, hi) { return Math.min(hi, Math.max(lo, n)); }

  function isValid(group, value) {
    var list = OPTIONS[group];
    if (!list) return false;
    for (var i = 0; i < list.length; i++) if (list[i].id === value) return true;
    return false;
  }

  function sanitise(raw) {
    var out = {
      palette: DEFAULTS.palette,
      type:    DEFAULTS.type,
      density: DEFAULTS.density,
      radius:  DEFAULTS.radius,
      grid:    DEFAULTS.grid,
      opacity: DEFAULTS.opacity,
      scale:   DEFAULTS.scale
    };
    if (!raw || typeof raw !== 'object') return out;
    ['palette', 'type', 'density', 'radius', 'grid'].forEach(function (k) {
      if (isValid(k, raw[k])) out[k] = raw[k];
    });
    if (typeof raw.opacity === 'number' && isFinite(raw.opacity)) {
      out.opacity = clamp(raw.opacity, OPACITY_MIN, OPACITY_MAX);
    }
    if (typeof raw.scale === 'number' && isFinite(raw.scale)) {
      out.scale = clamp(raw.scale, SCALE_MIN, SCALE_MAX);
    }
    return out;
  }

  function read() {
    try {
      var s = win.localStorage.getItem(KEY);
      return sanitise(s ? JSON.parse(s) : null);
    } catch (e) {
      memoryOnly = true;
      return sanitise(null);
    }
  }

  function write() {
    if (memoryOnly) return;
    try {
      win.localStorage.setItem(KEY, JSON.stringify(state));
    } catch (e) {
      memoryOnly = true;
    }
  }

  function apply() {
    var el = doc.documentElement;
    el.setAttribute('data-palette', state.palette);
    el.setAttribute('data-type', state.type);
    el.setAttribute('data-density', state.density);
    el.setAttribute('data-radius', state.radius);
    el.setAttribute('data-grid', state.grid);
    el.style.setProperty('--deco-opacity', String(state.opacity));
    el.style.setProperty('--type-scale', String(state.scale));
  }

  function emit(changedKey) {
    for (var i = 0; i < listeners.length; i++) {
      try { listeners[i](get(), changedKey); } catch (e) { /* a bad listener must not stop the others */ }
    }
  }

  function get() {
    return {
      palette: state.palette, type: state.type, density: state.density,
      radius: state.radius, grid: state.grid,
      opacity: state.opacity, scale: state.scale
    };
  }

  function set(key, value, opts) {
    if (!(key in DEFAULTS)) return false;
    if (key === 'opacity' || key === 'scale') {
      var n = Number(value);
      if (!isFinite(n)) return false;
      value = key === 'opacity'
        ? clamp(n, OPACITY_MIN, OPACITY_MAX)
        : clamp(n, SCALE_MIN, SCALE_MAX);
    } else if (!isValid(key, value)) {
      return false;
    }
    if (state[key] === value) return false;
    state[key] = value;
    apply();
    if (!(opts && opts.transient)) write();
    emit(key);
    return true;
  }

  function reset() {
    state = sanitise(null);
    apply();
    if (!memoryOnly) {
      try { win.localStorage.removeItem(KEY); } catch (e) { /* nothing to undo */ }
    }
    emit('reset');
  }

  function isDefault() {
    return state.palette === DEFAULTS.palette &&
           state.type    === DEFAULTS.type &&
           state.density === DEFAULTS.density &&
           state.radius  === DEFAULTS.radius &&
           state.grid    === DEFAULTS.grid &&
           Math.abs(state.opacity - DEFAULTS.opacity) < 0.001 &&
           Math.abs(state.scale   - DEFAULTS.scale)   < 0.001;
  }

  function subscribe(fn) {
    if (typeof fn !== 'function') return function () {};
    listeners.push(fn);
    return function () {
      var i = listeners.indexOf(fn);
      if (i > -1) listeners.splice(i, 1);
    };
  }

  state = read();
  apply();

  win.APTokens = {
    get: get,
    set: set,
    reset: reset,
    isDefault: isDefault,
    subscribe: subscribe,
    DEFAULTS: DEFAULTS,
    OPTIONS: OPTIONS,
    LIMITS: {
      opacity: [OPACITY_MIN, OPACITY_MAX],
      scale:   [SCALE_MIN, SCALE_MAX]
    },
    persists: function () { return !memoryOnly; }
  };
})(window, document);
