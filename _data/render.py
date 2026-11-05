"""Turn ``planning.json`` into HTML blocks the build drops into the page.

The page fragment holds placeholders like ``<!--data:alloc-matrix-->``; the build
calls :func:`blocks` and substitutes each one. Keeping the markup here means the
page stays readable prose and the data never gets hand-copied into HTML -- rerun
``extract.py`` and every table, grid and matrix on the page moves with it.
"""
import datetime
import html
import json
from collections import Counter, OrderedDict
from pathlib import Path

DATA = Path(__file__).parent / "planning.json"

# The snapshot wrote status in free text, so the same state arrives spelled
# several ways. These groups drive the colour of the indicator only; every row
# still shows the sheet's own wording.
STATUS_GROUPS = OrderedDict([
    ("done", ["completed"]),
    ("closed", ["ui closed", "ux closed", "ux approved", "approved. scenarios ip"]),
    ("review", ["in review", "waiting for approval", "in documentation"]),
    ("live", ["in progress", "ux in progress", "dweb in progress", "ui is pending"]),
    ("hold", ["on hold"]),
    ("todo", ["to pick", "to be picked", "yet to pick", "yet to begin"]),
])
GROUP_LABEL = {"done": "Completed", "closed": "Stage closed", "review": "In review",
               "live": "In progress", "hold": "On hold", "todo": "Not started",
               "none": "Not recorded"}


def e(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def dash(v):
    """A source cell that is empty, or literally a dash, renders as a dash."""
    s = str(v or "").strip()
    return "" if s in ("", "-", "–", "—") else s


def group_of(status):
    s = dash(status).lower()
    if not s:
        return "none"
    for g, members in STATUS_GROUPS.items():
        if s in members:
            return g
    return "live" if "progress" in s else "none"


def load():
    return json.loads(DATA.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# A. the allocation matrix
# --------------------------------------------------------------------------- #
def alloc_matrix(d):
    recs = d["allocation"]["records"]
    squads = sorted({r["squad"] for r in recs if r["squad"]}, key=str.lower)
    groups = [g for g in list(STATUS_GROUPS) + ["none"]
              if any(group_of(r["status"]) == g for r in recs)]

    def opt(v, label=None):
        return '<option value="%s">%s</option>' % (e(v), e(label or v))

    head = """<div class="sheet__controls">
  <label class="sheet__filter"><span>Squad</span>
    <select data-filter="squad">%s</select></label>
  <label class="sheet__filter"><span>Discipline</span>
    <select data-filter="band"><option value="">All</option>%s</select></label>
  <label class="sheet__filter"><span>Status</span>
    <select data-filter="group"><option value="">All</option>%s</select></label>
  <p class="sheet__count" data-sheet-count aria-live="polite"></p>
</div>""" % (
        '<option value="">All</option>' + "".join(opt(s) for s in squads),
        "".join(opt(b) for b in ("UX", "UI")),
        "".join(opt(g, GROUP_LABEL[g]) for g in groups),
    )

    rows = []
    for r in recs:
        g = group_of(r["status"])
        band = r["owner"].split()[0] if r["owner"][:2] in ("UX", "UI") else ""
        rows.append(
            '<tr data-squad="%s" data-band="%s" data-group="%s">'
            '<td class="sheet__id" data-label="Story ID">%s</td>'
            '<td class="sheet__story" data-label="Story / requirement">%s</td>'
            '<td data-label="Squad"><span class="tag">%s</span></td>'
            '<td data-label="UX / UI assigned">%s</td>'
            '<td data-label="PM">%s</td>'
            '<td class="sheet__status" data-label="Design stage status">'
            '<i class="dot dot--%s" aria-hidden="true"></i>%s</td>'
            '<td data-label="Start">%s</td>'
            '<td data-label="Target design delivery">%s</td></tr>' % (
                e(r["squad"]), e(band), e(g),
                e(dash(r["story_id"])) or "&mdash;",
                e(r["story"]),
                e(r["squad"]),
                e(r["owner"]),
                e(dash(r["pm"])) or "&mdash;",
                g, e(dash(r["status"])) or "&mdash;",
                e(dash(r["start"])) or "&mdash;",
                e(dash(r["target"])) or "&mdash;",
            ))

    legend = " ".join(
        '<span class="legend__k"><i class="dot dot--%s" aria-hidden="true"></i>%s</span>'
        % (g, e(GROUP_LABEL[g]))
        for g in groups)

    return """%s
<div class="sheet__wrap">
<table class="sheet" data-sheet>
  <caption class="sheet__cap">July allocation snapshot &mdash; %d work items across %d squads,
  one row per item, exactly as the sheet recorded them.</caption>
  <thead><tr>
    <th scope="col">Story ID</th><th scope="col">Story / requirement</th>
    <th scope="col">Squad</th><th scope="col">Assigned</th><th scope="col">PM</th>
    <th scope="col">Design stage status</th><th scope="col">Start</th>
    <th scope="col">Target delivery</th>
  </tr></thead>
  <tbody>%s</tbody>
</table>
</div>
<p class="legend">%s</p>
<p class="sheet__empty" data-sheet-empty hidden>No rows match that combination.</p>""" % (
        head, len(recs), len({r["squad"].lower() for r in recs if r["squad"]}),
        "\n".join(rows), legend)


def alloc_fill(d):
    """How complete the snapshot actually was, counted not estimated."""
    recs = d["allocation"]["records"]
    n = len(recs)
    fields = [("Squad", "squad"), ("Design stage status", "status"),
              ("Target delivery date", "target"), ("Start date", "start"),
              ("Product manager", "pm"), ("Story ID", "story_id")]
    out = []
    for label, k in fields:
        filled = sum(1 for r in recs if dash(r[k]))
        pct = round(filled / n * 100)
        out.append(
            '<li class="fill__row"><span class="fill__name">%s</span>'
            '<span class="fill__bar"><i style="width:%d%%"></i></span>'
            '<span class="fill__num">%d<span class="fill__of">/%d</span></span></li>'
            % (e(label), pct, filled, n))
    return ('<ul class="fill">%s</ul>\n<p class="note">Counted from the %d rows, not '
            'estimated. The gaps are the honest part: squad and status were kept up, '
            'dates and story IDs were not.</p>' % ("\n".join(out), n))


# --------------------------------------------------------------------------- #
# B. the template behind the snapshot
# --------------------------------------------------------------------------- #
def alloc_schema(d):
    a = d["allocation"]
    ex = {f["name"]: f["value"] for f in a["exemplar"]["fields"]}

    rows = []
    for f in a["fields"]:
        name = f["name"]
        short = name.split("(")[0].strip()
        hint = name[len(short):].strip(" ()") if "(" in name else ""
        rows.append(
            '<tr><th scope="row">%s%s</th><td>%s</td></tr>' % (
                e(short),
                '<span class="spec__hint">%s</span>' % e(hint) if hint else "",
                e(dash(ex.get(name, ""))) or '<span class="spec__none">empty</span>'))

    stages = "".join(
        '<li class="pipe__stage"><span class="pipe__n">%d</span>'
        '<span class="pipe__name">%s</span><span class="pipe__val">%s</span></li>' % (
            i, e(s["name"]), e(dash(s["value"])) or "&mdash;")
        for i, s in enumerate(a["exemplar"]["stages"], start=1))

    vocab = "".join(
        '<div class="vocab__set"><h4>%s</h4><p>%s</p></div>' % (
            e(k), "".join('<span class="tag">%s</span>' % e(v) for v in vals))
        for k, vals in a["vocab"].items())

    return """<div class="spec">
  <div class="spec__col">
    <h3 class="spec__title">The record</h3>
    <p class="spec__sub">Every field the template asks for, with the one worked row
    the workbook ships &mdash; the only record anywhere that fills them all.</p>
    <table class="spec__table">
      <caption class="sr-only">Allocation template fields, with the values from the
      workbook's one worked row</caption>
      <tbody>%s</tbody></table>
  </div>
  <div class="spec__col">
    <h3 class="spec__title">The five design stages</h3>
    <p class="spec__sub">A story is tracked through these, not through one status
    field. Values shown are the worked row's.</p>
    <ol class="pipe">%s</ol>
    <h3 class="spec__title spec__title--gap">Controlled vocabulary</h3>
    <p class="spec__sub">Dropdown lists parked off to the right of the sheet, so two
    people filling a row chose from the same words.</p>
    <div class="vocab">%s</div>
  </div>
</div>""" % ("\n".join(rows), stages, vocab)


# --------------------------------------------------------------------------- #
# C. availability
# --------------------------------------------------------------------------- #
def availability(d):
    v = d["availability"]
    months, cells = v["months"], v["rows"]

    spans, last = [], None
    for m in months:
        if m != last:
            spans.append([m, 0])
            last = m
        spans[-1][1] += 1
    head = "".join('<th scope="col" colspan="%d">%s</th>' % (n, e(m or "&mdash;"))
                   for m, n in spans)

    label = {"available": "available", "leave": "leave", "partial": "part week",
             "": "not filled in"}
    body = []
    for row in cells:
        tiles = "".join(
            '<td class="heat heat--%s"><span class="sr-only">%s</span></td>'
            % (c or "blank", label[c]) for c in row["cells"])
        body.append(
            '<tr%s><th scope="row" class="heat__who">%s'
            '<span class="heat__squad">%s</span></th>%s</tr>' % (
                ' class="heat__me"' if row.get("self") else "",
                e(row["res"]), e(dash(row["squad"])) or "&mdash;", tiles))

    t = v["tally"]
    known = t["available"] + t["leave"] + t["partial"]
    legend = "".join(
        '<span class="legend__k"><i class="swatch swatch--%s" aria-hidden="true"></i>%s</span>'
        % (k, e(lbl))
        for k, lbl in (("available", "Available"), ("partial", "Part week away"),
                       ("leave", "Leave"), ("blank", "Not filled in")))

    return """<div class="heat__wrap">
<table class="heatmap">
  <caption class="sheet__cap">Weekly availability tracker, %s &mdash; %d people &times; %d
  week columns. Dates are deliberately stripped: a week someone was partly away reads
  as &ldquo;part week&rdquo;, never as which days.</caption>
  <thead>
    <tr><td class="heat__corner"></td>%s</tr>
  </thead>
  <tbody>%s</tbody>
</table>
</div>
<p class="legend">%s</p>
<p class="note">%d of the %d cells were ever filled in. That is the tracker's real
coverage, and the reason it answered &ldquo;who is around next week&rdquo; well and
never answered &ldquo;how loaded is this person&rdquo; at all &mdash; no sheet here
records capacity, hours or estimates, so no utilisation figure is derivable.</p>""" % (
        e(v["span"]), len(cells), len(v["weeks"]), head, "\n".join(body), legend,
        known, known + t[""])


# --------------------------------------------------------------------------- #
# D. squad distribution + timeline
# --------------------------------------------------------------------------- #
def squad_load(d):
    recs = d["allocation"]["records"]
    # 'DRx' and 'Drx' are the same squad typed two ways; counted as one, noted below.
    counts = Counter()
    display = {}
    for r in recs:
        if not r["squad"]:
            continue
        k = r["squad"].lower()
        counts[k] += 1
        display.setdefault(k, r["squad"])
    top = counts.most_common()
    peak = top[0][1]
    bars = "".join(
        '<li class="bars__row"><span class="bars__name">%s</span>'
        '<span class="bars__bar"><i style="width:%.1f%%"></i></span>'
        '<span class="bars__n">%d</span></li>' % (
            e(display[k]), n / peak * 100, n)
        for k, n in top)
    return ('<ul class="bars">%s</ul>\n<p class="note">Work items recorded per squad in '
            'this one snapshot, counted from the %d rows. A count of open items is not a '
            'measure of load &mdash; the sheet holds no estimates &mdash; so read this as '
            'spread, not as capacity. <span class="tag">DRx</span> and '
            '<span class="tag">Drx</span> are the same squad typed two ways and are '
            'counted once.</p>' % (bars, len(recs)))


def timeline(d):
    recs = [r for r in d["allocation"]["records"] if r["start_iso"] or r["target_iso"]]
    iso = datetime.date.fromisoformat
    days = [iso(x) for r in recs for x in (r["start_iso"], r["target_iso"]) if x]
    lo, hi = min(days), max(days)
    span = (hi - lo).days or 1

    def pos(day):
        return (iso(day) - lo).days / span * 100

    both = [r for r in recs if r["start_iso"] and r["target_iso"]]
    rows = []
    for r in sorted(recs, key=lambda r: (r["start_iso"] or r["target_iso"], r["story"])):
        g = group_of(r["status"])
        if r["start_iso"] and r["target_iso"]:
            a, b = pos(r["start_iso"]), pos(r["target_iso"])
            mark = ('<span class="gantt__bar gantt__bar--%s" style="left:%.2f%%;'
                    'width:%.2f%%"></span>' % (g, a, max(b - a, 1.2)))
        elif r["start_iso"]:
            mark = ('<span class="gantt__tick gantt__tick--start gantt__tick--%s" '
                    'style="left:%.2f%%"></span>' % (g, pos(r["start_iso"])))
        else:
            mark = ('<span class="gantt__tick gantt__tick--end gantt__tick--%s" '
                    'style="left:%.2f%%"></span>' % (g, pos(r["target_iso"])))
        rows.append(
            '<li class="gantt__row"><span class="gantt__label">%s'
            '<span class="gantt__meta">%s &middot; %s</span></span>'
            '<span class="gantt__track">%s</span></li>' % (
                e(r["story"][:54]), e(r["squad"]), e(r["owner"]), mark))

    weeks = []
    cur = lo - datetime.timedelta(days=lo.weekday())
    while cur <= hi:
        if cur >= lo:
            weeks.append('<span class="gantt__week" style="left:%.2f%%">%s</span>'
                         % ((cur - lo).days / span * 100, cur.strftime("%-d %b")))
        cur += datetime.timedelta(days=7)

    return """<div class="gantt">
  <div class="gantt__axis"><span class="gantt__label"></span>
    <span class="gantt__track">%s</span></div>
  <ol class="gantt__rows">%s</ol>
</div>
<p class="legend"><span class="legend__k"><i class="swatch swatch--bar" aria-hidden="true"></i>Start
and target both recorded</span><span class="legend__k"><i class="gantt__tick gantt__tick--start"
aria-hidden="true" style="position:static;transform:none"></i>Start only</span>
<span class="legend__k"><i class="gantt__tick gantt__tick--end" aria-hidden="true"
style="position:static;transform:none"></i>Target only</span></p>
<p class="note">Every dated row in the snapshot, %s to %s. %d of the %d work items carry
any date at all and only %d carry both, which is why this is drawn as the sparse thing it
was rather than as a full plan. Dates are the targets the sheet held; no sheet records
what actually shipped.</p>""" % (
        "".join(weeks), "\n".join(rows), lo.strftime("%-d %B %Y"), hi.strftime("%-d %B %Y"),
        len(recs), len(d["allocation"]["records"]), len(both))


# --------------------------------------------------------------------------- #
# E. OKRs
# --------------------------------------------------------------------------- #
def okr_frameworks(d):
    def side(fw, extra=""):
        themes = "".join(
            '<li class="fw__theme"><span class="fw__name">%s</span>%s'
            '<span class="fw__tracks">%s</span></li>' % (
                e(t["name"]),
                '<span class="fw__blurb">%s</span>' % e(t["blurb"]) if t["blurb"] else "",
                "".join('<span class="tag">%s</span>' % e(tr["name"]) for tr in t["tracks"])
                or '<span class="spec__none">no tracks listed</span>')
            for t in fw["themes"])
        return """<div class="fw%s">
  <h3 class="fw__title">%s</h3>
  <p class="fw__src">%s</p>
  <ol class="fw__themes">%s</ol>
</div>""" % (extra, e(fw["label"]), e(fw["source"]), themes)

    a, b = d["okr"]["a"], d["okr"]["b"]
    names_a = {t["name"].lower() for t in a["themes"]}
    names_b = {t["name"].lower() for t in b["themes"]}
    return """<div class="fw__pair">%s%s</div>
<p class="note">Two workbooks, two framework versions, shown side by side rather than
merged. The later one splits <span class="tag">AI in Design</span> out into a theme of its
own and reshapes the team theme into <span class="tag">Talent</span>; %d themes becomes
%d, and %d sub-tracks becomes %d. Which revision was finally adopted is not recorded in
either file, so neither is presented as the framework.</p>""" % (
        side(a), side(b, " fw--b"), len(names_a), len(names_b),
        sum(len(t["tracks"]) for t in a["themes"]),
        sum(len(t["tracks"]) for t in b["themes"]))


def okr_cascade(d):
    a = d["okr"]["a"]
    themes = a["themes"]
    cols = []
    bounds = []
    for t in themes:
        letters = [tr["col"] for tr in t["tracks"]]
        bounds.append((t, letters))
        cols.extend(letters)

    filled = [r for r in a["cascade"] if r["filled"]]
    blank = [r for r in a["cascade"] if not r["filled"]]

    head = "".join('<th scope="col">%s<span class="cascade__tracks">%s</span></th>' % (
        e(t["name"]), e(" &middot; ".join(tr["name"] for tr in t["tracks"])))
        for t, _ls in bounds)

    body = []
    for r in filled:
        tds = []
        for t, letters in bounds:
            bits = [r["entries"][c] for c in letters if c in r["entries"]]
            if bits:
                tds.append('<td><ul class="cascade__items">%s</ul></td>' %
                           "".join("<li>%s</li>" % e(x) for x in bits))
            else:
                tds.append('<td class="cascade__gap"><span class="sr-only">not set</span></td>')
        body.append('<tr%s><th scope="row">%s</th>%s</tr>' % (
            ' class="cascade__me"' if r["self"] else "", e(r["who"]), "".join(tds)))

    return """<div class="cascade__wrap">
<table class="cascade">
  <caption class="sheet__cap">Objective cascade, in the workbook's own words &mdash;
  five themes across, one row per person, names replaced by role labels.</caption>
  <thead><tr><th scope="col" class="cascade__corner">Role</th>%s</tr></thead>
  <tbody>%s</tbody>
</table>
</div>
<p class="note">%d of the %d rows in that sheet carry entries; %d were opened for a person
and never filled. The blanks are left visible because a half-filled cascade is what the
file actually holds. Each cell states a commitment and, after the arrow, the target the
sheet set for it &mdash; no column anywhere records an outcome, so nothing here is a
result.</p>""" % (head, "\n".join(body), len(filled), len(a["cascade"]), len(blank))


def okr_mine(d):
    m = d["okr"]["mine"]
    themes, tracks = m["themes"], m["tracks"]
    span = {}
    order = [t["col"] for t in tracks]
    for i, th in enumerate(themes):
        nxt = themes[i + 1]["col"] if i + 1 < len(themes) else None
        start = order.index(th["col"]) if th["col"] in order else 0
        end = order.index(nxt) if nxt in order else len(order)
        span[th["col"]] = (start, max(end - start, 1))

    th_row = "".join('<th scope="col" colspan="%d">%s</th>' % (n, e(t["name"]))
                     for t in themes for _s, n in [span[t["col"]]])
    tr_row = "".join('<th scope="col" class="qm__track">%s</th>' % e(t["name"]) for t in tracks)

    body = []
    for q in m["quarters"]:
        tds = []
        for t in tracks:
            items = q["items"].get(t["col"], [])
            tds.append('<td>%s</td>' % (
                '<ul class="qm__items">%s</ul>' % "".join("<li>%s</li>" % e(x) for x in items)
                if items else '<span class="sr-only">nothing set</span>'))
        body.append('<tr><th scope="row" class="qm__q">%s</th>%s</tr>'
                    % (e(q["name"]), "".join(tds)))

    return """<div class="qm__wrap">
<table class="qm">
  <caption class="sheet__cap">My own sheet from the same workbook: eleven sub-tracks
  across, two quarters down, verbatim.</caption>
  <thead><tr><td class="qm__corner"></td>%s</tr>
         <tr><td class="qm__corner"></td>%s</tr></thead>
  <tbody>%s</tbody>
</table>
</div>
<p class="note">Both quarters are plans. The sheet has no column for what landed, and two
of its targets are written with a literal question mark where the number should be, so
every line here is a commitment made, not a result claimed. <span class="tag">Team
Allocation Status</span> and <span class="tag">Weekly Leave Tracker</span> appear as my
own key results under Delivery Excellence &mdash; the two artefacts above are the
deliverable, which is why this page is built out of them.</p>""" % (
        th_row, tr_row, "\n".join(body))


# --------------------------------------------------------------------------- #
def blocks():
    d = load()
    return {
        "alloc-matrix": alloc_matrix(d),
        "alloc-fill": alloc_fill(d),
        "alloc-schema": alloc_schema(d),
        "availability": availability(d),
        "squad-load": squad_load(d),
        "timeline": timeline(d),
        "okr-frameworks": okr_frameworks(d),
        "okr-cascade": okr_cascade(d),
        "okr-mine": okr_mine(d),
    }


if __name__ == "__main__":
    for k, v in blocks().items():
        print("%-16s %6d chars" % (k, len(v)))
