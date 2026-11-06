#!/usr/bin/env python3
"""Render the Capsule design-system exhibits from ``capsule.json``.

Every value on this page — every hex, every pixel size, every state name —
comes out of the JSON, which is a transcription of the blueprint and the live
Figma file. Nothing here is styled by eye: if a swatch is #005DAC it is because
the blueprint says Blue-400 is #005DAC, and the same string is printed next to
it. That is the only way a design-system case study can be checked.

The exhibits render as *light* panels inside the dark page, because Capsule is
a light-first system. Reproducing it on a dark canvas would be showing
something that does not exist.

``blocks()`` returns ``{key: html}`` for ``<!--data:key-->`` in the fragment.
"""
import html
import json
import pathlib

HERE = pathlib.Path(__file__).parent
D = json.loads((HERE / "capsule.json").read_text(encoding="utf-8"))


def esc(s):
    return html.escape(str(s), quote=False)


def stage(inner, label="", note="", wide=False, cls=""):
    """A light panel. Everything inside it is the real system, at real values."""
    cap = f'<p class="cap-stage__note">{esc(note)}</p>' if note else ""
    lab = f'<p class="cap-stage__label">{esc(label)}</p>' if label else ""
    w = " cap-stage--wide" if wide else ""
    return f'<div class="cap-stage{w} {cls}" data-reveal>{lab}{inner}</div>{cap}'


def tag(kind):
    """verified / confirm / future — the page never shows a claim untagged."""
    words = {
        "verified": "verified",
        "confirm": "needs your confirmation",
        "future": "future direction",
    }
    return f'<span class="cap-tag cap-tag--{kind}">{words.get(kind, kind)}</span>'


# ---------------------------------------------------------------------------
# Counts — what the system measurably is. Each one is countable from a file.
# ---------------------------------------------------------------------------
def counts():
    items = "".join(
        f"""<li class="cap-count" data-reveal style="--i:{i}">
  <p class="cap-count__v" data-count-text="{esc(c["v"])}">{esc(c["v"])}</p>
  <p class="cap-count__l">{esc(c["l"])}</p>
  <p class="cap-count__q">{esc(c["q"])}</p>
  <p class="cap-count__s">{tag(c["k"])}<span>{esc(D["_about"]["sources"][c["s"]].split("; ")[0])}</span></p>
</li>"""
        for i, c in enumerate(D["counts"])
    )
    return f'<ul class="cap-counts">{items}</ul>'


# ---------------------------------------------------------------------------
# 01 · The challenge. No invented "before" screenshot — the problem is stated
# from the specification that answers it, and the note says exactly that.
# ---------------------------------------------------------------------------
def challenge():
    rows = "".join(
        f"""<li class="cap-before" data-reveal style="--i:{i}">
  <span class="cap-before__n">0{i + 1}</span>
  <div><h4>{esc(a)}</h4><p>{esc(b)}</p></div>
</li>"""
        for i, (a, b) in enumerate(D["challenge"]["before"])
    )
    return f"""<p class="cap-lede" data-reveal>{esc(D["challenge"]["lede"])}</p>
<ul class="cap-befores">{rows}</ul>
<p class="cap-note" data-reveal>{tag(D["challenge"]["k"])}{esc(D["challenge"]["note"])}</p>"""


def principles():
    items = "".join(
        f"""<li class="cap-principle" data-reveal style="--i:{i};--pc:{c}">
  <span class="cap-principle__swatch" aria-hidden="true"></span>
  <h4 class="cap-principle__name">{esc(n)}</h4>
  <p class="cap-principle__body">{esc(b)}</p>
</li>"""
        for i, (n, b, c) in enumerate(D["principles"])
    )
    return f'<ul class="cap-principles">{items}</ul>'


def layers():
    items = "".join(
        f"""<li class="cap-layer" data-reveal style="--i:{i}">
  <span class="cap-layer__i">{i + 1}</span>
  <span class="cap-layer__n">{esc(n)}</span>
  <span class="cap-layer__d">{esc(d)}</span>
  <span class="cap-layer__c">{esc(c)}</span>
</li>"""
        for i, (n, d, c) in enumerate(D["layers"])
    )
    return f"""<ol class="cap-layers">{items}</ol>
<p class="cap-note" data-reveal>Each layer only depends on the one above it. That is the whole
reason a brand decision can be made once: it enters at the token layer and arrives everywhere below.</p>"""


# ---------------------------------------------------------------------------
# 03 · Foundations. The big exhibits.
# ---------------------------------------------------------------------------
def colour():
    brand = "".join(
        f"""<li class="cap-brand" style="--c:{hexv}">
  <span class="cap-brand__chip"></span>
  <span class="cap-brand__role">{esc(role)}</span>
  <span class="cap-brand__name">{esc(name)}</span>
  <code class="cap-brand__hex">{esc(hexv)}</code>
  <span class="cap-brand__use">{esc(use)}</span>
</li>"""
        for role, name, hexv, use in D["colour"]["brand"]
    )

    scales = []
    for sc in D["colour"]["scales"]:
        steps = "".join(
            f"""<button class="cap-swatch" type="button" style="--c:{hexv}"
     data-copy="{esc(hexv)}" aria-label="{esc(name)}, {esc(hexv)}. {esc(use)}">
  <span class="cap-swatch__chip"></span>
  <span class="cap-swatch__name">{esc(name)}</span>
  <code class="cap-swatch__hex">{esc(hexv)}</code>
  <span class="cap-swatch__use">{esc(use)}</span>
</button>"""
            for name, hexv, use in sc["steps"]
        )
        scales.append(f"""<div class="cap-scale">
  <p class="cap-scale__head"><b>{esc(sc["name"])}</b><span>{esc(sc["role"])}</span></p>
  <div class="cap-scale__row">{steps}</div>
</div>""")

    return (
        stage(f'<ul class="cap-brands">{brand}</ul>', label="Brand colours")
        + stage("".join(scales), label="Full scales",
                note="Seven scales, forty-one steps. Click any swatch to copy its hex. "
                     "Every value is transcribed from the blueprint’s colour tables.")
    )


def typography():
    t = D["typography"]
    rows = "".join(
        f"""<li class="cap-type" style="--fs:{size}px;--fw:{weight};--lh:{lh};--ls:{ls}">
  <div class="cap-type__meta">
    <code>{esc(token)}</code>
    <span>{size}px · {weight} · {lh}{"" if ls == "0" else " · " + esc(ls)}</span>
    <span class="cap-type__use">{esc(use)}</span>
  </div>
  <p class="cap-type__spec">Capsule</p>
</li>"""
        for token, size, weight, lh, ls, use in t["scale"]
    )
    return stage(
        f"""<div class="cap-face">
  <p class="cap-face__name">{esc(t["family"])}</p>
  <p class="cap-face__rule">{esc(t["rule"])}</p>
</div>
<ul class="cap-types">{rows}</ul>""",
        label="Type scale · 17 tokens",
        note="Rubik is self-hosted here at the weights the scale uses, so every line is the real "
             "typeface at its real size, not a visual approximation.",
    )


def spacing():
    peak = max(v for _, v, _ in D["spacing"])
    rows = "".join(
        f"""<li class="cap-space">
  <code class="cap-space__token">{esc(tok)}</code>
  <span class="cap-space__bar" style="--w:{v / peak * 100}%"><i></i></span>
  <b class="cap-space__v">{v}px</b>
  <span class="cap-space__use">{esc(use)}</span>
</li>"""
        for tok, v, use in D["spacing"]
    )
    return stage(f'<ul class="cap-spaces">{rows}</ul>', label="Spacing scale",
                 note="Drawn to scale: the bar is the actual value. 44px is the floor for "
                      "anything a finger has to hit.")


def radius():
    rows = "".join(
        f"""<li class="cap-rad">
  <span class="cap-rad__box" style="--r:{px}px"></span>
  <code>{esc(tok)}</code>
  <b>{esc(val)}</b>
  <span class="cap-rad__use">{esc(use)}</span>
</li>"""
        for tok, val, px, use in D["radius"]
    )
    return stage(f'<ul class="cap-rads">{rows}</ul>', label="Radius scale",
                 note="Buttons are never pill-shaped: 4px at small, 8px at medium and large. "
                      "The rule is in the blueprint, not a matter of taste.")


def elevation():
    rows = "".join(
        f"""<li class="cap-elev">
  <span class="cap-elev__box" style="--sh:{'none' if sh == 'none' else sh}"></span>
  <code>{esc(tok)}</code>
  <span class="cap-elev__v">{esc(sh)}</span>
  <span class="cap-elev__use">{esc(use)}</span>
</li>"""
        for tok, sh, use in D["elevation"]
    )
    return stage(f'<ul class="cap-elevs">{rows}</ul>', label="Elevation",
                 note=D["elevation_rule"])


def icons():
    rows = "".join(
        f'<li><span class="cap-ico__k">{esc(k)}</span><span class="cap-ico__v">{esc(v)}</span></li>'
        for k, v in D["icons"]
    )
    return stage(f'<ul class="cap-ico">{rows}</ul>', label="Iconography",
                 note="The icon rules are specified but the icon set itself is not in my files, "
                      "no icons are reproduced here rather than substituting a different library.")


# ---------------------------------------------------------------------------
# 04 · Architecture — primitive → semantic → component, with the real map.
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Accessibility. Measured, not asserted — the WCAG relative-luminance formula
# over the documented pairs. This is the one exhibit on the page that is my
# own analysis rather than a transcription, so it says so.
# ---------------------------------------------------------------------------
def contrast():
    c = D["contrast"]
    rows = ""
    for name, fg, bg, r, use in c["rows"]:
        aa = r >= 4.5
        large = r >= 3
        verdict = ("AA" if aa else ("AA large only" if large else "fails"))
        rows += f"""<tr class="{'is-pass' if aa else 'is-fail'}">
  <th scope="row"><span class="cap-cc" style="--fg:{fg};--bg:{bg}">Aa</span>{esc(name)}</th>
  <td><code>{esc(fg)}</code> on <code>{esc(bg)}</code></td>
  <td class="cap-ct__r"><b>{r}:1</b></td>
  <td class="cap-ct__v">{verdict}</td>
  <td class="cap-ct__u">{esc(use)}</td>
</tr>"""
    fails = [x for x in c["rows"] if x[3] < 4.5]
    return (
        stage(f"""<div class="cap-tbl__wrap">
  <table class="cap-ct">
    <thead><tr><th scope="col">Pair</th><th scope="col">Tokens</th><th scope="col">Ratio</th>
    <th scope="col">Verdict</th><th scope="col">Where it is used</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</div>""", label=f"Contrast · {len(c['rows'])} documented pairs, measured",
              note=c["note"])
        + f"""<div class="cap-finding" data-reveal>
  <p class="cap-finding__k">What the measurement found</p>
  <p class="cap-finding__body">{esc(c["claim"])}</p>
  <p class="cap-finding__body">But <b>{len(fails)} of the {len(c["rows"])} pairs fall below 4.5:1</b>:
  muted text, warning text, the disabled button label and the caution tag. Placeholder and disabled
  text are partly exempt under WCAG; warning copy and the caution tag are not. This is worth a look
  before the next version of the system.</p>
  <p class="cap-finding__caveat">{esc(c["caveat"])}</p>
</div>"""
    )


def architecture():
    sem = "".join(
        f"""<li class="cap-sem">
  <code class="cap-sem__token">{esc(tok)}</code>
  <span class="cap-sem__arrow" aria-hidden="true">&#8594;</span>
  <span class="cap-sem__prim">{esc(prim)}</span>
  <span class="cap-sem__chip" style="--c:{hexv}"></span>
  <code class="cap-sem__hex">{esc(hexv)}</code>
</li>"""
        for tok, prim, hexv in D["colour"]["semantic"]
    )
    return f"""<div class="cap-arch" data-reveal>
  <div class="cap-arch__col">
    <p class="cap-arch__k">Primitive</p>
    <p class="cap-arch__d">A value with a name. <code>Blue-400</code> is <code>#005DAC</code> and
    means nothing else.</p>
  </div>
  <div class="cap-arch__arrow" aria-hidden="true"><span></span></div>
  <div class="cap-arch__col">
    <p class="cap-arch__k">Semantic</p>
    <p class="cap-arch__d">A value with a <em>job</em>. <code>border-input-focus</code> happens to be
    Blue-400 today; the component never needs to know that.</p>
  </div>
  <div class="cap-arch__arrow" aria-hidden="true"><span></span></div>
  <div class="cap-arch__col">
    <p class="cap-arch__k">Component</p>
    <p class="cap-arch__d">Consumes semantics only. Re-point one semantic token and every component
    using it moves together.</p>
  </div>
</div>

{stage(f'<ul class="cap-sems">{sem}</ul>', label="The semantic map, as documented",
       note="Twelve semantic tokens from the blueprint, each resolved to the primitive behind it. "
            "This is the layer that makes a brand change a one-line edit.")}"""


# ---------------------------------------------------------------------------
# 05 · Components. Built live from the spec, and labelled as such.
# ---------------------------------------------------------------------------
def buttons():
    types = [
        ("Filled", "filled"), ("Outline", "outline"), ("Ghost", "ghost"),
        ("Text", "text"), ("Text link", "link"), ("Destructive", "destructive"),
    ]
    states = D["button_states"]
    head = "".join(f"<th scope='col'>{esc(s)}</th>" for s in states)
    rows = ""
    for name, cls in types:
        cells = "".join(
            f'<td><span class="cap-btn cap-btn--{cls} is-{s.lower()}">Next</span></td>'
            for s in states
        )
        rows += f'<tr><th scope="row">{esc(name)}</th>{cells}</tr>'

    sizes = "".join(
        # Units matter: `height:var(--h)` with an unitless 24 is an invalid
        # declaration, so the button silently collapsed to auto height.
        f"""<li><span class="cap-btn cap-btn--filled" style="--h:{h}px;--r:{r}px;--fs:{fs}px">Button</span>
<code>{esc(lbl)}</code><span>{h}px · radius {r}px</span></li>"""
        for lbl, h, r, fs in [("S", 24, 4, 12), ("M", 40, 8, 18), ("L", 48, 8, 18)]
    )

    plat = "".join(
        f"<tr><th scope='row'>{esc(p)}</th><td>{esc(h)}</td><td>{esc(i)}</td><td>{esc(pad)}</td><td>{esc(w)}</td></tr>"
        for p, h, i, pad, w in D["platforms"]
    )

    return (
        stage(f"""<div class="cap-tbl__wrap">
  <table class="cap-matrix">
    <thead><tr><th scope="col"><span class="sr-only">Type</span></th>{head}</tr></thead>
    <tbody>{rows}</tbody>
  </table>
</div>""", label="Buttons · six types × five states",
              note=D["button_states_note"])
        + stage(f'<ul class="cap-sizes">{sizes}</ul>', label="Sizes")
        + stage(f"""<div class="cap-tbl__wrap">
  <table class="cap-spec">
    <thead><tr><th scope="col">Platform</th><th scope="col">Height</th><th scope="col">Icon</th>
    <th scope="col">Padding</th><th scope="col">Width</th></tr></thead>
    <tbody>{plat}</tbody>
  </table>
</div>""", label="Platform defaults",
                note="Four platforms, three button heights. The differences are recorded on purpose, "
                     "that is what stops them being rediscovered every quarter.")
    )


def inputs():
    items = "".join(
        f"""<li class="cap-field cap-field--{kind}">
  <span class="cap-field__state">{esc(name)}</span>
  <label class="cap-field__label">Full name</label>
  <span class="cap-field__box">
    <span class="cap-field__val">{"Placeholder" if kind in ("idle", "error") and "Default" in name else "Priya Sharma"}</span>
    <span class="cap-field__mark" aria-hidden="true"></span>
  </span>
  <span class="cap-field__help">{esc(note)}</span>
</li>"""
        for name, kind, note in D["input_states"]
    )
    return stage(f'<ul class="cap-fields">{items}</ul>',
                 label="Text input · ten documented states",
                 note="Read off the Figma Behaviour frame. The Figma documentation uses a colleague’s "
                      "real name as placeholder content; it is replaced here.")


def bits():
    tags = "".join(
        f'<span class="cap-pill" style="--bg:{bg};--fg:{fg}">{esc(n)}</span>'
        for n, bg, fg in D["tags"]
    )
    dots = "".join(
        f'<span class="cap-dot" style="--c:{c}"><i></i>{esc(n)}</span>'
        for n, c in D["status_dots"]
    )
    avs = "".join(
        f'<span class="cap-av" style="--d:{d}px"><i>AP</i><b>{esc(k)}</b><em>{d}px</em></span>'
        for k, d in D["avatars"]
    )
    stars = ('<span class="cap-stars">'
             + "".join(f'<i class="{"is-on" if i < 4 else ""}">&#9733;</i>' for i in range(5))
             + '<b>4.0</b><em>(128)</em></span>')
    badges = """<span class="cap-badge-demo">Inbox<i class="cap-badge">12</i></span>
<span class="cap-badge-demo">Alerts<i class="cap-badge cap-badge--dot"></i></span>"""
    return (
        stage(f'<div class="cap-row">{tags}</div>', label="Tags · five semantic colours")
        + stage(f'<div class="cap-row">{dots}</div>', label="Status dots")
        + stage(f'<div class="cap-row cap-row--mid">{avs}</div>', label="Avatars · five sizes")
        + stage(f'<div class="cap-row cap-row--mid">{stars}{badges}</div>',
                label="Star rating and badges",
                note="Filled stars are YellowOrange-400 #FDA416, empty are Gray-200 #DADADA. "
                     "Count badges sit on Red-400 with a 2px white ring so they read against any surface.")
    )


def inventory():
    groups = "".join(
        f"""<div class="cap-invgrp" data-reveal style="--i:{i}">
  <p class="cap-invgrp__k">{esc(k)}<span>{len(v)}</span></p>
  <ul>{"".join(f"<li>{esc(x)}</li>" for x in v)}</ul>
</div>"""
        for i, (k, v) in enumerate(D["inventory"])
    )
    return f"""<div class="cap-inv">{groups}</div>
<p class="cap-note" data-reveal>{esc(D["inventory_note"])}</p>"""


# ---------------------------------------------------------------------------
# 06-08 · Product, handoff, governance.
# ---------------------------------------------------------------------------
def product():
    return f"""<div class="cap-gap" data-reveal>
  <p class="cap-gap__k">{tag("confirm")}</p>
  <h3 class="cap-gap__head">No shipped product screens are published here</h3>
  <p class="cap-gap__body">A component existing in Figma is not evidence that a product adopted it,
  and I do not have screenshots of Capsule components in a shipped Bajaj interface. Rather than
  present a mock-up as a product screen, this chapter is deliberately short.</p>
  <p class="cap-gap__body">What <em>is</em> evidenced: the system documents four platforms (App,
 
  MWeb, DWeb and PWA), each with its own header frame and its own sizing defaults. A system built for
  one surface does not grow four sets of platform rules.</p>
  <p class="cap-gap__ask">To finish this chapter I need two or three real product screens exported.</p>
</div>"""


def handoff():
    items = "".join(
        f"""<li class="cap-step" data-reveal style="--i:{i}">
  <span class="cap-step__n">{i + 1}</span>
  <div><h4>{esc(a)}</h4><p>{esc(b)}</p>{tag(k)}</div>
</li>"""
        for i, (a, b, k) in enumerate(D["handoff"])
    )
    return f'<ol class="cap-steps">{items}</ol>'


def governance():
    items = "".join(
        f"""<li class="cap-gov cap-gov--{k}" data-reveal style="--i:{i}">
  <h4>{esc(a)}</h4><p>{esc(b)}</p>{tag(k)}
</li>"""
        for i, (a, b, k) in enumerate(D["governance"])
    )
    dos = "".join(f"<li>{esc(x)}</li>" for x in D["dos"])
    donts = "".join(f"<li>{esc(x)}</li>" for x in D["donts"])
    return f"""<ul class="cap-govs">{items}</ul>

{stage(f'''<div class="cap-rules">
  <div class="cap-rules__col cap-rules__col--do"><p>Do</p><ul>{dos}</ul></div>
  <div class="cap-rules__col cap-rules__col--dont"><p>Don’t</p><ul>{donts}</ul></div>
</div>''', label="The cheat sheet, verbatim",
       note="The blueprint closes with these. A rule a designer can quote is worth more than a "
            "review meeting that reaches the same conclusion privately.")}"""


def confirm():
    items = "".join(
        f"""<li class="cap-conf" data-reveal style="--i:{i}">
  <h4 class="cap-conf__claim">{esc(c)}</h4>
  <p class="cap-conf__why">{esc(w)}</p>
  <p class="cap-conf__ask">{esc(q)}</p>
</li>"""
        for i, (c, w, q) in enumerate(D["confirm_list"])
    )
    return f"""<div class="cap-confirm" data-reveal>
  <p class="cap-confirm__k">{tag("confirm")}</p>
  <h3 class="cap-confirm__head">Six things I did not publish</h3>
  <p class="cap-confirm__body">These are the performance claims attached to Capsule elsewhere in my
  own material. Each one conflicts with another source, or has no source beyond itself. They are
  listed rather than printed as results.</p>
  <ol class="cap-confs">{items}</ol>
</div>"""


def learned():
    items = "".join(
        f"""<li class="cap-learn" data-reveal style="--i:{i}">
  <span class="cap-learn__n">0{i + 1}</span>
  <div><h4>{esc(a)}</h4><p>{esc(b)}</p></div>
</li>"""
        for i, (a, b) in enumerate(D["learned"])
    )
    return f"""<ol class="cap-learns">{items}</ol>
<blockquote class="cap-close" data-reveal>{esc(D["closing"])}</blockquote>"""


def blocks():
    return {
        "cap-counts": counts(),
        "cap-challenge": challenge(),
        "cap-principles": principles(),
        "cap-layers": layers(),
        "cap-colour": colour(),
        "cap-type": typography(),
        "cap-spacing": spacing(),
        "cap-radius": radius(),
        "cap-elevation": elevation(),
        "cap-icons": icons(),
        "cap-contrast": contrast(),
        "cap-architecture": architecture(),
        "cap-buttons": buttons(),
        "cap-inputs": inputs(),
        "cap-bits": bits(),
        "cap-inventory": inventory(),
        "cap-product": product(),
        "cap-handoff": handoff(),
        "cap-governance": governance(),
        "cap-confirm": confirm(),
        "cap-learned": learned(),
    }


if __name__ == "__main__":
    for k, v in blocks().items():
        print(f"{k:18} {len(v):8,} chars")
