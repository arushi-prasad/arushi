#!/usr/bin/env python3
"""Build the interactive portfolio.

Every page is a body fragment in ``_pages/``. This script wraps each one in
the shared shell — head, icon sprite, navigation, footer — and
writes the finished HTML to its route directory. The shell lives in exactly
one place, so the navigation and the footer cannot drift between pages.

    python3 _build.py            # rebuild every route

A fragment starts with a front-matter comment:

    <!--meta
    route: work
    title: Selected work
    ...
    -->

Keys
    route       directory the page is written to ("" is the site root)
    title       <title>, before the site suffix
    desc        meta description
    nav         which nav item is marked aria-current
    word_a      first word of the big page title
    word_b      second word of the big page title
    body_class  extra class on <div class="page">
    stage       "yes" to load stage.js (the homepage only)
    foot        "no" to omit the site footer (the homepage, which ends
                at the contact bar and is exactly one screen tall)
    lab         "yes" to load lab.js (experiments and snippets)
    sheets      comma-separated page-scoped stylesheets in assets/css/
    js          comma-separated page-scoped scripts in assets/js/

Case studies
    A fragment with ``case: yes`` is wrapped in the two-column case-study
    layout: a sticky rail on the left, the fragment's sections in a capped
    reading column to the right of it, and a reading-progress line along
    the bottom edge of the header.

    The rail holds, in reading order, where the page sits, what the project
    is, and which section you are in. The summary came back in Nov 2026,
    after the reference the layout follows: the column it costs is paid for
    by capping the reading measure instead, which is where the width was
    going to waste. Its rows are read out of the fragment's own summary
    block, so the rail cannot disagree with the page.

    The whole block is anchored to the left — to the same axis as the
    navigation above it — rather than centred, and the slack at wide widths
    is left as space on the right. See `.case` in case.css.

    Nothing here knows which case study it is rendering, so Work, DesignOps,
    Leadership, Systems and Writing pages all use it unchanged, and a case
    study written next year gets the layout by setting `case: yes`.

    case         "yes" to use the layout (loads case.css and case.js)
    case_crumb   unused. The rail carried a crumb until November 2026; it
    case_kicker  was removed with the blurb, along with the kicker, the
    case_title   title and the scope line, all of which said in the rail
    case_note    what the page already says in the reading column. The keys
    case_blurb   are still read by nothing and are left in the fragments
                 rather than edited out of eight files.
    case_project the project's own name. It is the title that slides into
                 the top of the rail once the hero's has scrolled away, and
                 it is what the rail is labelled by. Left out, it is read
                 off the last segment of the route.
    case_meta    the summary's rows, as `Label|Value` separated by `;`. Left
                 out — which is the normal case — the rows are READ OUT OF
                 THE FRAGMENT: the `ul.case__facts` or `dl.wp-sum` block the
                 case study already renders in its reading column. Nothing is
                 transcribed, so the rail and the column cannot disagree, and
                 a case study that has no summary block simply gets a rail
                 with a name and a blurb and no rows. `none` says the page's
                 facts block is not a project summary and must not be read as
                 one.
    case_sections  the rail's navigation, as `id|Label` separated by
                 `;`. Each entry is numbered by its position. An entry
                 written `> id|Label` is a sub-section of the one above it
                 and is numbered 16.1, 16.2 instead of taking a chapter
                 number. A third field is tolerated and ignored — it was an
                 activity count that printed at the right-hand edge of the
                 item, and the rail has no right-hand edge to spare now.
                 Every id must match the id of a section in the fragment,
                 and the rail's order must be the page's order: case.js
                 picks the active item by walking the rail, so an entry
                 pointing backwards would hold the marker for the rest of
                 the page. An entry written `-|Label` has no section yet: it
                 takes its number and its place in the contents and renders
                 without a link.
"""
import pathlib
import hashlib
import re
import sys

HERE = pathlib.Path(__file__).parent
PAGES = HERE / "_pages"

SITE = "Arushi Prasad"

# ---------------------------------------------------------------------------
# Navigation. NAV stays the full table of destinations — it is what the footer
# and the mobile sheet render, and the single place a label or a count is
# written down. Which of them appears *where* is TOP and HERO below.
# `count` is the number of entries the page actually holds — it is rendered as
# a superscript, the way a contents page numbers its chapters. Keep these in
# step with the fragments.
# ---------------------------------------------------------------------------
NAV = [
    ("work",       "work",                     "Work",                      "8"),
    # The slug is the route and the label is only what it is called. This one
    # is reached at /designops/ and reads "strategy" — renaming the label
    # moves no link target, and the four pages under it keep their URLs. The
    # accessible name matches the visible one, or a voice command for the
    # word on screen would not find the link.
    ("designops",  "strategy",                 "Strategy",                  "5"),
    ("leadership", "leadership",               "Leadership",                "11"),
    ("fun",        "Fun",                      "Fun stuff",                 "4"),
    ("about",      "About",                    "About",                     ""),
]

# The navigation is in two groups, and no destination is in both. The working
# sections sit in the header; the personal and exploratory ones are the
# portals arranged around the name in the hero. Order is the reading order in
# each place. Slugs here are routes — the work/ route carries its own label
# in NAV above, so renaming it moves no link target.
#
# Systems is deliberately not in either list. The design system is a body of
# leadership work rather than a sibling of it, so /systems/ is reached from
# the Leadership page and from the Work page, and not from the header. The
# route, the page and every existing link to it are unchanged.
TOP  = ["work", "designops", "leadership"]
HERO = ["fun", "writing", "experiments", "about"]

# Which destinations dim the canvas grid, as a list of their own.
#
# This used to be read straight off TOP, which tied a visual treatment to
# whatever happened to be in the header — and the two have nothing to do with
# each other. Adding Home to the header dimmed the home page's grid to a fifth
# of its weight, which is most of the hero's texture gone; taking Systems out
# of the header brightened that page's grid under several thousand words of
# case study. Neither was asked for and neither was visible from the line that
# caused it. The rule is about how much type a page carries, so it says so.
DENSE = ["work", "designops", "leadership", "systems"]

# The three secondary routes. Reachable from the homepage and from the footer
# of every page — never only from one place.
LAB = [
    ("experiments", "Experiments", "5"),
    ("writing",     "Writing",     "1"),
    ("snippets",    "Snippets",    "5"),
]

EMAIL = "arushi.ald@gmail.com"
LINKEDIN = "https://www.linkedin.com/in/arushi-prasad-24850566"

# ---------------------------------------------------------------------------
# Icon sprite. Stroke-drawn at a 16-unit grid so every icon shares a weight.
# ---------------------------------------------------------------------------
SPRITE = """<svg class="sprite" aria-hidden="true" focusable="false" width="0" height="0">
<defs>
<symbol id="i-colour" viewBox="0 0 16 16"><circle cx="8" cy="8" r="5.8"/><path d="M8 2.2a5.8 5.8 0 0 1 0 11.6z" fill="currentColor" stroke="none"/></symbol>
<symbol id="i-type" viewBox="0 0 16 16"><path d="M3.2 13.6 8 2.6l4.8 11"/><path d="M5.3 9.4h5.4"/></symbol>
<symbol id="i-spacing" viewBox="0 0 16 16"><path d="M2.2 3.6v8.8M13.8 3.6v8.8"/><path d="M5 8h6"/><path d="m6.6 6.4-1.7 1.6 1.7 1.6M9.4 6.4 11.1 8 9.4 9.6"/></symbol>
<symbol id="i-radius" viewBox="0 0 16 16"><path d="M2.4 13.6V7.2a4.8 4.8 0 0 1 4.8-4.8h6.4"/><path d="M2.4 2.4h.01M13.6 13.6h.01"/></symbol>
<symbol id="i-opacity" viewBox="0 0 16 16"><path d="M8 2.2c0 0 4.6 4.6 4.6 7.2a4.6 4.6 0 1 1-9.2 0C3.4 6.8 8 2.2 8 2.2Z"/><path d="M8 2.2c0 0 4.6 4.6 4.6 7.2A4.6 4.6 0 0 1 8 14z" fill="currentColor" stroke="none"/></symbol>
<symbol id="i-grid" viewBox="0 0 16 16"><rect x="2.4" y="2.4" width="11.2" height="11.2" rx="1.4"/><path d="M6.13 2.4v11.2M9.87 2.4v11.2M2.4 6.13h11.2M2.4 9.87h11.2"/></symbol>
  <symbol id="i-surprise" viewBox="0 0 16 16"><path d="M7.1 2.6 8.35 6.05 11.8 7.3 8.35 8.55 7.1 12 5.85 8.55 2.4 7.3 5.85 6.05Z"/><path d="M12.3 10.1v2.9M10.85 11.55h2.9"/></symbol>
  <symbol id="i-reset" viewBox="0 0 16 16"><path d="M13.4 8a5.4 5.4 0 1 1-1.8-4"/><path d="M13.6 2.6v3.6H10"/></symbol>
<symbol id="i-bars" viewBox="0 0 16 16"><path d="M2.4 4.6h11.2M2.4 8h11.2M2.4 11.4h11.2"/></symbol>
<symbol id="i-close" viewBox="0 0 16 16"><path d="m4.2 4.2 7.6 7.6M11.8 4.2l-7.6 7.6"/></symbol>
<symbol id="i-copy" viewBox="0 0 16 16"><rect x="5.6" y="5.6" width="8" height="8" rx="1.6"/><path d="M10.4 3.4H4.2a1.6 1.6 0 0 0-1.6 1.6v6.2"/></symbol>
<symbol id="i-mail" viewBox="0 0 16 16"><rect x="2" y="3.4" width="12" height="9.2" rx="1.6"/><path d="m2.8 4.6 5.2 3.9 5.2-3.9"/></symbol>
<symbol id="i-phone" viewBox="0 0 16 16"><path d="M5.6 2.8 3.2 3.6c-.7.3-1 1-.9 1.7.5 2.6 1.8 5 3.7 6.9s4.3 3.2 6.9 3.7h.1c.6 0 1.2-.4 1.4-1l.8-2.4-3-1.6-1.4 1.7a11 11 0 0 1-4.1-4.1l1.7-1.4z"/></symbol>
<symbol id="i-linkedin" viewBox="0 0 16 16"><rect x="2" y="2" width="12" height="12" rx="2.2"/><path d="M5.1 6.9v4.3M5.1 4.7v.01M7.9 11.2V6.9M7.9 8.6c0-1 .6-1.7 1.5-1.7s1.6.7 1.6 1.7v2.6"/></symbol>
<symbol id="i-arrow" viewBox="0 0 16 16"><path d="M4.8 11.2 11.2 4.8"/><path d="M6.2 4.8h5v5"/></symbol>
<symbol id="i-chevron" viewBox="0 0 16 16"><path d="m4.4 6.4 3.6 3.6 3.6-3.6"/></symbol>
<symbol id="i-tick" viewBox="0 0 16 16"><path d="m3.4 8.4 3 3 6.2-7"/></symbol>
<!-- Recognition. Stroke-drawn on the same 16-unit grid and at the same
     weight as the rest, so they sit in a line of text without shouting. -->
<symbol id="i-trophy" viewBox="0 0 16 16"><path d="M4.9 2.7h6.2v3.5a3.1 3.1 0 0 1-6.2 0Z"/><path d="M4.9 3.7H3.3v.9a2 2 0 0 0 1.6 1.9M11.1 3.7h1.6v.9a2 2 0 0 1-1.6 1.9"/><path d="M8 9.3v2.1"/><path d="M6.5 11.4h3v1.9h-3Z"/></symbol>
<symbol id="i-star" viewBox="0 0 16 16"><path d="m8 2.5 1.7 3.45 3.8.55-2.75 2.68.65 3.79L8 11.18l-3.4 1.79.65-3.79L2.5 6.5l3.8-.55Z"/></symbol>
<symbol id="i-medal" viewBox="0 0 16 16"><circle cx="8" cy="10.1" r="3.5"/><path d="M6.1 7.1 4.3 2.6M9.9 7.1l1.8-4.5"/></symbol>
<!-- Document types. A page outline each, told apart by what is on it: ruled
     cells for a workbook, a folded corner for a PDF, one wide band for a
     deck. Same 16-unit grid and weight as everything else. -->
<symbol id="i-sheet" viewBox="0 0 16 16"><rect x="2.8" y="2.2" width="10.4" height="11.6" rx="1.4"/><path d="M2.8 6.1h10.4M2.8 9.9h10.4M7.1 6.1v7.7"/></symbol>
<symbol id="i-pdf" viewBox="0 0 16 16"><path d="M3.4 2.2h5.4l3.8 3.8v7.8H3.4Z"/><path d="M8.8 2.2v3.8h3.8"/><path d="M5.9 9.2h2.6M5.9 11.4h4.2"/></symbol>
<symbol id="i-deck" viewBox="0 0 16 16"><rect x="2.4" y="3" width="11.2" height="7.6" rx="1.3"/><path d="M8 10.6v2.4M6 13.4h4"/></symbol>
<!-- What I use. One mark per item in the About page's stack list, drawn on
     the same 16-unit grid and at the same stroke weight as everything above,
     so they sit inside a line of text rather than on top of it. The
     brand-named ones are simplified evocations, not trademark reproductions;
     the ones that name a practice rather than a tool (Design Systems, UX
     Research, Prototyping...) get a glyph for the thing itself. -->
<!-- Outside the brief. One mark per thing named in the Fun Stuff line,
     drawn on the same 16-unit grid and weight as every other icon here so
     they sit inside a sentence rather than on top of it. -->
<symbol id="f-badminton" viewBox="0 0 16 16"><ellipse cx="6.5" cy="6.5" rx="3.6" ry="4.4" transform="rotate(-40 6.5 6.5)"/><path d="m9.3 9.5 3.9 4.3"/><path d="M4.3 4.9 9 9.1M4.9 8.5 8.5 4.4"/></symbol>
<symbol id="f-strength" viewBox="0 0 16 16"><path d="M2.2 6.4v3.2M4.3 4.7v6.6M11.7 4.7v6.6M13.8 6.4v3.2"/><path d="M4.3 8h7.4"/></symbol>
<symbol id="f-cycling" viewBox="0 0 16 16"><circle cx="4.1" cy="11" r="2.7"/><circle cx="11.9" cy="11" r="2.7"/><path d="m4.1 11 2.9-5.1h3.2l1.7 5.1"/><path d="M6.9 5.9h2.7"/></symbol>
<symbol id="f-trek" viewBox="0 0 16 16"><rect x="4.1" y="6" width="7.8" height="7.8" rx="2.1"/><path d="M6 6V4.7a2 2 0 0 1 4 0V6"/><path d="M6.4 9.6h3.2"/></symbol>
<symbol id="f-coffee" viewBox="0 0 16 16"><path d="M3.2 5.6h8.2v4.1a3.4 3.4 0 0 1-3.4 3.4H6.6a3.4 3.4 0 0 1-3.4-3.4Z"/><path d="M11.4 6.6h1a1.9 1.9 0 0 1 0 3.8h-1"/><path d="M2.4 14.6h10"/><path d="M6 2.2v1.6M8.6 2.2v1.6"/></symbol>
<symbol id="f-plant" viewBox="0 0 16 16"><path d="M4.4 9.4h7.2l-.8 4.4H5.2Z"/><path d="M8 9.4V5.4"/><path d="M8 6.8C8 4.5 6.4 2.6 4.3 2.6c0 2.3 1.6 4.2 3.7 4.2Z"/><path d="M8 7.6c0-2 1.6-3.7 3.5-3.7 0 2-1.6 3.7-3.5 3.7Z"/></symbol>
<symbol id="f-bowl" viewBox="0 0 16 16"><path d="M2.6 7.8h10.8a5.4 5.4 0 0 1-10.8 0Z"/><path d="M1.5 7.8h13"/><circle cx="6" cy="5.3" r="1.1"/><circle cx="9.7" cy="4.7" r="1.1"/></symbol>
<symbol id="f-people" viewBox="0 0 16 16"><circle cx="6" cy="5.5" r="2.4"/><path d="M2.3 13.2c0-2 1.7-3.7 3.7-3.7s3.7 1.7 3.7 3.7"/><circle cx="11.7" cy="6.4" r="1.8"/><path d="M10.2 9.8c1.9.1 3.5 1.6 3.5 3.4"/></symbol>
<symbol id="f-music" viewBox="0 0 16 16"><path d="M6.2 12.3V3.8l7-1.4v8.5"/><circle cx="4.3" cy="12.3" r="1.9"/><circle cx="11.3" cy="10.9" r="1.9"/></symbol>
<symbol id="f-mountain" viewBox="0 0 16 16"><path d="M1.6 12.9 6.4 4.2l4.2 7.6"/><path d="M8.2 12.9 11.4 7l3 5.9z"/><path d="M1.4 12.9h13.2"/></symbol>
<symbol id="t-figjam" viewBox="0 0 16 16"><rect x="2.2" y="2.6" width="11.6" height="10.8" rx="1.8"/><path d="M4.7 10c1-1.7 2.1-1.7 3.1 0s2.1 1.7 3.1 0"/><circle cx="5.6" cy="5.9" r="1.1"/></symbol>
<symbol id="t-framer" viewBox="0 0 16 16"><path d="M12.2 2.4H3.8l4.2 4.1h4.2z"/><path d="M3.8 6.5h8.4L8 10.6H3.8z"/><path d="M8 10.6v3.3l-4.2-3.3z"/></symbol>
<symbol id="t-mobbin" viewBox="0 0 16 16"><rect x="2.2" y="3.3" width="5" height="9.4" rx="1.3"/><rect x="8.8" y="3.3" width="5" height="9.4" rx="1.3"/><path d="M4.7 5.5h.01M11.3 5.5h.01"/></symbol>
<symbol id="t-gemini" viewBox="0 0 16 16"><path d="M8 2.1c.5 3.2 2.6 5.3 5.8 5.8-3.2.5-5.3 2.6-5.8 5.8-.5-3.2-2.6-5.3-5.8-5.8C5.4 7.4 7.5 5.3 8 2.1Z"/></symbol>
<symbol id="t-copilot" viewBox="0 0 16 16"><path d="M2.9 8.5c0-2.7 2.3-4.8 5.1-4.8s5.1 2.1 5.1 4.8v1.3c0 1.9-2.3 3.3-5.1 3.3s-5.1-1.4-5.1-3.3Z"/><path d="M6 8.7h.01M10 8.7h.01"/><path d="M8 3.7V2.1"/></symbol>
<symbol id="t-antigravity" viewBox="0 0 16 16"><path d="M8 11.9V2.6"/><path d="m5.2 5.4 2.8-2.8 2.8 2.8"/><path d="M3.2 14.1h9.6" stroke-dasharray="1.5 2.1"/></symbol>
<symbol id="t-html" viewBox="0 0 16 16"><path d="m5.3 5.1-3 2.9 3 2.9M10.7 5.1l3 2.9-3 2.9"/><path d="m9.3 3.5-2.6 9"/></symbol>
<symbol id="t-js" viewBox="0 0 16 16"><rect x="2.2" y="2.2" width="11.6" height="11.6" rx="2.1"/><path d="M7 6.3v4c0 .9-.6 1.4-1.4 1.4-.6 0-1.1-.3-1.4-.8"/><path d="M11.8 6.9c-1.4-.8-2.6-.2-2.6.8 0 1.5 2.6 1 2.6 2.4 0 .9-1.1 1.5-2.6.7"/></symbol>
<symbol id="t-next" viewBox="0 0 16 16"><circle cx="8" cy="8" r="5.8"/><path d="M5.9 10.9V5.3l4.7 6"/><path d="M10.3 5.3v3.1"/></symbol>
<symbol id="t-tailwind" viewBox="0 0 16 16"><path d="M2.6 6.6c.7-1.9 2-2.8 3.7-2.8 2.6 0 3.1 1.9 4.4 2.3.9.2 1.7-.1 2.4-1"/><path d="M2.6 11.6c.7-1.9 2-2.8 3.7-2.8 2.6 0 3.1 1.9 4.4 2.3.9.2 1.7-.1 2.4-1"/></symbol>
<symbol id="t-node" viewBox="0 0 16 16"><path d="M8 1.9 13.5 5v6L8 14.1 2.5 11V5Z"/><path d="M6.3 10.4V6.6l3.4 3.8V6.6"/></symbol>
<symbol id="t-postgres" viewBox="0 0 16 16"><ellipse cx="8" cy="4" rx="5.2" ry="2.2"/><path d="M2.8 4v8c0 1.2 2.3 2.2 5.2 2.2s5.2-1 5.2-2.2V4"/><path d="M2.8 8c0 1.2 2.3 2.2 5.2 2.2s5.2-1 5.2-2.2"/></symbol>
<symbol id="t-figma" viewBox="0 0 16 16"><rect x="5.4" y="2.3" width="5.3" height="3.5" rx="1.75"/><rect x="5.4" y="6.3" width="5.3" height="3.5" rx="1.75"/><circle cx="8.05" cy="12" r="1.9"/></symbol>
<symbol id="t-native" viewBox="0 0 16 16"><rect x="3.9" y="1.7" width="8.2" height="12.6" rx="1.9"/><circle cx="8" cy="8" r="1.1"/><ellipse cx="8" cy="8" rx="3.3" ry="1.4"/><ellipse cx="8" cy="8" rx="3.3" ry="1.4" transform="rotate(62 8 8)"/></symbol>
<symbol id="t-ts" viewBox="0 0 16 16"><rect x="2.2" y="2.2" width="11.6" height="11.6" rx="2.1"/><path d="M4.5 6.6h3.7M6.35 6.6v4.8"/><path d="M11.7 6.9c-1.6-.8-2.7-.1-2.7.8 0 1.6 2.7 1 2.7 2.5 0 .9-1.1 1.6-2.7.8"/></symbol>
<symbol id="t-expo" viewBox="0 0 16 16"><path d="M2.2 12.6 7.2 4a.95.95 0 0 1 1.6 0l5 8.6"/><path d="M6 12.6 8 9.2l2 3.4"/></symbol>
<symbol id="t-supabase" viewBox="0 0 16 16"><path d="M8.9 1.7 3.5 8.7h4.2l-.5 5.6 5.3-7H8.4Z"/></symbol>
<symbol id="t-claude" viewBox="0 0 16 16"><rect x="1.7" y="2.9" width="12.6" height="10.2" rx="1.7"/><path d="m4.4 6.7 1.8 1.8-1.8 1.8"/><path d="M8.4 10.3h3.2"/></symbol>
<symbol id="t-playwright" viewBox="0 0 16 16"><path d="M2.9 3.5h10.2v4.9c0 2.8-2.3 5.1-5.1 5.1S2.9 11.2 2.9 8.4Z"/><path d="M5.8 7.1h.01M10.2 7.1h.01"/><path d="M6.2 10.3c1.1.9 2.5.9 3.6 0"/></symbol>
<symbol id="t-cucumber" viewBox="0 0 16 16"><path d="M12.5 3.5c1.6 1.6.6 5.3-2.3 8.2s-6.6 3.9-8.2 2.3-.6-5.3 2.3-8.2 6.6-3.9 8.2-2.3Z"/><path d="m6.4 6.5 1.6 1.6M8.7 5.1l1.6 1.6M4.9 8.9l1.6 1.6"/></symbol>
<symbol id="t-storybook" viewBox="0 0 16 16"><path d="M8 4.3C6.6 2.9 4.8 2.5 2.6 2.7v9c2.2-.2 4 .2 5.4 1.6 1.4-1.4 3.2-1.8 5.4-1.6v-9c-2.2-.2-4 .2-5.4 1.6Z"/><path d="M8 4.3v9"/></symbol>
<symbol id="i-shield" viewBox="0 0 16 16"><path d="M8 2.1 3.4 4v4.2c0 2.8 1.9 4.7 4.6 5.7 2.7-1 4.6-2.9 4.6-5.7V4Z"/><path d="m6.1 7.9 1.5 1.5 2.5-3"/></symbol>
</defs>
</svg>"""


def icon(name, cls="ico"):
    return f'<svg class="{cls}" aria-hidden="true" focusable="false"><use href="#i-{name}"></use></svg>'


def ver(name):
    """?v=<hash of the file's contents>.

    Without this the browser is free to serve a cached stylesheet or script
    against freshly built HTML, which looks exactly like "the change did not
    work". The hash only moves when the file does, so caching still works —
    it just cannot be wrong.
    """
    f = HERE / name
    if not f.exists():
        return ""
    return "?v=" + hashlib.sha1(f.read_bytes()).hexdigest()[:8]


def up_from(route):
    """The `../` prefix that climbs from `route` back to the site root.

    Routes may now nest — designops/framework sits a level below
    designops — so this counts separators instead of assuming one level.
    """
    return "../" * (route.count("/") + 1) if route else ""


def rel(route, target):
    """A link from `route` to `target`, both site-relative route names."""
    up = up_from(route)
    return f"{up}{target}/" if target else (up or "./")


def nav_html(route, current):
    # The header carries the working sections only. The other four are the
    # hero portals, so putting them here as well would list them twice.
    by_slug = {slug: (slug, label, full, count) for slug, label, full, count in NAV}
    links = []
    # The superscript is how many things the section holds, the same quantity
    # the sheet prints beside it — not the item's position in the row.
    for slug, label, full, count in (by_slug[s] for s in TOP):
        cur = ' aria-current="page"' if slug == current else ""
        # Home is the site root, not a directory, so it is the one entry whose
        # link target is not its slug.
        href = rel(route, "" if slug == "home" else slug)
        # An empty superscript is a gap the eye still reads as a number that
        # failed to print, so a section without a count prints none.
        sup = f'<sup class="nav__count" aria-hidden="true">{count}</sup>' if count else ""
        links.append(
            f'<li><a class="nav__link" href="{href}"{cur} aria-label="{full}">'
            f'{label}{sup}</a></li>'
        )
    sheet = []
    for slug, label, full, count in NAV + [(s, l, l, c) for s, l, c in LAB]:
        cur = ' aria-current="page"' if slug == current else ""
        href = rel(route, "" if slug == "home" else slug)
        sheet.append(
            f'<li><a class="nav-sheet__link" href="{href}"{cur}>{full}'
            f'<span>{count or "·"}</span></a></li>'
        )
    home = rel(route, "")
    asset = up_from(route) + "assets"
    # Magic. The same control that used to sit at the right-hand end of the
    # toolbar under the hero, moved to the end of the navigation and given a
    # colour of its own. It is wired by stage.js, which only the homepage
    # loads, so only the homepage prints it: a button that looks live and
    # does nothing is worse than no button.
    #
    # It has exactly one job — show the five stickers, or put them away — and
    # nothing about the button itself reports which way round it is. One
    # icon, one name, one hint, in both states. The state that matters is on
    # the page, not on the control: five illustrations are either out across
    # the hero or they are not, which is not a thing a visitor can miss.
    #
    # There is no divider any more. It sat between the links and this button
    # and was 25px of the run on its own, which made the distance from
    # "leadership" to the sparkle more than twice the distance between any
    # two words in the row. The spacing does the separating now.
    #
    # The two labels share one slot under the pill and are both out of flow:
    # the hint while it is being approached, the readout once a design
    # control has said what it changed. Neither can move the navigation.
    #
    # aria-pressed is what carries the state to a screen reader, so the
    # accessible name can stay one fixed phrase that says what the button
    # does rather than which half of the toggle is next.
    magic = ""
    if current == "home":
        magic = f'''
      <div class="magic">
        <p class="magic__hint" aria-hidden="true" data-magic-hint>a little more ME</p>
        <p class="magic__say" data-say aria-hidden="true"></p>
        <button class="magic__btn" type="button" data-surprise aria-keyshortcuts="5" aria-pressed="false" aria-label="Toggle personality stickers">
          {icon('surprise', 'ico magic__ico')}
        </button>
      </div>'''
    # The mark is the portrait. alt is empty because the link itself carries
    # the accessible name — otherwise it would be announced twice.
    #
    # The header now carries a named Home link as well, so the mark no longer
    # takes aria-current: two elements announcing themselves as the current
    # page is one more than there is a current page.
    return f"""<header class="nav-wrap">
  <nav class="nav shell" aria-label="Primary">
    <a class="nav__logo" href="{home}" aria-label="Arushi Prasad, home"{' aria-current="page"' if current == "home" and "home" not in TOP else ""}>
      <img class="nav__avatar" src="{asset}/img/avatar.png" alt="" width="58" height="58" decoding="async">
    </a>
    <div class="nav__right">
      <ul class="nav__links" role="list">
        {''.join(links)}
      </ul>
{magic}
      <button class="nav__burger" type="button" data-nav-open aria-label="Open navigation" aria-expanded="false" aria-controls="nav-sheet">{icon('bars')}</button>
    </div>
  </nav>
</header>
<div class="nav-sheet" id="nav-sheet" data-open="false">
  <button class="nav-sheet__close" type="button" data-nav-close aria-label="Close navigation">{icon('close')}</button>
  <ul class="nav-sheet__list" role="list">{''.join(sheet)}</ul>
  <p class="t-sm t-dim">Design leader building products, systems and teams.</p>
</div>"""


def foot_html():
    """One line: who and where. The footer used to carry a four-column block
    of section links, the lab routes, contact details and a note about the
    token controls. All of it is reachable from the header or the homepage,
    so the footer now closes the page rather than repeating it."""
    return f"""<footer class="foot">
  <div class="shell">
    <div class="foot__base">
      <p class="t-label">Arushi Prasad · Design leader</p>
      <p class="t-label t-dim">Pune, India</p>
    </div>
  </div>
</footer>"""


META_RE = re.compile(r"^<!--meta\s*(.*?)-->\s*", re.S)


def parse(text):
    m = META_RE.match(text)
    if not m:
        raise SystemExit("fragment is missing its <!--meta ... --> block")
    meta = {}
    for line in m.group(1).strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, text[m.end():]


def kv_rows(raw):
    """[(label, value)] from the `Label|value; Label|value` grammar.

    The same shape `case_meta` uses, so a page writes its metadata one way
    wherever it puts it. Empty halves are dropped rather than rendered as a
    row with nothing in it.
    """
    rows = []
    for item in (raw or "").split(";"):
        if "|" in item:
            k, v = item.split("|", 1)
            if k.strip() and v.strip():
                rows.append((k.strip(), v.strip()))
    return rows


def page_hero(meta, route):
    """The big two-word title every section page opens with."""
    a, b = meta.get("word_a"), meta.get("word_b")
    if not a:
        return ""
    cards = meta.get("hero_cards", "")
    tagline = meta.get("tagline", "")
    # A page may stand its particulars next to the title rather than only in
    # the case rail — WorkPerks does, so duration, category and platform are
    # read before the first chapter rather than off to one side. Same
    # `Label|value;` grammar as case_meta. A page that writes neither key
    # gets neither block; nothing is emitted empty, because an empty <p>
    # still takes its margin and opens a gap under the heading.
    hero_meta = kv_rows(meta.get("hero_meta", ""))
    tag_html = (f'\n  <p class="page-hero__tagline" data-reveal>{tagline}</p>'
                if tagline.strip() else "")
    title_html = (f'<h1 class="page-hero__title" data-reveal>\n'
                  f'    <span class="page-hero__word page-hero__word-a">{a}</span>\n'
                  f'    <span class="page-hero__word page-hero__word-b">{b}</span>\n'
                  f'  </h1>')
    if hero_meta:
        rows = "".join(
            f'<div class="page-hero__meta-row">'
            f'<dt class="t-label page-hero__meta-k">{k}</dt>'
            f'<dd class="page-hero__meta-v">{v}</dd></div>'
            for k, v in hero_meta)
        # The particulars sit on the end of the title's last line rather than
        # under it, so the two read as one object. A flex row with the h1
        # first: the heading keeps its own box and the block lands where the
        # type stops, wrapping under it when the width runs out.
        title_html = (f'<div class="page-hero__titlerow">\n  {title_html}\n'
                      f'  <dl class="page-hero__meta" data-reveal>{rows}</dl>\n  </div>')
    # Heading first, then the tagline, then any supporting cards. The cards used
    # to sit above the title and read as a duplicate of the card grid further
    # down the page.
    return f"""<header class="page-hero shell">
  {title_html}{tag_html}
  {cards}
</header>"""


# ---------------------------------------------------------------------------
# The rail's project summary. Two parts: the project's name, which is not
# shown until the hero's copy of it has scrolled away, and the rows of
# metadata.
#
# The rows are not written down a second time. Every case study already
# renders its own summary in the reading column — Vidal and Vytals as a
# `ul.case__facts`, WorkPerks as a `dl.wp-sum` — and these read that block
# out of the fragment and set the same label/value pairs in the rail. The
# page stays the single source: edit the summary in the fragment and the rail
# follows it, with no key to keep in step and nothing to drift.
#
# A fragment that has neither block gets a rail with a name and a blurb and
# no rows, which is what the DesignOps pages and the essay get. Nothing is
# invented to fill the space.
# ---------------------------------------------------------------------------
FACT_RE = re.compile(
    r'<li[^>]*class="[^"]*case__fact\b[^"]*"[^>]*>\s*<b>(.*?)</b>\s*<span>(.*?)</span>',
    re.S)
SUM_RE = re.compile(
    r'<dt[^>]*class="[^"]*wp-sum__k\b[^"]*"[^>]*>(.*?)</dt>\s*'
    r'<dd[^>]*class="[^"]*wp-sum__v\b[^"]*"[^>]*>(.*?)</dd>',
    re.S)


def flatten(html_fragment):
    """The text of a cell, with its tags dropped and its spaces collapsed.

    A value may carry an <abbr> or a <strong>; the rail sets these at a size
    where that markup does nothing, and a stray open tag copied into an
    <dd> would break the page rather than style it.
    """
    txt = re.sub(r"<[^>]+>", "", html_fragment)
    return " ".join(txt.split())


def case_meta_rows(meta, body):
    """[(label, value)] for the rail's summary.

    `case_meta: none` is the opt-out, and it is not the same thing as
    leaving the key off. A page can carry a `case__facts` block that is not
    a project summary — the essay's is a row of figures from its own
    argument, "Designers in 2019: 2" — and read into a rail those become
    metadata about a project that does not exist. Such a page says `none`
    and gets a rail with a name and a blurb, which is the honest amount of
    summary it has.
    """
    raw = meta.get("case_meta", "").strip()
    if raw.lower() == "none":
        return []
    if raw:
        rows = []
        for item in raw.split(";"):
            if "|" in item:
                k, v = item.split("|", 1)
                if k.strip() and v.strip():
                    rows.append((k.strip(), v.strip()))
        return rows

    # `<b>value</b><span>Label</span>` — the label is the second cell.
    rows = [(flatten(lab), flatten(val)) for val, lab in FACT_RE.findall(body)]
    if rows:
        return rows
    # `<dt>Label</dt><dd>value</dd>` — the label is the first.
    return [(flatten(k), flatten(v)) for k, v in SUM_RE.findall(body)]


def case_project(meta):
    """The project's name. Read off the route when it is not written down."""
    name = meta.get("case_project", "").strip()
    if name:
        return name
    segs = [x for x in meta.get("route", "").split("/") if x]
    return segs[-1].replace("-", " ") if segs else meta.get("title", "")


def case_summary(meta, body):
    rows = case_meta_rows(meta, body)
    items = "".join(
        f'<div class="case__meta-row"><dt class="case__meta-k">{k}</dt>'
        f'<dd class="case__meta-v">{v}</dd></div>'
        for k, v in rows
    )
    # An empty <dl> is a container with nothing in it, so a page without rows
    # does not print one at all.
    dl = f'<dl class="case__meta">{items}</dl>' if items else ""
    # The name is in the markup from the start — it is what the rail is
    # labelled by, and a label that only exists after a scroll is a landmark
    # with no name until then. What changes is whether it is SHOWN: the wrap
    # around it is a collapsed grid row until case.js says the hero's title
    # has gone, so the two are never on the screen together. Without the
    # script the wrap is open, because a title only a script can reveal is a
    # title nobody reading without one would ever see.
    return f"""<div class="case__about">
      <div class="case__titlewrap">
        <h2 class="case__project" id="case-project">{case_project(meta)}</h2>
      </div>
      {dl}
    </div>"""


def case_rail(meta, body):
    """The sticky rail: what this project is, and which section you are in.

    Two things, in reading order: the project summary and the numbered
    contents. The summary is read out of the fragment rather than written
    down again — see case_summary above.

    The summary's title is hidden until the hero's has scrolled off, so the
    rail does not repeat a title the reader can already see. On the narrow
    layout there is no rail column to put it in, so it takes the bar's
    eyebrow slot instead and the word "Contents" fades out under it.

    The active item is set by case.js; the markup here is the complete,
    working version without it — a list of anchors, each one numbered with
    the number the writing refers to.

    Ahead of both sits the contents button. It is the whole of the rail on a
    phone, where a 17rem column beside the reading matter is not available:
    it names the section being read and opens the panel, which is the same
    markup the desktop rail shows open. On the desktop it is display:none, so
    it is out of the accessibility tree rather than merely invisible.
    """
    items = []
    rows = [r.strip() for r in meta.get("case_sections", "").split(";") if r.strip()]
    # The number is the section's position in the rail, counted here, not the
    # optional third field — on the DesignOps pages that field is an activity
    # count, and three of the eight case studies never wrote one at all.
    # Counting it means every rail is numbered the same way and the numbers
    # always agree with the order you read the page in.
    #
    # An entry written `> id|Label` is a sub-section of the entry above it and
    # is numbered 16.1, 16.2 rather than taking a chapter number of its own.
    # The chapter counter does not advance for one, so a chapter with two
    # sub-sections is still followed by the next whole number.
    chapter = 0
    sub = 0
    first_label = ""
    for raw in rows:
        is_sub = raw.startswith(">")
        if is_sub:
            raw = raw[1:].strip()
        parts = [p.strip() for p in raw.split("|")]
        sid, label = parts[0], parts[1]
        if is_sub:
            sub += 1
            number = f"{chapter:02d}.{sub}"
        else:
            chapter += 1
            sub = 0
            number = f"{chapter:02d}"
        num = f'<span class="case__count">{number}</span>'
        # Number first, so it is the hanging indent the labels align to and
        # the marker that takes the accent. The bullet it replaces was the
        # same signal twice, in a column with no room for two.
        cls = "case__item case__item--sub" if is_sub else "case__item"
        label_html = f'{num}<span class="case__label">{label}</span>'
        # The button's resting text is the first section's own name, so the
        # control reads correctly before a scroll has happened and with no
        # script at all. Taken from the first entry that is a real link: a
        # placeholder has no section to be inside.
        if not first_label and sid not in ("", "-"):
            first_label = label
        if sid in ("", "-"):
            # An entry whose section does not exist yet. It is written into
            # the contents so the numbering and the order are already right,
            # and it is a span rather than an anchor so there is no link that
            # goes nowhere. case.js only ever looks for [data-case-link], so
            # one of these is invisible to the scroll marker by construction.
            items.append(
                f'<li class="{cls}"><span class="case__link case__link--flat">'
                f'{label_html}</span></li>'
            )
        else:
            items.append(
                f'<li class="{cls}"><a class="case__link" href="#{sid}" data-case-link="{sid}">'
                f'{label_html}</a></li>'
            )

    return f"""<aside class="case__rail" data-case-rail data-open="false" aria-labelledby="case-project">
  <button class="case__toc" type="button" data-case-toc aria-expanded="false" aria-controls="case-toc">
    <span class="case__toc-eyebrow">
      <span class="case__toc-word">Contents</span>
      <span class="case__toc-name">{case_project(meta)}</span>
    </span>
    <span class="case__toc-now" data-case-now>{first_label}</span>
    {icon('chevron', 'ico case__toc-ico')}
  </button>
  <div class="case__rail-in" id="case-toc">
    {case_summary(meta, body)}
    <nav class="case__nav" aria-label="Sections in this case study">
      <ol class="case__list" role="list">
        {''.join(items)}
      </ol>
    </nav>
  </div>
</aside>"""


def case_wrap(meta, body):
    """Two columns: the rail, then the fragment. Nothing else changes.

    Ahead of them, the reading-progress line. It is written here rather
    than in each fragment because it belongs to the layout, and it is
    empty markup — case.js drives the fill, CSS hides the whole thing when
    there is no script to drive it. aria-hidden because it is a picture of
    the scrollbar the window already has: a screen reader is told the
    reading position by the scrollbar and by the rail's aria-current, and
    a third announcement of it is noise.
    """
    if meta.get("case") != "yes":
        return body
    return f"""<div class="case__prog" data-case-prog aria-hidden="true"><span class="case__prog-bar" data-case-prog-bar></span></div>
<div class="case">
{case_rail(meta, body)}
<div class="case__main">
{body}
</div>
</div>"""


DATA_BLOCKS = None


def fill_data(body):
    """Replace ``<!--data:key-->`` with the block rendered from planning.json.

    Lazy, so pages that use no data blocks never read the JSON, and loud: an
    unknown key stops the build rather than leaving a silent hole in the page.
    """
    global DATA_BLOCKS
    if "<!--data:" not in body:
        return body
    if DATA_BLOCKS is None:
        sys.path.insert(0, str(HERE / "_data"))
        import render
        import render_quality
        import render_ai
        import render_leadership
        import render_capsule
        DATA_BLOCKS = dict(render.blocks())
        DATA_BLOCKS.update(render_quality.blocks())
        DATA_BLOCKS.update(render_ai.blocks())
        DATA_BLOCKS.update(render_leadership.blocks())
        DATA_BLOCKS.update(render_capsule.blocks())

    def sub(m):
        key = m.group(1)
        if key not in DATA_BLOCKS:
            raise SystemExit("unknown data block: %s (have %s)"
                             % (key, ", ".join(sorted(DATA_BLOCKS))))
        return DATA_BLOCKS[key]

    return re.sub(r"<!--data:([a-z0-9-]+)-->", sub, body)


def build(fragment):
    meta, body = parse(fragment.read_text(encoding="utf-8"))
    body = fill_data(body)
    route = meta.get("route", "")
    asset = up_from(route) + "assets"

    scripts = ['<script src="%s/js/site.js%s" defer></script>' % (asset, ver("assets/js/site.js"))]
    if meta.get("stage") == "yes":
        scripts.append('<script src="%s/js/stage.js%s" defer></script>' % (asset, ver("assets/js/stage.js")))
    if meta.get("lab") == "yes":
        scripts.append('<script src="%s/js/lab.js%s" defer></script>' % (asset, ver("assets/js/lab.js")))
    if meta.get("case") == "yes":
        scripts.append('<script src="%s/js/case.js%s" defer></script>' % (asset, ver("assets/js/case.js")))
    # Page-scoped scripts, the counterpart of `sheets:` below: a page that is
    # art-directed enough to need its own behaviour carries its own file, and
    # no other page downloads it.
    for name in [j.strip() for j in meta.get("js", "").split(",") if j.strip()]:
        scripts.append('<script src="%s/js/%s.js%s" defer></script>'
                       % (asset, name, ver("assets/js/%s.js" % name)))

    sheets = ["tokens", "base", "components"]
    if meta.get("stage") == "yes":
        sheets.append("stage")
    if meta.get("lab") == "yes":
        sheets.append("lab")
    # Page-scoped stylesheets, so a heavily art-directed page can carry its own
    # CSS without every other page paying for it.
    sheets += [s.strip() for s in meta.get("sheets", "").split(",") if s.strip()]
    if meta.get("case") == "yes":
        sheets.append("case")
    # A sheet named in both `sheets:` and by a flag would otherwise be linked
    # twice, and the first link decides where it sits in the cascade. Keep the
    # LAST position of each: case.css adjusts tiles.css, so it has to come
    # after it, and the flag above is what puts it there.
    sheets = list(dict.fromkeys(reversed(sheets)))[::-1]
    links = "\n  ".join(
        '<link rel="stylesheet" href="%s/css/%s.css%s">' % (asset, sh, ver("assets/css/%s.css" % sh))
        for sh in sheets
    )

    # The home page deliberately has no footer: it is one screen that ends
    # at the email address, so there is nothing below the fold to land in.
    foot = "" if meta.get("foot") == "no" else foot_html()

    tokens_v = ver("assets/js/tokens.js")

    title = meta["title"]
    full_title = title if title == SITE else f"{title} · {SITE}"

    # The content-heavy destinations dim the canvas grid (base.css reads
    # data-dense) so it stops competing with the type. DENSE, not TOP — see
    # the note beside it.
    dense = ' data-dense="yes"' if meta.get("nav") in DENSE else ""

    html = f"""<!DOCTYPE html>
<html lang="en" data-palette="mono" data-type="editorial" data-density="comfortable" data-radius="subtle"{dense}>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{full_title}</title>
  <meta name="description" content="{meta.get('desc', '')}">
  <meta name="color-scheme" content="dark">
  <link rel="preload" href="{asset}/fonts/inter-tight-latin.woff2" as="font" type="font/woff2" crossorigin>
  {links}
  <!-- Loaded before paint so a saved token preference is applied to <html>
       without a flash of the defaults. -->
  <script src="{asset}/js/tokens.js{tokens_v}"></script>
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
{SPRITE}
{nav_html(route, meta.get('nav', ''))}
<main id="main" tabindex="-1">
<div class="page {meta.get('body_class', '')}">
{page_hero(meta, route)}
{case_wrap(meta, body.strip())}
</div>
</main>
{foot}
{chr(10).join(scripts)}
</body>
</html>
"""

    out_dir = HERE / route if route else HERE
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(html, encoding="utf-8")
    return route or "(root)"


def main():
    frags = sorted(PAGES.glob("*.html"))
    if not frags:
        raise SystemExit("no fragments found in _pages/")
    for f in frags:
        print("built", build(f))
    print(f"\n{len(frags)} pages written.")


if __name__ == "__main__":
    sys.exit(main())
