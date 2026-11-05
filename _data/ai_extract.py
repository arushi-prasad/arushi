"""Parse the AI Design Operating System source document into JSON.

The document is a long specification written in Markdown. Everything the page
shows -- the seven layers, the responsibility matrix, the workflows, the rituals,
the governance questions, the measurement candidates -- is lifted out of it here
rather than retyped into HTML, so the page cannot drift from the source.

The repository statistics are a separate matter: they are measured live from the
WorkPerks codebase by :func:`measure_codebase`, never taken from the document.

    python3 _data/ai_extract.py ["/path/to/3. AI-Design-Operating-System.md"]
"""
import datetime
import json
import os
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent
OUT = HERE / "ai.json"
DOC = ("/Users/arushi.prasad/Desktop/Portfolio/03. Design Ops/"
       "3. AI-Design-Operating-System.md")
CODE = pathlib.Path("/Users/arushi.prasad/Desktop/WorkPerks/Front End")
SKIP = {"node_modules", ".next", "dist", "build", ".git", "ios", "android", ".expo"}


def tidy(s):
    return " ".join(str(s or "").split())


def sections(text):
    """Split on any heading, keeping level, title and the body beneath it."""
    out = []
    for m in re.finditer(r"^(#{1,4})\s+(.*?)\s*$", text, re.M):
        start = m.end()
        nxt = re.search(r"^#{1,4}\s", text[start:], re.M)
        body = text[start:start + nxt.start()] if nxt else text[start:]
        out.append({"level": len(m.group(1)), "title": tidy(m.group(2)), "body": body})
    return out


def bullets(body, after=None):
    """The bullet list in a body, optionally only the one following a label."""
    if after:
        m = re.search(re.escape(after) + r"\s*:?\s*\n", body)
        if not m:
            return []
        body = body[m.end():]
        stop = re.search(r"\n\s*\n(?=[A-Za-z*#>|])", body)
        if stop:
            body = body[:stop.start()]
    return [tidy(x) for x in re.findall(r"^\s*[-*]\s+(.*?)\s*$", body, re.M) if tidy(x)]


# --------------------------------------------------------------------------- #
# The document labels the same idea differently from layer to layer.
AI_LABELS = ("AI role", "AI can support", "AI can help", "AI-assisted",
             "Potential applications")
HUMAN_LABELS = ("Human ownership", "Designer-owned")
SHARED_LABELS = ("Engineering-owned / shared",)


def first_bullets(text, labels):
    for lab in labels:
        got = bullets(text, lab)
        if got:
            return got, lab
    return [], ""


def build_layers(text, secs):
    """The seven layers.

    Layers 1-4 are '## Layer NN'; Build, Quality and Knowledge are promoted to
    their own numbered '# N. Layer NN' sections and keep their detail in
    sub-headings rather than in labelled bullet blocks. Each layer therefore
    takes everything from its own heading up to the next layer heading, and both
    shapes are read out of that span.
    """
    heads = [(m.start(), m.group(0), m.group(1), tidy(m.group(2)))
             for m in re.finditer(
                 r"^#{1,3}\s+(?:\d+\.\s+)?Layer\s+(\d+)\s*[—–-]\s*(.+?)\s*$",
                 text, re.M)]
    out = []
    for i, (pos, raw, num, name) in enumerate(heads):
        end = heads[i + 1][0] if i + 1 < len(heads) else len(text)
        span = text[pos + len(raw):end]
        # Stop at the next top-level section that is not a layer.
        cut = re.search(r"^#\s+\d+\.\s+(?!Layer)", span, re.M)
        if cut:
            span = span[:cut.start()]

        ai, ai_label = first_bullets(span, AI_LABELS)
        human, _ = first_bullets(span, HUMAN_LABELS)
        shared, _ = first_bullets(span, SHARED_LABELS)
        define, _ = first_bullets(span, ("Define", "Covers"))

        # Sub-headings inside the layer, with their own bullets. This is how
        # Quality and Knowledge carry their detail.
        groups = []
        for gm in re.finditer(r"^#{3,4}\s+(.+?)\s*$", span, re.M):
            gstart = gm.end()
            gnext = re.search(r"^#{1,4}\s", span[gstart:], re.M)
            gbody = span[gstart:gstart + gnext.start()] if gnext else span[gstart:]
            items = bullets(gbody)
            label = tidy(gm.group(1))
            if items and label not in AI_LABELS + HUMAN_LABELS + SHARED_LABELS:
                groups.append({"label": label, "items": items})

        # A pull quote or a model line, where the layer has one.
        quote = re.findall(r"^>\s+\*\*(.+?)\*\*\s*$", span, re.M)
        arrows = [tidy(a) for a in re.findall(r"^\*\*(.+?→.+?)\*\*\s*$", span, re.M)]

        out.append({
            "n": int(num), "name": name,
            "define": define, "ai": ai, "ai_label": ai_label,
            "human": human, "shared": shared,
            "groups": groups,
            "quote": tidy(quote[0]) if quote else "",
            "arrows": arrows,
        })
    seen, final = set(), []
    for L in sorted(out, key=lambda x: x["n"]):
        if L["n"] not in seen:
            seen.add(L["n"])
            final.append(L)
    return final


def build_matrix(text):
    """The Human vs AI responsibility table, read as a Markdown table."""
    m = re.search(r"\|\s*Activity\s*\|.*?\n((?:\|.*\n)+)", text)
    rows = []
    for line in m.group(1).splitlines():
        cells = [tidy(c) for c in line.strip().strip("|").split("|")]
        if len(cells) != 3 or set(cells[0]) <= set("-: "):
            continue
        rows.append({"activity": cells[0], "ai": cells[1], "human": cells[2]})
    return rows


def build_workflows(secs):
    out = {}
    for s in secs:
        key = {"Old model": "old", "AI-native model": "new"}.get(s["title"])
        if not key:
            continue
        arrow = re.search(r"\*\*(.+?→.+?)\*\*", s["body"])
        out[key] = {
            "stages": [tidy(x) for x in arrow.group(1).split("→")] if arrow else [],
            "traits": bullets(s["body"], "Characteristics"),
        }
    return out


def build_simple(secs, parent, level, want_body=True):
    """Children of a numbered section: title plus its first paragraph/bullets."""
    out, inside = [], False
    for s in secs:
        if re.match(r"^\d+\.\s", s["title"]):
            inside = parent.lower() in s["title"].lower()
            continue
        if not inside or s["level"] != level:
            continue
        para = ""
        for block in re.split(r"\n\s*\n", s["body"]):
            b = tidy(block)
            if b and not b.startswith(("-", "*", ">", "|", "#")):
                para = b
                break
        item = {"title": re.sub(r"^\d+\s*[—–-]\s*", "", s["title"])}
        if want_body:
            item["note"] = para
            item["items"] = bullets(s["body"])
        out.append(item)
    return out


def measure_codebase(root):
    """Count the WorkPerks app directly. Nothing here is taken on trust."""
    if not root.exists():
        return None
    files, loc, screens, ui = [], 0, 0, 0
    newest = 0
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP]
        for f in fn:
            if not f.endswith((".ts", ".tsx")):
                continue
            p = pathlib.Path(dp, f)
            files.append(p)
            try:
                loc += len(p.read_text(errors="ignore").splitlines())
                newest = max(newest, os.path.getmtime(p))
            except OSError:
                pass
            rel = str(p.relative_to(root))
            if rel.startswith("src/screens"):
                screens += 1
            if rel.startswith("src/ui"):
                ui += 1

    # Routes are the screens registered with the navigator, counted from source.
    routes = set()
    for p in files:
        for m in re.finditer(r"<(?:Stack|Tab|Drawer)\.Screen\s[^>]*name=[\"']([^\"']+)",
                             p.read_text(errors="ignore")):
            routes.add(m.group(1))

    primitives = sorted(p.stem for p in files
                        if str(p.relative_to(root)).startswith("src/ui"))
    return {
        "project": "WorkPerks employee app",
        "stack": "Expo / React Native / TypeScript",
        "ts_files": len(files),
        "loc": loc,
        "routes": len(routes),
        "screen_files": screens,
        "ui_files": ui,
        "primitives": primitives,
        "route_names": sorted(routes),
        "measured": datetime.date.fromtimestamp(newest).isoformat() if newest else "",
        "method": "Counted from the working tree, excluding node_modules, build "
                  "output and native project folders. Routes are the distinct "
                  "names registered on a navigator in source.",
    }


def main():
    doc = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else DOC)
    if not doc.exists():
        raise SystemExit("source document not found: %s" % doc)
    text = doc.read_text(encoding="utf-8")
    secs = sections(text)

    gaps = [tidy(g) for g in re.findall(r"\[INPUT NEEDED:?\s*(.*?)\]", text)]
    data = {
        "source": {"file": doc.name, "lines": len(text.splitlines())},
        "gaps": gaps,
        "layers": build_layers(text, secs),
        "matrix": build_matrix(text),
        "workflows": build_workflows(secs),
        "operating_model": build_simple(secs, "AI-Native Design Team Operating Model", 2),
        "rituals": build_simple(secs, "Design Team Rituals", 3),
        "governance": build_simple(secs, "AI Governance", 2),
        "metrics": build_simple(secs, "Measuring the AI Design Operating System", 3),
        "generations": build_simple(secs, "From Design System to Design Intelligence", 3),
        "blueprint": build_simple(secs, "A Practical AI Design OS Blueprint", 2),
        "build_split": {
            k: bullets(next((s["body"] for s in secs if s["title"] == t), ""))
            for k, t in (("designer", "Designer-owned"), ("ai", "AI-assisted"),
                         ("shared", "Engineering-owned / shared"))
        },
        "codebase": measure_codebase(CODE),
    }
    OUT.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")

    print("wrote %s  (from %s, %d lines)" % (OUT.name, doc.name, data["source"]["lines"]))
    print("  layers            : %d" % len(data["layers"]))
    for L in data["layers"]:
        print("     %d %-18s ai=%-2d human=%-2d shared=%-2d groups=%d  (%s)"
              % (L["n"], L["name"], len(L["ai"]), len(L["human"]),
                 len(L["shared"]), len(L["groups"]), L["ai_label"] or "-"))
    print("  responsibility rows: %d" % len(data["matrix"]))
    print("  workflows         : old %d stages, new %d stages" % (
        len(data["workflows"].get("old", {}).get("stages", [])),
        len(data["workflows"].get("new", {}).get("stages", []))))
    for k in ("operating_model", "rituals", "governance", "metrics",
              "generations", "blueprint"):
        print("  %-18s: %d" % (k, len(data[k])))
    print("  gaps the doc flags: %d" % len(data["gaps"]))
    for g in data["gaps"][:6]:
        print("     [INPUT NEEDED] %s" % g[:70])
    c = data["codebase"]
    if c:
        print("  codebase (measured %s):" % c["measured"])
        print("     %d TS files, %s lines, %d routes, %d ui primitives"
              % (c["ts_files"], f"{c['loc']:,}", c["routes"], c["ui_files"]))
    else:
        print("  codebase          : NOT FOUND -- stats must not be published")


if __name__ == "__main__":
    sys.exit(main())
