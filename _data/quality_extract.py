"""Turn the Design Quality & Governance sources into one sanitised JSON file.

Three workbooks hold three related-but-different versions of the same UX
evaluation instrument, and only one of them was ever filled in. This script
keeps them apart on purpose: it never merges a definition sheet with a question
sheet, and never averages one workbook's scores into another's.

    python3 _data/quality_extract.py ["/path/to/2. Design Quality & Governance"]

Writes ``_data/quality.json``. Recomputes every published score from the
question-level ratings so the page cannot drift from the workbook.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from xlsx import load  # noqa: E402

OUT = Path(__file__).parent / "quality.json"
DEFAULT_SRC = ("/Users/arushi.prasad/Desktop/Portfolio/03. Design Ops/"
               "2. Design Quality & Governance")

# The workbooks are full of typos ("Learnabiity", "Enagagement", "preventaion").
# Headings are corrected for presentation; question and definition text is left
# exactly as written, because that is the artefact.
HEADING_FIX = {
    "Learnabiity": "Learnability",
    "Enagagement": "Engagement",
    "Error Handling & Guidence": "Error Handling & Guidance",
    "Error preventaion": "Error prevention",
    "Error preventaion & Handling": "Error prevention & Handling",
    "Interectivity": "Interactivity",
}


def tidy(v):
    return " ".join(str(v or "").split())


def fix(v):
    t = tidy(v)
    return HEADING_FIX.get(t, t)


def rows_of(g):
    return sorted(set(r for r, _ci in g))


def row_cells(g, r):
    return {c: v for (rr, _ci), (c, v) in g.items() if rr == r}


def split_factor(v):
    """'Discoverability Allow user to quickly ...' -> (name, definition)."""
    t = tidy(v)
    m = re.match(r"^([A-Za-z&\s]+?)\s+((?:Allow|Minimize|Captivate|Empower|Guide)\b.*)$", t)
    if m:
        return fix(m.group(1)), m.group(2)
    return fix(t), ""


CRITIQUE = {
    "attribution": {
        "title": "Share & Critique your way to a Culture of Collaboration",
        "author": "Shalini Raghunathan",
        "org": "3 Big Things",
        "role": "Co-Founder",
        "date": "February 8, 2025",
        "source": "5. Share & Critique for Collaboration.pdf, page 1",
        "note": "Third-party material. Not my work; a method I keep in the governance toolkit."
    },
    "setup": {
        "page": 2,
        "items": [
            "Core team of 3-10 people",
            "Have Shared context and/or work in related spaces",
            "Meet 2-3 times a week"
        ]
    },
    "choreography": {
        "page": 3,
        "stated_total": "45-55 mins",
        "custodian": "Custodian keeps time, facilitates the conversation, keeps it in scope.",
        "stages": [
            {
                "n": 1,
                "who": "Creator",
                "lo": 12,
                "hi": 15,
                "text": "Creator shares work - 12-15 mins",
                "detail": ""
            },
            {
                "n": 2,
                "who": "Collaborators",
                "lo": 3,
                "hi": 5,
                "text": "Collaborators ask for clarifications, if needed, briefly. 3-5 mins",
                "detail": ""
            },
            {
                "n": 3,
                "who": "Collaborators",
                "lo": 7,
                "hi": 10,
                "text": "Collaborators write feedback and post to the gallery in silence - 7-10 mins",
                "detail": "Includes time for folks to read and react to others' comments."
            },
            {
                "n": 4,
                "who": "Everyone",
                "lo": 15,
                "hi": 20,
                "text": "Round Robin feedback & conversation - 15-20 mins",
                "detail": "Each collaborator reads out their post-its (and explains briefly, if needed). Nominates the next collaborator."
            },
            {
                "n": 5,
                "who": "Creator",
                "lo": 5,
                "hi": 5,
                "text": "Creator records Action Items and schedules follow-ups - 5 mins",
                "detail": ""
            }
        ]
    },
    "roles": [
        "Creator",
        "Collaborator",
        "Custodian"
    ],
    "cs": [
        "Contextual",
        "Concise",
        "Curious"
    ],
    "mindsets": [
        {
            "role": "Creator",
            "page": 17,
            "by_c": {
                "Contextual": [
                    "Share what the problem is and who are you solving it for.",
                    "Tell a story about your work's journey, inspirations and challenges.",
                    "Define scope. Where are you in the project and design lifecycle?"
                ],
                "Concise": [
                    "What aspects of the design work are you seeking feedback on?",
                    "What aspects of the design work do you NOT want feedback on?",
                    "Structure your narrative to precisely articulate why you are seeking feedback at this time."
                ],
                "Curious": [
                    "Do not defend or solve. Feedback is a gift.",
                    "Listen to absorb and understand, not to respond.",
                    "Use \"Why?\" and \"Yes, and...\" to dig deeper and get the best out of the session.",
                    "Reflect and interpret. Translate feedback into action items that advance the work."
                ]
            }
        },
        {
            "role": "Collaborator",
            "page": 20,
            "by_c": {
                "Contextual": [
                    "Frame your feedback to focus on user's goals and objectives.",
                    "Stay within the scope of the feedback requested.",
                    "Critique the work, not the creator."
                ],
                "Concise": [
                    "Provide feedback that is specific, objective and tangible.",
                    "Share your opinions with justification.",
                    "Offer insight, not solutions."
                ],
                "Curious": [
                    "Highlight what's working well. Don't focus only on the negatives.",
                    "State your assumptions. Ask for clarifications. Probe.",
                    "Challenge to contribute, not to win. Disagree respectfully."
                ]
            }
        },
        {
            "role": "Custodian",
            "page": 22,
            "by_c": {
                "Contextual": [
                    "Stay neutral and objective.",
                    "Ensure collaborators move through the 4 Players roles.",
                    "Remember and remind the group of the “Why”."
                ],
                "Concise": [
                    "Keep time.",
                    "Redirect in case of detours.",
                    "Diffuse tensions."
                ],
                "Curious": [
                    "Ensure all voices are heard.",
                    "Challenge the group, if needed.",
                    "Critique the critique."
                ]
            }
        }
    ],
    "frameworks": [
        {
            "name": "Rose / Thorn / Bud",
            "page": 10,
            "parts": [
                [
                    "Rose",
                    "Success"
                ],
                [
                    "Thorn",
                    "Challenge"
                ],
                [
                    "Bud",
                    "Potential"
                ]
            ]
        },
        {
            "name": "I Like / I Wish / I Wonder",
            "page": 11,
            "parts": [
                [
                    "I like",
                    ""
                ],
                [
                    "I wish",
                    ""
                ],
                [
                    "I wonder",
                    ""
                ]
            ]
        },
        {
            "name": "4 Ls Retrospective (adapted)",
            "page": 12,
            "parts": [
                [
                    "Liked",
                    "What did the team like?"
                ],
                [
                    "Learned",
                    "What did the team learn?"
                ],
                [
                    "Lacked",
                    "What did the team lack?"
                ],
                [
                    "Longed for",
                    "What did the team long for?"
                ]
            ]
        },
        {
            "name": "Hits / Misses / Improvements / Ideas",
            "page": 13,
            "parts": [
                [
                    "Hits",
                    ""
                ],
                [
                    "Misses",
                    ""
                ],
                [
                    "Improvements",
                    ""
                ],
                [
                    "Ideas",
                    ""
                ]
            ]
        }
    ],
    "four_player": {
        "page": 19,
        "name": "Kantor's 4 Player Model",
        "roles": [
            "Mover",
            "Opposer",
            "Follower",
            "Bystander"
        ],
        "note": "Collaborators Move through all 4 roles"
    },
    "wip": {
        "page": 5,
        "examples": [
            "Research plan",
            "Discussion guide",
            "Research synthesis",
            "Research report",
            "Concept sketches",
            "Storyboard",
            "Wireframes",
            "Visual design",
            "Portfolio",
            "Social media post",
            "Frameworks",
            "Client/Stakeholder presentation deck",
            "Team initiative plan",
            "Workshop plan",
            "project/sprint plan",
            "Conference talk proposal"
        ],
        "formats": [
            "Physical Whiteboard",
            "Digital workspace / Miro board",
            "Document/Presentation",
            "Confluence page",
            "Paper sketch",
            "Paper prototype",
            "Low-fi digital wireframe",
            "Hi-fi digital wireframe"
        ]
    },
    "readiness": {
        "page": 7,
        "must": "When you can articulate your ideas visually and verbally.",
        "nice": [
            "When you have strong opinions, loosely held, about your work.",
            "When you have some clarity and some questions about your work."
        ]
    }
}


# --------------------------------------------------------------------------- #
def build_completed(book):
    """The one evaluation that was actually filled in, from the Template."""
    metrics = book["Evaluation Metrics"]
    dims, current = [], None
    for r in rows_of(metrics):
        cells = row_cells(metrics, r)
        if r == 1:
            continue
        b, a = cells.get("B", ""), cells.get("A", "")
        if b and not a:                                   # a factor heading row
            name, definition = split_factor(b)
            current = {"name": name, "definition": definition,
                       "questions": [], "recorded": None}
            dims.append(current)
            continue
        if not (a and b and current is not None):
            continue
        rating = cells.get("C", "")
        current["questions"].append({
            "n": int(float(a)),
            "text": tidy(b),
            "rating": float(rating) if rating else None,
        })
        if cells.get("D"):
            current["recorded"] = float(cells["D"])

    # Verify the sheet's own dimension averages against its question ratings.
    for d in dims:
        vals = [q["rating"] for q in d["questions"] if q["rating"] is not None]
        exact = (sum(vals) / len(vals)) if vals else None
        d["computed"] = round(exact, 4) if exact is not None else None
        d["matches"] = (d["recorded"] is not None and exact is not None
                        and abs(d["recorded"] - exact) < 1e-9)

    def num(v):
        try:
            return float(str(v).strip())
        except (TypeError, ValueError):
            return None

    report = book["Report"]
    rep_rows, total = [], None
    for r in rows_of(report):
        cells = row_cells(report, r)
        score, out_of = num(cells.get("E")), num(cells.get("D"))
        if score is None:                       # the header row
            continue
        if cells.get("C"):
            rep_rows.append({"name": fix(cells["C"]), "score": score,
                             "out_of": out_of if out_of is not None else 5.0})
        elif out_of is not None:
            total = {"score": score, "out_of": out_of}

    # And verify the report against the dimensions it claims to summarise.
    by_name = {d["name"]: d for d in dims}
    for row in rep_rows:
        d = by_name.get(row["name"])
        row["matches"] = bool(d and d["recorded"] is not None
                              and abs(d["recorded"] - row["score"]) < 1e-9)
    exact_total = sum(r["score"] for r in rep_rows)
    total_check = round(exact_total, 4)

    return {
        "dimensions": dims,
        "report": rep_rows,
        "total": total,
        "total_computed": total_check,
        "total_matches": total is not None and abs(total["score"] - exact_total) < 1e-9,
        "source": "Design_Evaluation_Template.xlsx / Evaluation Metrics + Report",
    }


def build_scale(book, sheet, label, source):
    """The 1-5 rating scale, with what each level means per dimension."""
    g = book[sheet]
    head_row = next(r for r in rows_of(g) if row_cells(g, r).get("C")
                    and not str(row_cells(g, r).get("A", "")).strip().isdigit())
    head = row_cells(g, head_row)
    cols = [c for c in ("C", "D", "E", "F", "G") if head.get(c)]
    levels = []
    for r in rows_of(g):
        if r <= head_row:
            continue
        cells = row_cells(g, r)
        a = tidy(cells.get("A", ""))
        if not re.fullmatch(r"\d+", a):
            continue
        levels.append({
            "level": int(a),
            "label": tidy(cells.get("B", "")),
            "by_dimension": {fix(head[c]): tidy(cells.get(c, "")) for c in cols},
        })
    return {"label": label, "source": source,
            "dimensions": [fix(head[c]) for c in cols], "levels": levels}


def build_instrument(g, label, source, text_col, kind):
    """A blank instrument: factors, their parameters, and the text per row."""
    out, current = [], None
    for r in rows_of(g):
        if r == 1:
            continue
        cells = row_cells(g, r)
        a, b = cells.get("A", ""), cells.get("B", "")
        if a:
            name, definition = split_factor(a)
            current = {"name": name, "definition": definition, "rows": []}
            out.append(current)
        if b and current is not None:
            current["rows"].append({"parameter": fix(b), "text": tidy(cells.get(text_col, ""))})
    return {"label": label, "source": source, "kind": kind, "factors": out,
            "count": sum(len(f["rows"]) for f in out)}


def build_snapshot(g, label, source):
    """Framework.xlsx Sheet5: the same review cut two ways, by factor and by
    parameter. No question-level rows sit behind it anywhere in the file."""
    by_factor, by_parameter = [], []
    for r in rows_of(g):
        cells = row_cells(g, r)
        if cells.get("C") and cells.get("D"):
            by_factor.append({"name": fix(cells["C"]), "score": float(cells["D"])})
        if cells.get("M") and cells.get("N"):
            by_parameter.append({"name": fix(cells["M"]), "score": float(cells["N"])})
    return {"label": label, "source": source,
            "by_factor": by_factor, "by_parameter": by_parameter}


def build_checklist(path):
    """The UX checklist, read straight out of the .pptx.

    The deck has no embedded media -- every slide is live text and shapes -- so
    no slide image can be exported from it. The page reconstructs it instead,
    and says so.
    """
    import zipfile
    from xml.etree import ElementTree as ET
    A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"

    z = zipfile.ZipFile(path)
    slides = sorted(
        (n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)),
        key=lambda n: int(re.search(r"(\d+)", n.split("/")[-1]).group(1)))

    out = []
    for i, n in enumerate(slides, start=1):
        root = ET.fromstring(z.read(n))
        lines = []
        for para in root.iter(A + "p"):
            t = tidy("".join(x.text or "" for x in para.iter(A + "t")))
            if t:
                lines.append(t)
        if not lines:
            continue
        title = lines[0]
        rest = lines[1:]
        # Slides carry a one-line rationale before the checks; the opening slide
        # is all checks. A line ending in "?" is a check, not a rationale.
        if rest and not rest[0].endswith("?") and len(rest) > 1:
            rationale, checks = rest[0], rest[1:]
        else:
            rationale, checks = "", rest
        out.append({"slide": i, "title": title, "rationale": rationale, "checks": checks})

    media = [n for n in z.namelist() if "/media/" in n]
    return {"source": "UX Checklist.pptx", "slides": out,
            "embedded_media": len(media),
            "cover": out[0]["title"] if out else "",
            "stages": out[1:] if len(out) > 1 else [],
            "check_count": sum(len(s["checks"]) for s in out[1:])}


def build_review_layers(g):
    """Sheet6 is four cells. Carried as the fragment it is, not inflated."""
    vals = [tidy(v) for (_r, _ci), (_c, v) in sorted(g.items()) if tidy(v)]
    return {"cells": vals, "source": "Framework.xlsx / Sheet6",
            "note": "Four cells only. The sheet names review layers but records "
                    "no criteria, cadence or results against them."}


# --------------------------------------------------------------------------- #
def main():
    src = Path(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SRC)
    ev = src / "Design Evaluation"
    if not ev.exists():
        raise SystemExit("source folder not found: %s" % ev)

    template = dict(load(ev / "Design_Evaluation_Template.xlsx"))
    metrics = dict(load(ev / "DesignEvaluationMetrics .xlsx"))
    framework = dict(load(ev / "Framework.xlsx"))

    data = {
        "checklist": build_checklist(src / "UX Checklist.pptx"),
        "critique": CRITIQUE,
        "completed": build_completed(template),
        "scale": build_scale(template, "Overview", "Rating scale, 1-5",
                             "Design_Evaluation_Template.xlsx / Overview"),
        "blank_questions": build_instrument(
            metrics["Design Evaluation"], "Question set, with parameters",
            "DesignEvaluationMetrics.xlsx / Design Evaluation", "C", "blank"),
        "definitions": build_instrument(
            framework["Sheet1 (2)"], "The model, as definitions",
            "Framework.xlsx / Sheet1 (2)", "C", "definitions"),
        "revised_questions": build_instrument(
            framework["Sheet4"], "Question set, revised fifth factor",
            "Framework.xlsx / Sheet4", "C", "blank"),
        "snapshot": build_snapshot(framework["Sheet5"], "A separate recorded snapshot",
                                   "Framework.xlsx / Sheet5"),
        "review_layers": build_review_layers(framework["Sheet6"]),
    }
    OUT.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")

    c = data["completed"]
    print("wrote %s" % OUT.name)
    print("  completed evaluation : %d dimensions, %d scored questions"
          % (len(c["dimensions"]), sum(len(d["questions"]) for d in c["dimensions"])))
    for d in c["dimensions"]:
        print("     %-28s recorded %-7s computed %-7s %s"
              % (d["name"], d["recorded"], d["computed"],
                 "ok" if d["matches"] else "MISMATCH"))
    print("     %-28s recorded %-7s computed %-7s %s"
          % ("TOTAL", round(c["total"]["score"], 4), c["total_computed"],
             "ok" if c["total_matches"] else "MISMATCH"))
    print("  rating scale         : %d levels x %d dimensions"
          % (len(data["scale"]["levels"]), len(data["scale"]["dimensions"])))
    for k in ("blank_questions", "definitions", "revised_questions"):
        i = data[k]
        print("  %-20s : %d factors, %d rows  (%s)"
              % (k, len(i["factors"]), i["count"], i["source"]))
    ck = data["checklist"]
    print("  ux checklist         : %d slides, %d checks, %d embedded images"
          % (len(ck["slides"]), ck["check_count"], ck["embedded_media"]))
    s = data["snapshot"]
    print("  separate snapshot    : %d factors, %d parameters"
          % (len(s["by_factor"]), len(s["by_parameter"])))
    print("  review layers        : %s" % ", ".join(data["review_layers"]["cells"]))


if __name__ == "__main__":
    sys.exit(main())
