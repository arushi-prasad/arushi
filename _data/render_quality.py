"""Turn ``quality.json`` into the HTML blocks for the Design Quality page.

Same contract as render.py: the page fragment holds ``<!--data:key-->`` markers
and the build substitutes what :func:`blocks` returns. Scores are formatted here
but never computed here -- quality_extract.py recomputes them from the
question-level ratings and the page prints what it is given.
"""
import html
import json
from pathlib import Path

DATA = Path(__file__).parent / "quality.json"
SCALE_MAX = 5.0


def e(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def num(v, dp=2):
    """2.1666666 -> 2.17, 3.5 -> 3.5, 5.0 -> 5."""
    if v is None:
        return "·"
    s = ("%." + str(dp) + "f") % float(v)
    return s.rstrip("0").rstrip(".") if "." in s else s


def load():
    return json.loads(DATA.read_text(encoding="utf-8"))


def srcnote(text):
    return '<p class="srcnote">%s</p>' % e(text)


# --------------------------------------------------------------------------- #
# The recorded evaluation
# --------------------------------------------------------------------------- #
def scorecard(d):
    c = d["completed"]
    rows = []
    for r in c["report"]:
        pct = r["score"] / SCALE_MAX * 100
        rows.append(
            '<li class="score__row">'
            '<span class="score__name">%s</span>'
            '<span class="score__track" role="img" aria-label="%s out of 5">'
            '<i class="score__fill" style="width:%.2f%%"></i></span>'
            '<span class="score__val">%s<span class="score__of">/5</span></span></li>'
            % (e(r["name"]), e(num(r["score"])), pct, e(num(r["score"]))))

    ticks = "".join(
        '<span class="score__tick" style="left:%.1f%%"><i></i>%d</span>' % (i / 5 * 100, i)
        for i in range(0, 6))

    t = c["total"]
    return """<div class="score">
  <div class="score__head">
    <h3 class="score__title">UX evaluation: recorded scores</h3>
    <p class="score__sub">One completed review. Each dimension is the mean of its own
    question ratings on a 1&ndash;5 scale, where 1 is &ldquo;Not at all&rdquo; and 5 is
    &ldquo;Completely&rdquo;.</p>
  </div>
  <ol class="score__rows">%s</ol>
  <div class="score__axis"><span class="score__name"></span>
    <span class="score__track">%s</span><span class="score__val"></span></div>
  <p class="score__total"><span class="score__big">%s</span>
    <span class="score__totlab">out of %s across five dimensions</span></p>
</div>
%s""" % (
        "\n".join(rows), ticks, e(num(t["score"])), e(num(t["out_of"], 0)),
        srcnote("Source: %s. Every figure above was recomputed from the sheet's own "
                "question ratings and matched its recorded value exactly." % c["source"]))


def questions(d):
    c = d["completed"]
    panels = []
    for i, dim in enumerate(c["dimensions"]):
        qs = "".join(
            '<li class="qq__row"><span class="qq__score" data-band="%s">%s</span>'
            '<span class="qq__text">%s</span></li>'
            % ("low" if (q["rating"] or 0) < 2.5 else
               ("mid" if (q["rating"] or 0) < 3.5 else "high"),
               e(num(q["rating"])), e(q["text"]))
            for q in dim["questions"])
        panels.append(
            '<section class="qq" data-dim="%d"%s>'
            '<header class="qq__head"><h4 class="qq__name">%s</h4>'
            '<p class="qq__def">%s</p>'
            '<p class="qq__mean">%s<span class="score__of">/5</span>'
            '<span class="qq__meanlab">mean of %d</span></p></header>'
            '<ol class="qq__rows">%s</ol></section>'
            % (i, "" if i == 0 else " hidden", e(dim["name"]), e(dim["definition"]),
               e(num(dim["recorded"])), len(dim["questions"]), qs))

    tabs = "".join(
        '<button type="button" class="qtab%s" data-dim="%d" aria-pressed="%s">'
        '<span class="qtab__n">%s</span><span class="qtab__name">%s</span></button>'
        % (" is-on" if i == 0 else "", i, "true" if i == 0 else "false",
           e(num(dim["recorded"])), e(dim["name"]))
        for i, dim in enumerate(c["dimensions"]))

    return """<div class="qq__wrap" data-questions>
  <div class="qtabs" role="group" aria-label="Choose an evaluation dimension">%s</div>
  <div class="qq__panels">%s</div>
</div>
%s""" % (tabs, "\n".join(panels),
         srcnote("Source: %s. All twenty questions and their individual ratings, as "
                 "recorded. Every question on this page is the workbook's own wording, "
                 "including its typos." % c["source"]))


# --------------------------------------------------------------------------- #
# The model behind it
# --------------------------------------------------------------------------- #
def model(d):
    inst = d["definitions"]
    cards = []
    for f in inst["factors"]:
        rows = "".join(
            '<li class="pm__row"><span class="pm__param">%s</span>'
            '<span class="pm__def">%s</span></li>' % (e(r["parameter"]), e(r["text"]))
            for r in f["rows"])
        cards.append(
            '<article class="pm"><header class="pm__head">'
            '<h3 class="pm__name">%s</h3><p class="pm__intent">%s</p>'
            '<p class="pm__count">%d parameters</p></header>'
            '<ol class="pm__rows">%s</ol></article>'
            % (e(f["name"]), e(f["definition"]), len(f["rows"]), rows))
    return '<div class="pm__grid">%s</div>\n%s' % (
        "\n".join(cards),
        srcnote("Source: %s. Each factor is defined by what it should achieve, then "
                "broken into the parameters a reviewer actually looks at." % inst["source"]))


def versions(d):
    sets = [
        ("Definitions", d["definitions"], "What each parameter means. No questions, no scores."),
        ("Question set", d["blank_questions"], "The same model turned into reviewer questions. Blank, never filled in."),
        ("Revised question set", d["revised_questions"], "A later revision. The fifth factor is renamed and regrouped."),
        ("Completed review", None, "The one version with ratings in it."),
    ]
    completed = d["completed"]
    rows = []
    for label, inst, note in sets:
        if inst is None:
            factors = [x["name"] for x in completed["dimensions"]]
            count = sum(len(x["questions"]) for x in completed["dimensions"])
            source = completed["source"]
            filled = True
        else:
            factors = [f["name"] for f in inst["factors"]]
            count, source, filled = inst["count"], inst["source"], False
        rows.append(
            '<tr%s><th scope="row">%s<span class="vr__note">%s</span></th>'
            '<td data-label="Fifth factor"><span class="vr__fifth">%s</span></td>'
            '<td data-label="Rows">%d</td>'
            '<td data-label="Scores">%s</td>'
            '<td data-label="Source" class="vr__src">%s</td></tr>'
            % (' class="vr__on"' if filled else "", e(label), note,
               e(factors[-1] if factors else ""), count,
               "recorded" if filled else '<span class="vr__blank">none</span>', e(source)))

    return """<div class="vr__wrap">
<table class="vr">
  <caption class="srcnote">Four versions of one instrument, kept apart</caption>
  <thead><tr><th scope="col">Version</th><th scope="col">Fifth factor</th>
    <th scope="col">Rows</th><th scope="col">Scores</th><th scope="col">Source sheet</th></tr></thead>
  <tbody>%s</tbody>
</table>
</div>
<p class="note">The first four factors are stable across all four. The fifth is not: it is
<span class="tag">Error Prevention and Handling</span> in the definitions,
<span class="tag">Error Handling &amp; Guidance</span> in the question set and the completed
review, and <span class="tag">Guidance &amp; Handholding</span> in the revision, which
also grows from five questions to six. These are not presented as one framework, because
the files do not show them as one.</p>""" % "\n".join(rows)


def scale(d):
    s = d["scale"]
    dims = s["dimensions"]
    head = "".join('<th scope="col">%s</th>' % e(x) for x in dims)
    rows = []
    for L in s["levels"]:
        cells = "".join(
            '<td data-label="%s">%s</td>' % (e(x), e(L["by_dimension"].get(x, "")) or
                                             '<span class="vr__blank">·</span>')
            for x in dims)
        rows.append('<tr><th scope="row"><span class="sc__n">%d</span>%s</th>%s</tr>'
                    % (L["level"], e(L["label"]), cells))
    return """<div class="sc__wrap">
<table class="sc">
  <caption class="srcnote">What each point on the scale means, per dimension:
  %s</caption>
  <thead><tr><th scope="col">Level</th>%s</tr></thead>
  <tbody>%s</tbody>
</table>
</div>
<p class="note">This is the part that does the work. A 1&ndash;5 scale with no shared
definition of 3 is just opinion with a number attached; these twenty-five descriptors are
what let two reviewers land on the same score for the same screen. Level 0 is
&ldquo;Not applicable&rdquo; and carries no descriptors.</p>""" % (
        e(s["source"]), head, "\n".join(rows))


def snapshot(d):
    s = d["snapshot"]

    def bars(items, label):
        rows = "".join(
            '<li class="score__row"><span class="score__name">%s</span>'
            '<span class="score__track" role="img" aria-label="%s out of 5">'
            '<i class="score__fill score__fill--alt" style="width:%.2f%%"></i></span>'
            '<span class="score__val">%s<span class="score__of">/5</span></span></li>'
            % (e(x["name"]), e(num(x["score"])), x["score"] / SCALE_MAX * 100, e(num(x["score"])))
            for x in items)
        return ('<div class="snap__col"><h3 class="snap__title">%s</h3>'
                '<ol class="score__rows">%s</ol></div>' % (e(label), rows))

    return """<div class="snap">%s%s</div>
%s
<p class="note"><strong>These are not the scores above.</strong> They sit in a different
workbook, score a fifth factor the completed review does not have
(<span class="tag">Guidance &amp; Handholding</span>), and have no question-level rows
behind them anywhere in the file. Nothing in the sources establishes what was reviewed,
when, or by whom, so this is shown as a separate snapshot and never as a
before-and-after. The two sets are not combined or averaged.</p>""" % (
        bars(s["by_factor"], "By factor"), bars(s["by_parameter"], "By parameter"),
        srcnote("Source: %s. The only sheet that scores the same review two ways." % s["source"]))


def review_layers(d):
    r = d["review_layers"]
    chips = "".join('<li class="chip">%s</li>' % e(c) for c in r["cells"])
    return ('<ul class="chips" role="list">%s</ul>\n%s\n<p class="note">%s</p>'
            % (chips, srcnote("Source: " + r["source"]), e(r["note"])))


# --------------------------------------------------------------------------- #
# The checklist
# --------------------------------------------------------------------------- #
def checklist(d):
    ck = d["checklist"]
    cards = []
    for i, s in enumerate(ck["stages"], start=1):
        checks = "".join(
            '<li class="ck__item"><span class="ck__box" aria-hidden="true"></span>%s</li>'
            % e(c) for c in s["checks"])
        cards.append(
            '<article class="ck"><p class="ck__n">%02d</p>'
            '<h3 class="ck__title">%s</h3>%s<ul class="ck__items">%s</ul></article>'
            % (i, e(s["title"]),
               '<p class="ck__why">%s</p>' % e(s["rationale"]) if s["rationale"] else "",
               checks))

    opening = ck["slides"][0] if ck["slides"] else None
    lead = ""
    if opening and opening["checks"]:
        lead = ('<blockquote class="ck__lead"><p>%s</p><ul>%s</ul></blockquote>'
                % (e(opening["title"]),
                   "".join("<li>%s</li>" % e(c) for c in opening["checks"])))

    return """%s
<div class="ck__grid">%s</div>
%s
<p class="note">A digital reconstruction, not a screenshot: the deck is %d slides of live
text with no embedded images, so there is nothing in it to export. Wording is the
original's, including &ldquo;Did I replaced all dummy data&rdquo;. Seven review stages,
%d checks. A checklist existing is not evidence that every design was reviewed against it,
and the files record no completed reviews.</p>""" % (
        lead, "\n".join(cards),
        srcnote("Reconstructed from %s, slides 1&ndash;%d" % (ck["source"], len(ck["slides"]))),
        len(ck["slides"]), ck["check_count"])


# --------------------------------------------------------------------------- #
# Share & Critique
# --------------------------------------------------------------------------- #
def choreography(d):
    ch = d["critique"]["choreography"]
    lo = sum(s["lo"] for s in ch["stages"])
    hi = sum(s["hi"] for s in ch["stages"])
    span = hi

    stages = []
    for s in ch["stages"]:
        # The bar is as wide as the stage's maximum; the solid part of it is the
        # guaranteed minimum, so a 7-10 minute stage reads as both numbers.
        stages.append(
            '<li class="ch__stage" style="--hi:%.2f%%;--lo-rel:%.2f%%">'
            '<span class="ch__n">%d</span>'
            '<span class="ch__who">%s</span>'
            '<span class="ch__bar"><i></i></span>'
            '<span class="ch__time">%s</span>'
            '<span class="ch__text">%s</span>%s</li>'
            % (s["hi"] / span * 100, s["lo"] / s["hi"] * 100, s["n"], e(s["who"]),
               e("%d min" % s["lo"] if s["lo"] == s["hi"] else "%d&ndash;%d min" % (s["lo"], s["hi"])).replace("&amp;ndash;", "&ndash;"),
               e(s["text"]),
               '<span class="ch__detail">%s</span>' % e(s["detail"]) if s["detail"] else ""))

    return """<ol class="ch">%s</ol>
<p class="ch__foot"><span class="ch__total">%s</span>
<span class="ch__totlab">total, as the deck states it</span></p>
%s
<p class="note">%s The stage timings sum to %d&ndash;%d minutes, so the deck's stated lower
bound sits %d minutes above the sum of its own minimums. The stated total is kept as
written rather than quietly corrected.</p>""" % (
        "\n".join(stages), e(ch["stated_total"]),
        srcnote("Reconstructed from page %d. Durations and wording are the source's."
                % ch["page"]),
        e(ch["custodian"]), lo, hi, 45 - lo)


def mindsets(d):
    c = d["critique"]
    cs = c["cs"]
    head = "".join('<th scope="col">%s</th>' % e(x) for x in cs)
    rows = []
    for m in c["mindsets"]:
        cells = "".join(
            '<td data-label="%s"><ul>%s</ul></td>'
            % (e(x), "".join("<li>%s</li>" % e(i) for i in m["by_c"].get(x, [])))
            for x in cs)
        rows.append('<tr><th scope="row">%s<span class="ms__pg">page %d</span></th>%s</tr>'
                    % (e(m["role"]), m["page"], cells))
    return """<div class="ms__wrap">
<table class="ms">
  <caption class="srcnote">Three roles &times; three C's, verbatim from the deck</caption>
  <thead><tr><th scope="col">Role</th>%s</tr></thead>
  <tbody>%s</tbody>
</table>
</div>""" % (head, "\n".join(rows))


def frameworks(d):
    fws = d["critique"]["frameworks"]
    tabs = "".join(
        '<button type="button" class="ftab%s" data-fw="%d" aria-pressed="%s">%s</button>'
        % (" is-on" if i == 0 else "", i, "true" if i == 0 else "false", e(f["name"]))
        for i, f in enumerate(fws))
    panels = []
    for i, f in enumerate(fws):
        parts = "".join(
            '<li class="fwk__part"><span class="fwk__lab">%s</span>%s</li>'
            % (e(a), '<span class="fwk__hint">%s</span>' % e(b) if b else "")
            for a, b in f["parts"])
        panels.append('<ul class="fwk__parts" data-fw="%d"%s>%s</ul>'
                      % (i, "" if i == 0 else " hidden", parts))
    return """<div class="fwk" data-frameworks>
  <div class="ftabs" role="group" aria-label="Choose a critique framework">%s</div>
  %s
</div>
%s""" % (tabs, "\n".join(panels),
         srcnote("Digital reconstructions of the frameworks on pages %s. The frameworks "
                 "are established practice presented in the deck, not mine and not its "
                 "author's invention."
                 % ", ".join(str(f["page"]) for f in fws)))


def four_player(d):
    fp = d["critique"]["four_player"]
    roles = "".join('<li class="fp__role">%s</li>' % e(r) for r in fp["roles"])
    return ('<div class="fp"><ol class="fp__ring">%s</ol>'
            '<p class="fp__mid">%s</p></div>\n%s'
            % (roles, e(fp["note"]),
               srcnote("%s, as cited on page %d. Named positions in a conversation that "
                       "everyone moves through, not fixed personality types."
                       % (fp["name"], fp["page"]))))


def wip(d):
    w = d["critique"]["wip"]
    ex = "".join('<li class="chip">%s</li>' % e(x) for x in w["examples"])
    fm = "".join('<li class="chip">%s</li>' % e(x) for x in w["formats"])
    r = d["critique"]["readiness"]
    return """<div class="wip">
  <div class="wip__col"><h4 class="snap__title">What counts as work in progress</h4>
    <ul class="chips" role="list">%s</ul></div>
  <div class="wip__col"><h4 class="snap__title">How it gets shared</h4>
    <ul class="chips" role="list">%s</ul></div>
</div>
<div class="ready">
  <p class="ready__must"><span class="ready__lab">Must have</span>%s</p>
  <p class="ready__nice"><span class="ready__lab">Nice to have</span>%s</p>
</div>
%s""" % (ex, fm, e(r["must"]), e(" ".join(r["nice"])),
         srcnote("Source: pages %d and %d." % (w["page"], r["page"])))


def credit(d):
    a = d["critique"]["attribution"]
    return """<aside class="credit">
  <p class="credit__lab">Source &amp; attribution</p>
  <p class="credit__body"><strong>&ldquo;%s&rdquo;</strong> is the work of
  <strong>%s</strong>, %s of %s, dated %s. It is not my material and I am not its author.
  It sits here because it is the method I would reach for, and because a page about design
  quality that quietly reused someone else's deck would fail its own argument.</p>
  <p class="credit__src">%s</p>
</aside>""" % (e(a["title"]), e(a["author"]), e(a["role"]), e(a["org"]), e(a["date"]),
               e(a["source"]))


# --------------------------------------------------------------------------- #
def blocks():
    d = load()
    return {
        "q-scorecard": scorecard(d),
        "q-questions": questions(d),
        "q-model": model(d),
        "q-versions": versions(d),
        "q-scale": scale(d),
        "q-snapshot": snapshot(d),
        "q-review-layers": review_layers(d),
        "q-checklist": checklist(d),
        "q-credit": credit(d),
        "q-choreography": choreography(d),
        "q-mindsets": mindsets(d),
        "q-frameworks": frameworks(d),
        "q-four-player": four_player(d),
        "q-wip": wip(d),
    }


if __name__ == "__main__":
    for k, v in blocks().items():
        print("%-18s %6d chars" % (k, len(v)))
