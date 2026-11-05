#!/usr/bin/env python3
"""Render the Leadership chapters from ``leadership.json``.

The page is an editorial story rather than a case study, so these blocks are
deliberately unlike the ones in ``render.py``: a growth constellation, a photo
collage, a career map, an evidence wall. What they share with the rest of the
site is the rule that nothing is written twice — every figure, caption and
attribution on the page comes out of the JSON, which is also the evidence
inventory. If a claim is not in that file it cannot reach the page.

``blocks()`` returns ``{key: html}`` and ``_build.py`` substitutes
``<!--data:key-->`` in the fragment.
"""
import html
import json
import pathlib

HERE = pathlib.Path(__file__).parent
DATA = json.loads((HERE / "leadership.json").read_text(encoding="utf-8"))


def esc(s):
    """Escape, but leave the curly quotes and dashes the copy is written with."""
    return html.escape(str(s), quote=False)


def hue(name):
    """A chapter accent, taken straight from the hue ring in tokens.css.

    Deliberately not --accent: the Colour control re-points that, and this page
    is art-directed to stay warm whichever palette the reader picks.
    """
    return f"--lead-hue:var(--hue-{name});--lead-hue-deep:var(--hue-{name}-deep);--lead-hue-light:var(--hue-{name}-light)"


def kind_tag(kind, text=""):
    """The small provenance tag. A target never renders as a result."""
    words = {
        "recorded": "recorded",
        "snapshot": "snapshot",
        "target": "target — not a result",
        "proposal": "proposed",
        "voice": "from my notes",
    }
    label = words.get(kind, kind)
    extra = f" · {esc(text)}" if text else ""
    return f'<span class="lead-tag lead-tag--{kind}">{label}{extra}</span>'


# ---------------------------------------------------------------------------
# 02 · The growth constellation.
#
# One dot per designer, laid out as a cluster that gains mass year by year. The
# dots are a quantity, not a staff list, and the caption says so — the brief is
# explicit that a reader must never think they are looking at individuals.
# ---------------------------------------------------------------------------
def growth():
    rows = []
    peak = max(t["size"] for t in DATA["timeline"])
    for i, t in enumerate(DATA["timeline"]):
        dots = "".join(
            f'<span class="lead-dot" style="--d:{j}"></span>' for j in range(t["size"])
        )
        note = (
            f'<p class="lead-year__note">{esc(t["note"])}</p>' if t.get("note") else ""
        )
        width = round(t["size"] / peak * 100)
        rows.append(f"""
<li class="lead-year" data-reveal style="--i:{i};--fill:{width}%">
  <div class="lead-year__mark">
    <span class="lead-year__num">{esc(t["year"])}</span>
    <span class="lead-year__size" data-count="{t["size"]}">{t["size"]}</span>
    <span class="lead-year__unit">designers</span>
  </div>
  <div class="lead-year__body">
    <h3 class="lead-year__head">{esc(t["head"])}</h3>
    <p class="lead-year__text">{esc(t["body"])}</p>
    {note}
    <div class="lead-year__dots" aria-hidden="true">{dots}</div>
  </div>
</li>""")
    return f"""<div class="lead-growth">
  <ol class="lead-years">{"".join(rows)}</ol>
  <p class="lead-caption">Each dot is one designer in the count for that year — a quantity, not a person.
  Figures for 2019, 2022, 2023 and 2025 are recorded; 2020 and 2021 are read off the words
  “doubled” and the rituals year, and are shaped, not counted.</p>
</div>"""


# ---------------------------------------------------------------------------
# 03 · Two shapes of the same function, side by side, plus what the second one
# was for. The 2024 model is labelled a proposal because that is what the
# source is; the 2025 roster is what the shape looked like in use.
# ---------------------------------------------------------------------------
def model():
    sq = DATA["squads"]

    def panel(block):
        total = sum(g["count"] for g in block["groups"])
        groups = "".join(
            f"""<li class="lead-org__row">
  <span class="lead-org__name">{esc(g["name"])}</span>
  <span class="lead-org__bar" style="--n:{g["count"]};--of:{total}"><i></i></span>
  <span class="lead-org__n">{g["count"]}</span>
  <span class="lead-org__note">{esc(g["note"])}</span>
</li>"""
            for g in block["groups"]
        )
        return f"""<div class="lead-org" data-reveal>
  <p class="lead-org__label t-label">{esc(block["label"])}</p>
  <p class="lead-org__total"><span data-count="{total}">{total}</span> designers</p>
  <ul class="lead-org__rows">{groups}</ul>
  {kind_tag(block["kind"])}
</div>"""

    lines = "".join(
        f'<li class="lead-line"><span class="lead-line__dot"></span>{esc(l)}</li>'
        for l in sq["lines"]
    )
    obj = DATA["model_objectives"]
    cards = "".join(
        f"""<li class="lead-obj" data-reveal style="--i:{i}">
  <h4 class="lead-obj__head">{esc(a)}</h4>
  <p class="lead-obj__body">{esc(b)}</p>
</li>"""
        for i, (a, b) in enumerate(obj["items"])
    )
    mech = "".join(f"<li>{esc(m)}</li>" for m in obj["mechanics"])

    return f"""<div class="lead-shapes">
  {panel(sq["competency"])}
  <div class="lead-shapes__arrow" aria-hidden="true"><span></span></div>
  {panel(sq["hybrid"])}
</div>

<div class="lead-lines" data-reveal>
  <p class="lead-lines__label t-label">Drawn around four product lines</p>
  <ul class="lead-lines__list">{lines}</ul>
</div>

<div class="lead-model" data-reveal>
  <div class="lead-model__head">
    <h3 class="lead-model__title">{esc(obj["label"])}</h3>
    {kind_tag(obj["status"], obj["status_label"])}
  </div>
  <p class="lead-model__intro">What the reshape was actually for — six objectives, written down
  before anyone moved desk.</p>
  <ul class="lead-objs">{cards}</ul>
  <div class="lead-mech">
    <p class="lead-mech__label t-label">How it was meant to run</p>
    <ul class="lead-mech__list">{mech}</ul>
  </div>
</div>"""


# ---------------------------------------------------------------------------
# 04 · Culture. The collage comes first because the photographs are the point;
# the rituals are the mechanism underneath them.
# ---------------------------------------------------------------------------
def photos():
    ph = DATA["photos"]
    ann = DATA["annotations"]
    cells = []
    for i, p in enumerate(ph):
        # Where the subject sits in the frame. Without this a centred crop puts
        # the Karjat group, who are at the bottom of a tall photograph, out of shot.
        pos = f';--pos:{p["pos"]}' if p.get("pos") else ""
        note = ""
        if i == 1 and len(ann) > 0:
            note = f'<span class="lead-scrawl lead-scrawl--a">{esc(ann[0])}</span>'
        if i == 4 and len(ann) > 1:
            note = f'<span class="lead-scrawl lead-scrawl--b">{esc(ann[1])}</span>'
        cells.append(f"""
<figure class="lead-shot lead-shot--{i}" data-reveal style="{hue(p["hue"])};--i:{i}{pos}">
  <img src="../../assets/img/leadership/{p["file"]}" alt="{esc(p["alt"])}" loading="lazy" decoding="async">
  <figcaption class="lead-shot__cap"><span>{esc(p["cap"])}</span></figcaption>
  {note}
</figure>""")
    return f"""<div class="lead-collage">{"".join(cells)}</div>
<p class="lead-caption lead-caption--wide">{esc(DATA["photos_note"])}
{esc(ann[2]) if len(ann) > 2 else ""}</p>"""


def rituals():
    items = "".join(
        f"""<li class="lead-ritual" data-reveal style="{hue(r["hue"])};--i:{i}">
  <span class="lead-ritual__cadence t-label">{esc(r["cadence"])}</span>
  <h4 class="lead-ritual__name">{esc(r["name"])}</h4>
  <p class="lead-ritual__line">{esc(r["line"])}</p>
</li>"""
        for i, r in enumerate(DATA["rituals"])
    )
    rule = DATA["rule"]
    no = "".join(f"<li>{esc(x)}</li>" for x in rule["no"])
    yes = "".join(f"<li>{esc(x)}</li>" for x in rule["yes"])
    return f"""<ul class="lead-rituals">{items}</ul>

<div class="lead-rule" data-reveal>
  <p class="lead-rule__label t-label">One rule I accidentally enforced</p>
  <blockquote class="lead-rule__quote">{esc(rule["line"])}</blockquote>
  <div class="lead-rule__cols">
    <div class="lead-rule__col lead-rule__col--no">
      <p class="t-label">Not this</p><ul>{no}</ul>
    </div>
    <div class="lead-rule__col lead-rule__col--yes">
      <p class="t-label">This</p><ul>{yes}</ul>
    </div>
  </div>
</div>"""


def sessions():
    s = DATA["sessions"]
    stats = "".join(
        f'<div class="lead-stat"><p class="lead-stat__v" data-count-text="{esc(v)}">{esc(v)}</p>'
        f'<p class="lead-stat__l t-label">{esc(l)}</p></div>'
        for v, l in s["stats"]
    )
    items = "".join(
        f"""<li class="lead-session" data-reveal style="--i:{i}">
  <h4 class="lead-session__name">{esc(name)}</h4>
  <span class="lead-session__att t-label">{esc(att)}</span>
  <p class="lead-session__out">{esc(out)}</p>
</li>"""
        for i, (name, att, out) in enumerate(s["items"])
    )
    return f"""<div class="lead-sessions" data-reveal>
  <div class="lead-sessions__stats">{stats}</div>
  <blockquote class="lead-sessions__rule">{esc(s["rule"])}</blockquote>
  <ul class="lead-sessions__list">{items}</ul>
  <p class="lead-caption">{esc(s["note"])}</p>
</div>"""


# ---------------------------------------------------------------------------
# 05 · The award. One loud moment, then the three phases that led to it — and
# an explicit note that the page is not claiming a cause.
# ---------------------------------------------------------------------------
def award():
    a = DATA["award"]
    phases = "".join(
        f"""<li class="lead-phase" data-reveal style="--i:{i}">
  <span class="lead-phase__n">{i + 1}</span>
  <h4 class="lead-phase__name">{esc(name)}</h4>
  <p class="lead-phase__body">{esc(body)}</p>
</li>"""
        for i, (name, body) in enumerate(a["phases"])
    )
    nots = "".join(f"<li>{esc(x)}</li>" for x in a["why_not"])
    return f"""<div class="lead-award" data-reveal>
  <div class="lead-award__plate">
    <p class="lead-award__event t-label">{esc(a["event"])}</p>
    <p class="lead-award__name">{esc(a["name"])}</p>
    <p class="lead-award__line">{esc(a["line"])}</p>
    <p class="lead-award__second">Alongside it that year — {esc(a["second"])}.</p>
  </div>
  <figure class="lead-award__shot">
    <img src="../../assets/img/leadership/aop-night.jpg"
         alt="The design team together at the AOP awards night." loading="lazy" decoding="async">
  </figure>
</div>

<ol class="lead-phases">{phases}</ol>

<div class="lead-why" data-reveal>
  <div class="lead-why__col lead-why__col--no"><p class="t-label">Not why we won</p><ul>{nots}</ul></div>
  <div class="lead-why__col lead-why__col--yes"><p class="t-label">Why we won</p><p class="lead-why__line">{esc(a["why"])}</p></div>
</div>
<p class="lead-caption">{esc(a["caution"])}</p>"""


# ---------------------------------------------------------------------------
# 06 · Growing people. The career map is the one genuinely interactive piece:
# five tracks, four rungs each, expanded one at a time. Everything is in the
# markup, so it reads perfectly with JavaScript off — the script only collapses
# what is already there.
# ---------------------------------------------------------------------------
def ladder():
    L = DATA["ladder"]
    bands = "".join(f'<span class="lead-band">{esc(b)}</span>' for b in L["bands"])
    tracks = []
    for ti, t in enumerate(L["tracks"]):
        steps = "".join(
            f"""<li class="lead-step" style="--i:{i}">
  <span class="lead-step__lvl t-label">{esc(L["levels"][i][0])} <i>{esc(L["levels"][i][1])}</i></span>
  <h5 class="lead-step__name">{esc(name)}</h5>
  <p class="lead-step__body">{esc(body)}</p>
</li>"""
            for i, (name, body) in enumerate(t["steps"])
        )
        tracks.append(f"""
<div class="lead-track" style="{hue(t["hue"])};--i:{ti}" data-track="{ti}" data-reveal>
  <button class="lead-track__head" type="button" data-track-toggle="{ti}"
          aria-expanded="{'true' if ti == 0 else 'false'}" aria-controls="track-{ti}">
    <span class="lead-track__name">{esc(t["name"])}</span>
    <span class="lead-track__blurb">{esc(t["blurb"])}</span>
    <span class="lead-track__chev" aria-hidden="true"></span>
  </button>
  <ol class="lead-track__steps" id="track-{ti}">{steps}</ol>
</div>""")
    return f"""<div class="lead-ladder" data-reveal>
  <div class="lead-ladder__head">
    <h3 class="lead-ladder__title">{esc(L["label"])}</h3>
    <div class="lead-bands">{bands}</div>
  </div>
  <p class="lead-ladder__attrib">{esc(L["attrib"])}</p>
  <div class="lead-tracks">{"".join(tracks)}</div>
</div>"""


def rise():
    r = DATA["rise"]
    steps = "".join(
        f"""<li class="lead-rise__step" data-reveal style="--i:{i}">
  <span class="lead-rise__n">{i + 1}</span>
  <h5 class="lead-rise__name">{esc(name)}</h5>
  <p class="lead-rise__body">{esc(body)}</p>
</li>"""
        for i, (name, body) in enumerate(r["cycle"])
    )
    scale = "".join(
        f'<li><span class="lead-scale__n">{i + 1}</span>{esc(s)}</li>'
        for i, s in enumerate(r["scale"])
    )
    t = r["target"]
    return f"""<div class="lead-rise" data-reveal>
  <div class="lead-rise__head">
    <h3 class="lead-rise__title">{esc(r["name"])}</h3>
    <p class="lead-rise__expand">{esc(r["expand"])}</p>
  </div>
  <p class="lead-ladder__attrib">{esc(r["attrib"])}</p>
  <ol class="lead-rise__cycle">{steps}</ol>
  <div class="lead-rise__foot">
    <ul class="lead-scale">{scale}</ul>
    <div class="lead-target">
      <p class="lead-target__v">{esc(t["value"])}</p>
      <p class="lead-target__l">{esc(t["label"])}</p>
      {kind_tag(t["kind"])}
      <p class="lead-target__warn">{esc(t["warn"])}</p>
    </div>
  </div>
</div>"""


def skills():
    s = DATA["skills"]
    head = "".join(f"<th scope=\"col\"><span>{esc(a)}</span></th>" for a in s["axes"])
    rows = []
    for r in s["roles"]:
        cells = "".join(
            f'<td><span class="lead-pip" style="--v:{v};--max:{s["max"]}" '
            f'title="{v} of {s["max"]}"><i></i></span><b>{v}</b></td>'
            for v in r["vals"]
        )
        rows.append(
            f'<tr style="{hue(r["hue"])}"><th scope="row">{esc(r["name"])}</th>{cells}</tr>'
        )
    return f"""<div class="lead-skills" data-reveal>
  <h3 class="lead-skills__title">{esc(s["label"])}</h3>
  <p class="lead-ladder__attrib">{esc(s["attrib"])}</p>
  <div class="lead-skills__wrap">
    <table class="lead-matrix">
      <thead><tr><th scope="col"><span class="sr-only">Role</span></th>{head}</tr></thead>
      <tbody>{"".join(rows)}</tbody>
    </table>
  </div>
  <p class="lead-caption">The number is the level that role was expected to reach, one to five.
  It is a definition of “good”, not a score anyone was given.</p>
</div>"""


# ---------------------------------------------------------------------------
# 07 · The evidence wall. Every tile carries its own source and qualification,
# because a number on a portfolio without either is just decoration.
# ---------------------------------------------------------------------------
def numbers():
    tiles = "".join(
        f"""<li class="lead-num" data-reveal style="{hue(n["hue"])};--i:{i}">
  <p class="lead-num__v"><span data-count-text="{esc(n["value"])}">{esc(n["value"])}</span><i>{esc(n["unit"])}</i></p>
  <p class="lead-num__l">{esc(n["label"])}</p>
  <p class="lead-num__q">{esc(n["qual"])}</p>
  <p class="lead-num__s">{kind_tag(n["kind"])}<span class="lead-num__src">{esc(n["src"])}</span></p>
</li>"""
        for i, n in enumerate(DATA["numbers"])
    )
    return f"""<ul class="lead-nums">{tiles}</ul>
<p class="lead-caption lead-caption--wide">{esc(DATA["numbers_note"])}</p>"""


def restricted():
    r = DATA["restricted"]
    head, *body = r["rows"]
    th = "".join(f"<th scope=\"col\">{esc(c)}</th>" for c in head)
    tr = "".join(
        "<tr>" + "".join(f"<td>{esc(c)}</td>" for c in row) + "</tr>" for row in body
    )
    return f"""<div class="lead-locked" data-reveal>
  <div class="lead-locked__head">
    <span class="lead-locked__pill t-label">{esc(r["title"])}</span>
    <p class="lead-locked__line">{esc(r["line"])}</p>
  </div>
  <div class="lead-locked__plate" aria-hidden="true">
    <table class="lead-locked__table"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>
  </div>
  <p class="lead-locked__note">{esc(r["note"])}</p>
  <p class="lead-locked__status">{esc(r["status"])}</p>
</div>"""


# ---------------------------------------------------------------------------
# 08 · Five principles, set as editorial statements rather than a card grid.
# ---------------------------------------------------------------------------
def principles():
    items = "".join(
        f"""<li class="lead-prin" data-reveal style="{hue(p["hue"])};--i:{i}">
  <span class="lead-prin__n">{esc(p["n"])}</span>
  <div class="lead-prin__body">
    <h3 class="lead-prin__title">{esc(p["title"])}</h3>
    <p class="lead-prin__text">{esc(p["body"])}</p>
    <blockquote class="lead-prin__pull">{esc(p["pull"])}</blockquote>
  </div>
</li>"""
        for i, p in enumerate(DATA["principles"])
    )
    return f'<ol class="lead-prins">{items}</ol>'


# ---------------------------------------------------------------------------
# 09 · The way out. Forward-looking, and it hands the reader somewhere to go.
# ---------------------------------------------------------------------------
def closing():
    c = DATA["closing"]
    links = "".join(
        f"""<a class="lead-next" href="{href}">
  <span class="lead-next__name">{esc(name)}</span>
  <span class="lead-next__note">{esc(note)}</span>
  <span class="lead-next__arrow" aria-hidden="true">&#8594;</span>
</a>"""
        for name, href, note in c["links"]
    )
    return f"""<div class="lead-close" data-reveal>
  <figure class="lead-close__shot">
    <img src="../../assets/img/leadership/team-selfie.jpg"
         alt="The design team pressed into one frame, everyone grinning." loading="lazy" decoding="async">
  </figure>
  <div class="lead-close__body">
    <h3 class="lead-close__head">{esc(c["head"])}</h3>
    <p class="lead-close__text">{esc(c["body"])}</p>
    <blockquote class="lead-close__sign">{esc(c["sign"])}</blockquote>
    <div class="lead-close__links">{links}</div>
  </div>
</div>"""


def blocks():
    return {
        "lead-growth": growth(),
        "lead-model": model(),
        "lead-photos": photos(),
        "lead-rituals": rituals(),
        "lead-sessions": sessions(),
        "lead-award": award(),
        "lead-ladder": ladder(),
        "lead-rise": rise(),
        "lead-skills": skills(),
        "lead-numbers": numbers(),
        "lead-restricted": restricted(),
        "lead-principles": principles(),
        "lead-closing": closing(),
    }


if __name__ == "__main__":
    for k, v in blocks().items():
        print(f"{k:18} {len(v):7,} chars")
