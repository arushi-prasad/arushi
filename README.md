# Arushi Prasad — Interactive Portfolio

An interaction-led portfolio built around a wordmark you can touch and a
design-token system you can edit. Static HTML, CSS and JavaScript. No
framework, no dependencies, no third-party requests — the same stack as the
rest of this repository.

Reference for the interaction model and information architecture:
[hipuku.dev](https://www.hipuku.dev). Everything here — content, identity,
palette, components and code — is original.

This site is **standalone**. It does not touch, import from, or link into
`00.Homepage/`. The only outbound links into the repository are the two real
case studies (see *Links out*, below).

---

## Run it

The site must be served over HTTP, from the **repository root**, because the
Work page links to the existing case studies that live outside this folder.

```bash
cd ~/Desktop/Portfolio
python3 -m http.server 8790
```

Then open:

```
http://127.0.0.1:8790/07.%20Interactive%20Portfolio/
```

Opening `index.html` straight off disk works for the pages themselves, but
`file://` will not resolve the two case-study links.

---

## Build

Every page is a body fragment in `_pages/`. `_build.py` wraps each one in the
shared shell — head, icon sprite, navigation, curtain, footer — and writes it
to its route directory.

```bash
cd "07. Interactive Portfolio"
python3 _build.py          # rebuilds all ten routes
```

The shell lives in exactly one place, so navigation and footer cannot drift
between pages. Edit `_pages/*.html`, not the generated `*/index.html`.

A fragment opens with a front-matter comment:

```html
<!--meta
route: work
title: Selected work
nav: work
word_a: selected
word_b: work
tagline: …
-->
```

| Key | Meaning |
|---|---|
| `route` | directory the page is written to; empty is the site root |
| `title` / `desc` | `<title>` and meta description |
| `nav` | which nav item gets `aria-current="page"` |
| `word_a` / `word_b` | the two words of the big page title |
| `tagline` | the line under the title |
| `hero_cards` | the three cards behind the title |
| `stage` / `lab` | load `stage.js` / `lab.js` and their stylesheets |

---

## Routes

| Route | What it is |
|---|---|
| `/` | The stage — wordmark, destinations, token toolbar |
| `/work` | Selected work. Two cards open real case studies |
| `/designops` | Five pillars, plus the AI design OS, labelled **Concept** |
| `/leadership` | Two to twenty, four positions, recognition |
| `/systems` | Capsule, the live token layer, AI-assisted tooling |
| `/fun` | Everest, the ride, the plant, curiosity |
| `/about` | Career journey, philosophy, contact |
| `/experiments` | Five working builds wired to the real tokens |
| `/writing` | A minimal index: Articles / Notes tabs over four labelled drafts |
| `/snippets` | Five interaction demonstrations |

The six in the main navigation are Work, DesignOps, Leadership, Systems, Fun
and About. Experiments, Writing and Snippets are reachable from the home page
and from the footer of every page — nothing lives behind only one door.

---

## The token system

```
assets/css/tokens.css     every value the site uses, defined once
assets/js/tokens.js       the shared store the five controls write into
```

The five home-page controls do not each do their own thing. They all write
into one store; the store writes to `<html>` once; CSS does the rest.

| Control | Writes | Reaches |
|---|---|---|
| Colour | `html[data-palette]` | accent, focus rings, card art, the letter hue ring |
| Type | `html[data-type]` + `--type-scale` | family, weight, tracking, leading; the wordmark's size |
| Spacing | `html[data-density]` | one multiplier behind every `--step-*` |
| Radius | `html[data-radius]` | one multiplier behind every `--radius-*` |
| Opacity | `--deco-opacity` | the canvas grid, card art, hairlines, asides |

Four palettes, three type treatments, two densities, three radius settings,
and opacity clamped between 15% and 100%. The neutral ramp never changes, so
text contrast is identical across every palette.

**Keyboard:** `1`–`5` open a tool, `0` restarts, `Escape` closes. Each option
row is a radiogroup, so the arrow keys move between options.

**The selection box.** Choosing Type draws a Figma-style box with eight
handles around the wordmark. Drag any handle to change the type scale, or
focus one and use the arrow keys; `Home` returns it to 1×. The wordmark is
scaled with `transform`, which is outside layout, so dragging it cannot move
anything else on the page.

### Persistence — the decision

Preferences are stored in `localStorage` and **persist across visits**, not
just the session.

The reasoning: these controls are a demonstration of design-system thinking,
and a token system that forgets its values the moment you navigate would
demonstrate the opposite. Persisting makes the point that the tokens are
shared infrastructure rather than five local widgets — change the palette on
`/experiments` and it is still there on `/about`.

Mitigations, because persistence without an exit is a trap:

- A visible **Restart** sits in the toolbar. It is never disabled: it puts
  every token back to its default *and* replays the stage from its first
  frame, and a replay is always available. It used to switch itself off
  whenever the tokens were clean — which is the state the page loads in, so
  it was dead on arrival and killed itself again after a single press.
- `0` restarts from anywhere on the home page.
- Every stored value is re-validated on read, so a hand-edited or stale
  entry cannot put the UI into a state the CSS has no rule for.
- If `localStorage` is unavailable, the store falls back to memory for the
  session and nothing else changes.
- The footer of every page says where the settings came from and how to
  clear them.

---

## The wordmark

Six letters of real, selectable, copyable text in an `<h1>` — not an image,
not SVG paths. Each letter is its own focusable target.

- Every letter rests in warm ivory. Hover, focus or tap gives it a hue drawn
  from the **active palette**, so the Colour control changes what hovering
  produces.
- Leaving, blurring or tapping again returns it to ivory.
- `Enter` or `Space` holds a hue; pressing again releases it. Touch taps
  toggle, because there is no "leave" on a touch screen.
- Only `color` and a shadow change, so a hue can never shift the layout.
- Under `prefers-reduced-motion` the lift and the shadow are dropped and the
  colour simply changes.

`ARUSHI` sets about 3.45&nbsp;em wide at this weight and tracking, which is why
`--wm-w` is divided by 3.45 rather than a rounder number. Get that divisor
wrong and the mark overflows the page, which on a phone pushes the whole
layout sideways and takes the navigation with it.

---

## The grid under the hero

The page grid is two CSS background-images on `body::before` and `::after` —
hairlines on a 44&nbsp;px cell, or dots on the same cell — at `--grid-deco`,
fixed to the viewport. On the home page it also answers a pointer.

`mesh.js` puts one `<canvas>` under the hero, full-bleed and exactly as tall
as `.stage`, at `z-index:0` — over the page grid and under the peek layer,
the name, the pills and the ruler. In a window about 200&nbsp;px across it
lifts the straight lines out and puts bent ones back:

1. stroke the straight lines in the page colour — the grid, locally, is gone
2. lay down the light
3. stroke the same lines again, displaced, in the grid's own colour at the
   grid's own opacity
4. stroke them once more through a radial gradient, so the lines nearest the
   pointer carry a little more light than the rest
5. put a lit disc on every crossing in the window, through the same kind of
   gradient, because the crossings are where the eye reads a grid
6. and switch a few of those crossings on and off again, one at a time, as
   the hand moves

The window's edge is what makes this invisible. Displacement falls to exactly
zero there, so step 3 puts each line back precisely where step 1 took it from.
There is no disc, no mask and no seam — outside the window the canvas is
empty and the real grid shows through it.

- Intersections are **pulled** toward the pointer, at most 13&nbsp;px, on a
  field that is zero at the pointer itself and zero again at 185&nbsp;px. It
  chases a smoothed pointer rather than the real one, which is what gives it
  weight.
- Steps 2 and 4–6 all add ivory, so they are **one budget**, not four
  decisions. The page is `#14130F` — red 20 — and the name above it is
  `--ink-100`, red 251. On the brightest pixel there is, they come to about
  210: the glow lifts the ground to 31, the line light takes a line from its
  ambient 31 to 59, the crossing takes that to 120, and a spark at the top of
  its arc takes that to about 210. Three steps of contrast rather than one
  wash, nothing clamped to white, and nothing within forty levels of the
  wordmark.
- A **spark** is a grid index and a clock, not a mark on a trail layer: it is
  resolved through the same displacement field every frame, so it stays on
  its crossing while the grid bends under it, and it is drawn additively, so
  one lit on the way past outlives the window that lit it and finishes fading
  on the untouched grid. That tail is the whole of the afterglow — there is
  nothing to accumulate and nothing to clean up, and the last one is out
  inside a second. About one is lit per 54&nbsp;px of travel and one per
  420&nbsp;ms while the hand moves, never more than twelve at once, each on a
  smooth attack and a slower decay. They are warm ivory leaned toward
  `--hue-ochre-light` — candlelight, and fixed across the palettes, because
  the **Colour** control has no business turning the background gold.
- A pointer that **stops** for 700&nbsp;ms relaxes the mesh, and so does one
  that leaves. The release is quicker than the arrival.
- Then the frame loop **stops**. At rest the canvas holds no ink at all and
  the page costs exactly what it costs without the effect.
- Everything it reads — cell, hairline, colour, opacity, which of the two
  layers is up — comes off the live computed styles, so the **Grid**, **Colour**
  and **Opacity** controls go on owning the grid. Grid *off* paints nothing.
- The canvas is created by the script, not written into the markup. On a
  touch screen, under `prefers-reduced-motion`, or with JavaScript off there
  is no canvas on the page at all.

---

## The navigation mark

The nav carries the portrait rather than a wordmark: a 36&nbsp;px circle,
cropped to the head from the full 1254&nbsp;px illustration so it still reads
at that size, and stored at 144&nbsp;px for high-density screens.

It is fixed at `border-radius:50%` rather than `var(--radius-full)`. The
Radius control reaches every other component on the site, but a face in a
square is a different decision from a card in a square.

The link carries `aria-label="Arushi Prasad, home"` and the image's `alt` is
empty, so the name is announced once rather than twice. With the wordmark
gone from the header, the name still appears in every page `<title>` and in
the footer of every page.

---

## Structure

```
_build.py              wraps fragments in the shared shell
_pages/*.html          the ten body fragments — edit these
_verify.html           the behavioural test harness (see below)
_verify-name.html      the wordmark: the cursive name, and that nothing
                       on it answers a pointer
_verify-hero.html      the four pills, the description each one reveals,
                       and the connectors tying them to the lettering
_verify-mesh.html      the hero grid: that it bends only around the
                       pointer, lands back on the real grid, carries
                       light without clamping to white, and leaves
                       nothing behind
_verify-magic.html     the Magic control: the stickers, what stands
                       down while they are out, and the standing label
                       and arrow under the button at thirteen widths
index.html             generated
work/ designops/ …     generated
assets/
  css/
    tokens.css         every value, defined once
    base.css           reset, canvas grid, type, nav, curtain, footer
    components.css     cards, chips, buttons, rows, stats, panels
    stage.css          the home page only
    lab.css            experiments, snippets, the plant
    writing.css        the writing index — tabs and rows
  js/
    tokens.js          the shared store (loaded before paint, no FOUC)
    site.js            reveal, mobile nav, curtain, copy buttons
    stage.js           letters, toolbar, selection box, live readout,
                       the intro timeline and its restart
    mesh.js            the hero grid's answer to a pointer (home only)
    lab.js             experiments, snippets, the plant
    writing.js         the writing index's Articles / Notes tabs
  fonts/               Inter Tight (variable) + Geist Mono, self-hosted
  img/                 only images the pages actually reference
    avatar.png         the navigation mark — a 144px face crop of
                       "Monochrome Portrait.png"
```

---

## Testing

`_verify.html` drives the real pages in an iframe and reports pass/fail. It
checks behaviour, not appearance: that each control changes the token it
claims to, that Restart restores every default and replays the intro — from
the finished state, and again when interrupted mid-run — that a setting survives a
navigation, that scaling the wordmark shifts nothing, that the plant and the
stepper and the before/after respond to the keyboard, that every button has
an accessible name, that no link 404s and no image fails to decode.

With the server running, open:

```
http://127.0.0.1:8790/07.%20Interactive%20Portfolio/_verify.html
```

Current status: **126 checks, all passing**, in both the default and the
forced-reduced-motion run.

Two notes if you run it headless:

- Chrome headless clamps the viewport to a **500&nbsp;px minimum**, so
  `--window-size=390,…` does not give you a phone. Render the page in a
  390&nbsp;px-wide iframe instead.
- Headless virtual time never advances a running CSS transition, so a
  transitioning property reads back as its start value forever. The harness
  freezes transitions in the frame before measuring resolved styles.

---

## Links out

The Work page links to the two case studies that already exist in this
repository:

- `02. Product Design | Case Studies/01. Workperks/case-study/`
- `02. Product Design | Case Studies/02. Vytals/case-study/`

Both are reached with relative, percent-encoded paths. Neither file was
modified.

---

## Content rules observed

Per `00. root.md`: nothing is invented. Every figure on the site traces to
`Resume/Arushi-Prasad-Resume.md` or
`00.Homepage/md files/02. homepage-content-IA-spec.md`.

Deliberately **not** used:

- The `thumbs/` image set — every file is stamped *REPLACE ME*.
- `hero/03-capsule-system.jpg` — a screenshot of the old homepage carrying
  the 4× / 73% / 2mo Capsule figures the content spec marks unverified.
- Any attrition or tenure number.
- Any claim that WorkPerks has shipped. It is in pilot, and the site says so.

Where there is nothing to show, the page says so: `/writing` lists the four
drafts that have source material behind them and nothing else, the plugin
slot on `/systems` is an explicit placeholder, and the fourth Work entry is a
non-linked card because no case study exists for it.

On `/writing` specifically, three consequences of that rule are visible in
the layout rather than written out:

- **No row is a link.** None of the four pieces is published, so none has a
  destination. The row shape for a published piece — a link across the whole
  row, the title warming, an arrow stepping out — is in `writing.css` and
  unused, which is what the page's closing note means by *built and working*.
- **The right-hand column is the date slot**, and because no piece has a
  publication date it carries the one piece of metadata they do have: their
  status. There are no placeholder dates.
- **Notes holds one piece**, *Three things I stopped defending*, the only one
  of the four that is a short reflection rather than an essay. Both tabs fall
  back to an empty state (`data-empty` on the panel, written in by
  `writing.js`) if their list ever empties.
