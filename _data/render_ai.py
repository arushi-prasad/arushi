"""HTML blocks for the AI Design Operating System page.

Everything here is driven by ``ai.json``: the frameworks come out of the source
document, the repository counts are measured from the WorkPerks working tree.
Nothing in this module invents a number, and every block that describes a
proposed model carries a CONCEPT label rather than implying it is in place.
"""
import html
import json
from pathlib import Path

DATA = Path(__file__).parent / "ai.json"


def e(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def load():
    return json.loads(DATA.read_text(encoding="utf-8"))


def ev(kind, note=""):
    """The evidence label. Three states, used strictly."""
    text = {"verified": "Verified", "experiment": "Experiment", "concept": "Concept"}[kind]
    return ('<p class="ev ev--%s"><span class="ev__dot" aria-hidden="true"></span>'
            '<span class="ev__k">%s</span>%s</p>'
            % (kind, e(text), '<span class="ev__n">%s</span>' % e(note) if note else ""))


def srcnote(text):
    return '<p class="srcnote">%s</p>' % e(text)


# --------------------------------------------------------------------------- #
# 02 · workflows
# --------------------------------------------------------------------------- #
def workflows(d):
    w = d["workflows"]

    def rail(key, label, cls):
        x = w[key]
        steps = "".join(
            '<li class="rail__step"><span class="rail__n">%02d</span>'
            '<span class="rail__name">%s</span></li>' % (i, e(s))
            for i, s in enumerate(x["stages"], start=1))
        traits = "".join('<li class="chip">%s</li>' % e(t) for t in x["traits"])
        return ('<article class="rail %s" data-flow="%s">'
                '<h3 class="rail__title">%s</h3>'
                '<ol class="rail__steps">%s</ol>'
                '<ul class="chips" role="list">%s</ul></article>'
                % (cls, e(key), e(label), steps, traits))

    return """<div class="flows" data-flows>
  <div class="flows__switch" role="group" aria-label="Choose a workflow model">
    <button type="button" class="fswitch is-on" data-flow="old" aria-pressed="true">Sequential</button>
    <button type="button" class="fswitch" data-flow="new" aria-pressed="false">AI-native</button>
  </div>
  <div class="flows__pair">%s%s</div>
</div>
%s
<p class="note">Both models are drawn from the source document. The second is an
operating model I am arguing for, not a description of how every project I touch runs
today &mdash; and the first is not wrong, it is what works when iteration is expensive.
What changes is where the loop closes.</p>""" % (
        rail("old", "Sequential", "rail--old"),
        rail("new", "AI-native", "rail--new"),
        ev("concept", "The AI-native model is a proposed operating approach"))


# --------------------------------------------------------------------------- #
# 03 · thesis
# --------------------------------------------------------------------------- #
def thesis(d):
    parts = [
        ("Human judgment", "Deciding what matters, and owning the outcome."),
        ("AI acceleration", "Generating, exploring, scaffolding, drafting."),
        ("Systemised knowledge", "Components, rules, context and decisions that persist."),
        ("Continuous feedback", "What shipped, what broke, what the next cycle inherits."),
    ]
    cells = "".join(
        '<li class="eq__part"><span class="eq__n">%02d</span>'
        '<h3 class="eq__name">%s</h3><p class="eq__note">%s</p></li>'
        % (i, e(a), e(b)) for i, (a, b) in enumerate(parts, start=1))
    return """<div class="eq">
  <ol class="eq__row">%s</ol>
  <p class="eq__sum">Each one is weaker without the others. AI without systemised
  knowledge regenerates the same decisions forever; knowledge without feedback goes
  stale; neither replaces the judgment call.</p>
</div>
%s""" % (cells, ev("concept"))


# --------------------------------------------------------------------------- #
# 04 · the seven layers
# --------------------------------------------------------------------------- #
def layers(d):
    Ls = d["layers"]
    stack = "".join(
        '<button type="button" class="stack__layer%s" data-layer="%d" aria-pressed="%s">'
        '<span class="stack__n">%02d</span><span class="stack__name">%s</span>'
        '<span class="stack__bar" aria-hidden="true"></span></button>'
        % (" is-on" if i == 0 else "", L["n"], "true" if i == 0 else "false",
           L["n"], e(L["name"]))
        for i, L in enumerate(Ls))

    panels = []
    for i, L in enumerate(Ls):
        cols = []
        if L["ai"]:
            cols.append(('ai', L["ai_label"] or "AI assists with", L["ai"]))
        if L["human"]:
            cols.append(('human', "Human owns", L["human"]))
        for g in L["groups"]:
            cols.append(('neutral', g["label"], g["items"]))
        body = "".join(
            '<div class="lay__col lay__col--%s"><h4 class="lay__ch">%s</h4>'
            '<ul class="lay__list">%s</ul></div>'
            % (kind, e(label), "".join("<li>%s</li>" % e(x) for x in items))
            for kind, label, items in cols)
        extra = ""
        if L["arrows"]:
            extra += "".join(
                '<p class="lay__arrow">%s</p>'
                % " ".join('<span>%s</span>' % e(p.strip())
                           for p in a.split("→"))
                for a in L["arrows"])
        if L["quote"]:
            extra += '<p class="lay__quote">%s</p>' % e(L["quote"])
        if L["n"] == 5 and not L["shared"]:
            extra += ('<p class="gap"><span class="gap__k">Input needed</span>'
                      'The source document deliberately leaves the engineering '
                      'ownership boundary blank rather than guessing at it. '
                      'It stays blank here too.</p>')
        panels.append(
            '<section class="lay" data-layer="%d"%s>'
            '<header class="lay__head"><p class="lay__n">Layer %02d</p>'
            '<h3 class="lay__name">%s</h3>%s</header>'
            '<div class="lay__cols">%s</div>%s</section>'
            % (L["n"], "" if i == 0 else " hidden", L["n"], e(L["name"]),
               '<ul class="chips" role="list">%s</ul>'
               % "".join('<li class="chip">%s</li>' % e(x) for x in L["define"])
               if L["define"] else "", body, extra))

    return """<div class="os" data-layers>
  <div class="os__stack" role="group" aria-label="Choose a layer of the operating system">
    %s
  </div>
  <div class="os__detail">%s</div>
</div>
%s
<p class="note">Seven layers, from the source document. The point of the stack is that
AI touches every one of them but owns none of them &mdash; each layer names what AI can
contribute and what stays a human call.</p>""" % (
        stack, "\n".join(panels),
        ev("concept", "A proposed operating model, not an implemented process"))


# --------------------------------------------------------------------------- #
# 05 · responsibility matrix
# --------------------------------------------------------------------------- #
def matrix(d):
    rows = "".join(
        '<tr><th scope="row">%s</th>'
        '<td class="rm__ai" data-label="AI contributes">%s</td>'
        '<td class="rm__hu" data-label="Human remains responsible for">%s</td></tr>'
        % (e(r["activity"]), e(r["ai"]), e(r["human"])) for r in d["matrix"])
    return """<div class="rm__wrap">
<table class="rm">
  <caption class="srcnote">Thirteen activities, in the source document's own wording</caption>
  <thead><tr><th scope="col">Activity</th>
    <th scope="col"><span class="rm__key rm__key--ai">AI contributes</span></th>
    <th scope="col"><span class="rm__key rm__key--hu">Human remains responsible for</span></th>
  </tr></thead>
  <tbody>%s</tbody>
</table>
</div>
<figure class="bigquote">
  <blockquote><p>AI expands the surface area of design. It does not remove accountability.</p></blockquote>
</figure>
%s
<p class="note">Read the right-hand column as the real job description. Every row on the
left is work that still arrives needing review &mdash; a generated flow, a generated
component, a generated paragraph of documentation is a draft with a confident tone, and
nothing more than that until someone signs it off.</p>""" % (rows, ev("concept"))


# --------------------------------------------------------------------------- #
# 06 · WorkPerks
# --------------------------------------------------------------------------- #
SURFACES = [
    ("Onboarding", "splash, org ID, per-module learn, intro pages, permissions"),
    ("Perks &amp; benefits catalogue", "categories, detail, partners, collections, locations, saved, search, orders"),
    ("Flexi benefits", "allocation across funded heads against a grade-band pool, donut and decision sheets"),
    ("Rewards &amp; Recognition", "wall, awards, certificates, nominations, programmes, winners, milestones, journey map"),
    ("Vouchers &amp; coins", "balance, catalogue, denominations, code redemption, my vouchers"),
    ("Reimbursements", "claim heads, new claim, my claims"),
    ("AI chat", "a modal route with local retrieval"),
    ("Notifications", "preferences, challenges, profile"),
]


def workperks(d):
    cells = "".join(
        '<li class="eco__cell"><span class="eco__n">%02d</span>'
        '<h4 class="eco__name">%s</h4><p class="eco__note">%s</p></li>'
        % (i, a, b) for i, (a, b) in enumerate(SURFACES, start=1))
    chain = ["Product problem", "Ecosystem definition", "Experience architecture",
             "Design system", "UX / UI", "AI-assisted build", "Working product"]
    steps = "".join(
        '<li class="prod__step"><span class="prod__n">%02d</span>%s</li>' % (i, e(s))
        for i, s in enumerate(chain, start=1))
    return """<ol class="prod">%s</ol>
<h3 class="snap__title" style="margin-top:var(--step-12)">The eight product surfaces</h3>
<ul class="eco" role="list">%s</ul>
%s""" % (steps, cells,
         srcnote("Surfaces as enumerated by the project's own repository walkthrough, "
                 "shown in the terminal session further down this page."))


def scale(d):
    c = d["codebase"]
    if not c:
        return ('<p class="gap"><span class="gap__k">Not available</span>'
                'The WorkPerks working tree was not reachable when this page was '
                'built, so no repository statistics are shown.</p>')

    bars = [("Registered routes", c["routes"], "screens wired to a navigator"),
            ("TypeScript files", c["ts_files"], "source files, .ts and .tsx"),
            ("UI primitives", c["ui_files"], "modules in src/ui")]
    peak = max(v for _n, v, _h in bars)
    rowhtml = "".join(
        '<li class="sbar__row"><span class="sbar__name">%s<span class="sbar__hint">%s</span></span>'
        '<span class="sbar__track"><i style="width:%.1f%%"></i></span>'
        '<span class="sbar__val">%d</span></li>'
        % (e(n), e(h), v / peak * 100, v) for n, v, h in bars)

    return """<ul class="stats stats--big">
  <li><p class="stat__value">%s</p><p class="stat__label">lines of TypeScript</p></li>
  <li><p class="stat__value">%d</p><p class="stat__label">registered routes</p></li>
  <li><p class="stat__value">%d</p><p class="stat__label">UI primitives</p></li>
</ul>
<ul class="sbar">%s</ul>
%s
%s
<p class="note"><strong>Three different units, deliberately not combined.</strong> A
route count, a file count and a line count measure different things and none of them is
a measure of quality, speed or business impact. They are here to show the scale of the
surface a designer can now reach into &mdash; nothing more. I am not claiming AI wrote
this, that it was faster than an alternative, or that size is an achievement.</p>
<p class="note">The portfolio previously recorded a snapshot of <span class="tag">67
routes</span>, <span class="tag">28 UI primitives</span>, <span class="tag">163 TS
files</span> and <span class="tag">~33,800 lines</span>. Re-measuring the working tree
gives the figures above: the primitive count is unchanged, the other three have grown.
The older numbers are left visible here rather than quietly replaced.</p>""" % (
        f"{c['loc']:,}", c["routes"], c["ui_files"], rowhtml,
        ev("verified", "Measured from the working tree on %s" % c["measured"]),
        srcnote("%s &mdash; %s. %s" % (c["project"], c["stack"], c["method"])))


def primitives(d):
    c = d["codebase"]
    if not c:
        return ""
    return ('<ul class="chips" role="list">%s</ul>\n%s'
            % ("".join('<li class="chip">%s</li>' % e(p) for p in c["primitives"]),
               srcnote("Every module in src/ui, listed by filename. This is the "
                       "component vocabulary the app is actually built from.")))


# --------------------------------------------------------------------------- #
# 07 · the build loop
# --------------------------------------------------------------------------- #
def buildloop(d):
    chain = ["Product thinking", "Experience design", "Claude Code", "Frontend",
             "Backend", "APIs / integrations", "React Native", "Working product"]
    steps = "".join(
        '<li class="prod__step%s"><span class="prod__n">%02d</span>%s</li>'
        % (" prod__step--on" if s == "Claude Code" else "", i, e(s))
        for i, s in enumerate(chain, start=1))

    split = d["build_split"]
    cols = []
    for key, label, kind in (("designer", "Designer-owned", "human"),
                             ("ai", "AI-assisted", "ai")):
        items = split.get(key) or []
        cols.append('<div class="lay__col lay__col--%s"><h4 class="lay__ch">%s</h4>'
                    '<ul class="lay__list">%s</ul></div>'
                    % (kind, e(label), "".join("<li>%s</li>" % e(x) for x in items)))
    cols.append(
        '<div class="lay__col lay__col--gap"><h4 class="lay__ch">Engineering-owned / shared</h4>'
        '<p class="gap"><span class="gap__k">Input needed</span>'
        'The source document refuses to invent this boundary and so does this page. '
        'Describing a collaboration model I cannot evidence would undo the point of '
        'the rest of the section.</p></div>')

    return """<ol class="prod prod--loop">%s</ol>
<h3 class="snap__title" style="margin-top:var(--step-10)">Who owned what</h3>
<div class="lay__cols lay__cols--three">%s</div>
%s""" % (steps, "".join(cols),
         ev("experiment", "A workflow I have actually run, evidenced by the repository "
                          "and the session below"))


# --------------------------------------------------------------------------- #
# 09 · Capsule
# --------------------------------------------------------------------------- #
def generations(d):
    gens = d["generations"]
    names = ["UI library", "Design system", "Design intelligence"]
    kinds = ["verified", "verified", "concept"]
    feeds = ["Design tokens", "Components and variants", "Usage rules", "Product context",
             "Design principles", "Constraints", "AI-readable instructions",
             "Validation criteria"]
    cards = "".join(
        '<li class="gen%s"><p class="gen__n">Generation %d</p>'
        '<h3 class="gen__name">%s</h3><p class="gen__note">%s</p>%s</li>'
        % (" gen--concept" if kinds[i] == "concept" else "", i + 1,
           e(names[i]), e(g["note"]),
           '<p class="gen__tag">Concept</p>' if kinds[i] == "concept" else
           '<p class="gen__tag gen__tag--v">Verified</p>')
        for i, g in enumerate(gens))
    chips = "".join('<li class="chip">%s</li>' % e(f) for f in feeds)
    return """<ol class="gens">%s</ol>
<div class="feed">
  <h3 class="snap__title">What a design system would have to hand an AI</h3>
  <ul class="chips" role="list">%s</ul>
</div>
<figure class="bigquote">
  <blockquote><p>Instead of teaching AI what the product looks like, teach AI how the product thinks.</p></blockquote>
</figure>
%s
<p class="note">Generations 1 and 2 describe Capsule as it exists &mdash; tokens,
components, rules, governance. Generation 3 is a proposal. Capsule does not generate
designs or validate output automatically today, and this page does not suggest it
does.</p>""" % (cards, chips, ev("concept", "Generation 3 only"))


# --------------------------------------------------------------------------- #
# 10 · team operating model
# --------------------------------------------------------------------------- #
def opmodel(d):
    stages = d["operating_model"]
    ring = "".join(
        '<li class="cycle__stage"><span class="cycle__n">%02d</span>'
        '<h3 class="cycle__name">%s</h3><p class="cycle__note">%s</p></li>'
        % (i, e(s["title"]), e(s["note"])) for i, s in enumerate(stages, start=1))
    wheel = ["Work", "Knowledge", "System", "Better work"]
    spokes = "".join('<li class="wheel__node">%s</li>' % e(w) for w in wheel)
    return """<ol class="cycle">%s</ol>
<div class="wheel">
  <ol class="wheel__ring">%s</ol>
  <p class="wheel__mid">The loop only closes if finished work is written back</p>
</div>
%s""" % (ring, spokes, ev("concept"))


def rituals(d):
    rows = "".join(
        '<li class="rit"><h3 class="rit__name">%s</h3><p class="rit__note">%s</p>'
        '<ul class="rit__items">%s</ul></li>'
        % (e(r["title"]), e(r["note"]),
           "".join("<li>%s</li>" % e(x) for x in r["items"][:6]))
        for r in d["rituals"])
    return ('<ul class="rits" role="list">%s</ul>\n%s\n'
            '<p class="note">Five rituals from the source document. None of these runs '
            'in my organisation today &mdash; they are what I would introduce, and '
            'saying otherwise would be the easiest lie on this page.</p>'
            % (rows, ev("concept", "Proposed rituals, not current practice")))


# --------------------------------------------------------------------------- #
# 11 · governance
# --------------------------------------------------------------------------- #
def governance(d):
    rows = "".join(
        '<li class="gov"><span class="gov__n">%02d</span>'
        '<h3 class="gov__name">%s</h3><p class="gov__q">%s</p></li>'
        % (i, e(g["title"]), e(g["note"]))
        for i, g in enumerate(d["governance"], start=1))
    return """<ol class="govs">%s</ol>
<figure class="bigquote">
  <blockquote><p>AI can generate an output. A responsible human must own the outcome.</p></blockquote>
</figure>
%s
<p class="note">Each category is a question rather than a policy, because a policy I
have not written and an organisation has not adopted would be a claim I cannot make.
These are the seven things I would want answered before a team starts.</p>""" % (
        rows, ev("concept", "A proposed framework; no organisational policy is claimed"))


# --------------------------------------------------------------------------- #
# 12 · measurement
# --------------------------------------------------------------------------- #
def metrics(d):
    cats = d["metrics"]
    cards = "".join(
        '<article class="meas"><h3 class="meas__name">%s</h3><ul class="meas__list">%s</ul></article>'
        % (e(c["title"]),
           "".join('<li><span class="meas__m">%s</span>'
                   '<span class="meas__v">Metric to establish</span></li>' % e(m)
                   for m in c["items"]))
        for c in cats)
    total = sum(len(c["items"]) for c in cats)
    return """<div class="meass">%s</div>
%s
<p class="note">%d candidate metrics across six categories, and <strong>not one of them
has a value</strong>. No baseline for any of these exists in my source files, so every
cell reads &ldquo;metric to establish&rdquo;. A page like this is where fabricated
percentages normally appear; putting the empty frame on display instead is the more
useful artefact, because the first real job is deciding which four of these are worth
instrumenting.</p>""" % (cards, ev("concept", "No values recorded in any source"), total)


# --------------------------------------------------------------------------- #
# 13 · blueprint
# --------------------------------------------------------------------------- #
OPPS = [
    ("Automate", "Repetitive, rule-shaped work with a checkable output."),
    ("Accelerate", "Work where AI reduces manual effort but a human still steers."),
    ("Assist", "Work where AI informs a decision a human makes."),
    ("Human-owned", "Decisions that carry accountability and stay with a person."),
]


def blueprint(d):
    steps = "".join(
        '<li class="bp__step"><span class="bp__n">%02d</span>'
        '<span class="bp__name">%s</span></li>'
        % (i, e(s["title"].split("—", 1)[-1].strip()))
        for i, s in enumerate(d["blueprint"], start=1))
    quad = "".join(
        '<li class="opp opp--%d"><h3 class="opp__name">%s</h3><p class="opp__note">%s</p></li>'
        % (i, e(a), e(b)) for i, (a, b) in enumerate(OPPS, start=1))
    return """<ol class="bp">%s</ol>
<h3 class="snap__title" style="margin-top:var(--step-12)">Sorting the work: four kinds of AI opportunity</h3>
<ul class="opps" role="list">%s</ul>
%s""" % (steps, quad, ev("concept"))


# --------------------------------------------------------------------------- #
def blocks():
    d = load()
    return {
        "ai-workflows": workflows(d),
        "ai-thesis": thesis(d),
        "ai-layers": layers(d),
        "ai-matrix": matrix(d),
        "ai-workperks": workperks(d),
        "ai-scale": scale(d),
        "ai-primitives": primitives(d),
        "ai-buildloop": buildloop(d),
        "ai-generations": generations(d),
        "ai-opmodel": opmodel(d),
        "ai-rituals": rituals(d),
        "ai-governance": governance(d),
        "ai-metrics": metrics(d),
        "ai-blueprint": blueprint(d),
    }


if __name__ == "__main__":
    for k, v in blocks().items():
        print("%-16s %6d chars" % (k, len(v)))
