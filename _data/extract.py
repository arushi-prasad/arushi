"""Turn the private planning workbooks into one sanitised JSON file.

The workbooks live outside this repository and are never published. This script
reads them, strips every personal name, drops the leave dates and the levelling
table, and writes ``_data/planning.json`` -- which is the only planning data the
site ever sees. Re-run it with the source folder mounted:

    python3 _data/extract.py "/path/to/1. Planning & Resource Management"

Nothing here derives a number the workbooks do not state. Where a source cell is
empty the value stays empty, so the page can show a dash instead of a guess.
"""
import datetime
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from xlsx import load  # noqa: E402

OUT = Path(__file__).parent / "planning.json"
EPOCH = datetime.date(1899, 12, 30)

# Every name in the workbooks, keyed by the first token, because the sheets spell
# the same person several ways ("Roshan Sinha" / "Roshan Kumar Sinha" / "Roshan
# Kumar"). The value is the discipline the Roles sheet records for them.
ALIAS = {"udhayakumar": "udhaya", "debadrdita": "debadrita", "patnayak": "pattanaik"}


def key(name):
    first = re.split(r"[\s.|,]+", str(name).strip().lower())[0]
    return ALIAS.get(first, first)


def serial_to_date(v):
    try:
        n = float(v)
    except (TypeError, ValueError):
        return None
    if not (40000 < n < 50000):
        return None
    return EPOCH + datetime.timedelta(days=int(n))


def nice(v):
    """A source date cell -> a readable date, without inventing precision."""
    d = serial_to_date(v)
    if d:
        return d.strftime("%-d %b %Y")
    s = str(v).strip()
    # The sheet also holds hand-typed days such as "4th July" with no year. The
    # surrounding serial dates place the sheet in 2024; the year is not invented,
    # it is the year every resolved date in the same columns carries.
    if re.match(r"^\d{1,2}(st|nd|rd|th)?\s+[A-Za-z]+$", s):
        return s + " 2024"
    return s


def scrub(text, people):
    """Replace every first name inside free text with its anonymous label.

    The OKR cells name collaborators inline ("Revisiting components with X, Y &
    Z"). The sentence is worth keeping; the names are not.
    """
    def swap(m):
        at, word = m.group(1), m.group(2)
        k = key(word)
        if k == "arushi":
            return "me"
        if k == "zia":
            return "the design lead"
        label = people.get(k)
        return label if label else (at + word)
    pattern = re.compile(r"(@?)\b([A-Za-z]{3,})\b")
    out = pattern.sub(
        lambda m: swap(m) if (key(m.group(2)) in people
                              or key(m.group(2)) in ("arushi", "zia")
                              or m.group(1) == "@") else m.group(0),
        text)
    return out


def cell(grid, row, col):
    for (r, _ci), (c, v) in grid.items():
        if r == row and c == col:
            return v
    return ""


def row_cells(grid, row):
    return {c: v for (r, _ci), (c, v) in grid.items() if r == row}


def rows_of(grid):
    return sorted(set(r for r, _ci in grid))


# --------------------------------------------------------------------------- #
# people
# --------------------------------------------------------------------------- #
def build_people(roles):
    """first-name key -> anonymous label, from the Roles sheet's own disciplines."""
    disciplines, squads = {}, {}
    for r in rows_of(roles):
        cells = row_cells(roles, r)
        name, role = cells.get("B", ""), cells.get("C", "")
        if not name or not role or name.upper() == "DESIGNERS":
            continue
        disciplines[key(name)] = role
        squads[key(name)] = cells.get("D", "")
    # The UI team is listed as a column, not as rows with a ROLE cell.
    for r in rows_of(roles):
        v = row_cells(roles, r).get("L", "")
        if v and v not in ("UI Team", "Arushi"):
            disciplines.setdefault(key(v), "UI Designer")
    return disciplines, squads


def label_people(disciplines, order):
    """Stable anonymous labels: UX 01.., UI 01.., in first-appearance order."""
    out, seen = {}, {"UX": 0, "UI": 0, "XX": 0}
    for name in order:
        k = key(name)
        if k in out:
            continue
        role = disciplines.get(k, "")
        band = "UI" if role.startswith("UI") else ("UX" if role else "XX")
        seen[band] += 1
        out[k] = "%s %02d" % (band if band != "XX" else "Designer", seen[band])
    return out


# --------------------------------------------------------------------------- #
# allocation
# --------------------------------------------------------------------------- #
def pm_labeller():
    """Anonymous, stable labels for the product managers named in the sheets."""
    seen = {}

    def label(raw):
        name = " ".join(str(raw).split())
        # Some cells hold a squad name or a dash rather than a person.
        if not name or name in ("-", "–") or name.lower() in (
                "drx", "hrx", "wellness", "labs", "dls"):
            return ""
        k = key(name)
        if k not in seen:
            seen[k] = "PM %02d" % (len(seen) + 1)
        return seen[k]

    label.seen = seen
    return label


def build_allocation(book, people, disciplines):
    """The template's schema, its one worked row, and the July snapshot's rows.

    Layout of ``Team Allocation sheet``: row 1 names the record fields in A-O and
    U; row 2 names five design-stage columns (P-T) grouped under the Status
    header, and also labels the dropdown lists parked off to the right in AH-AP;
    row 3 is the single worked example.
    """
    schema = book["Team Allocation sheet"]
    head, stage_head, ex = (row_cells(schema, 1), row_cells(schema, 2), row_cells(schema, 3))

    def ordered(row, cols):
        return [c for _ci, c in sorted((ci, c) for (r, ci), (c, _v) in schema.items()
                                       if r == row and c in cols)]

    field_cols = ordered(1, set("ABCDEFGHIJKLMNO") | {"U"})
    stage_cols = ordered(2, {"P", "Q", "R", "S", "T"})

    fields = [{"col": c, "name": " ".join(head[c].split())} for c in field_cols if c != "A"]
    stages = [{"col": c, "name": " ".join(stage_head[c].split())} for c in stage_cols]

    # Controlled vocabularies from the dropdown columns. Row 2 is each list's own
    # label; AJ/AK are the designer pick-lists and are deliberately not copied.
    vocab = {}
    for col, name in (("AH", "squad"), ("AI", "sub squad"), ("AL", "complexity"),
                      ("AM", "priority"), ("AN", "requirement"), ("AO", "category"),
                      ("AP", "type")):
        vals = [v for (r, _ci), (c, v) in sorted(schema.items()) if c == col and r > 2]
        if vals:
            vocab[name] = vals
    vocab["design stage status"] = [stage_head[c] for c in ordered(2, {"W", "X", "Y", "Z", "AA", "AB"})]

    # One worked row. It is the only record in any sheet that fills every field,
    # so it stands as the schema exemplar, with both designers anonymised.
    def ex_value(col):
        raw = ex.get(col, "")
        if not raw:
            return ""
        if col in ("N", "O"):
            return people.get(key(raw), "Designer")
        return nice(raw) if col in ("K", "L", "P") else " ".join(str(raw).split())

    exemplar = {
        "fields": [{"name": f["name"], "value": ex_value(f["col"])} for f in fields],
        "stages": [{"name": s["name"], "value": ex_value(s["col"])} for s in stages],
    }

    # The July snapshot: a leaner seven-column format, one row per work item.
    july = book["July Allocation Sheet"]
    pm_label = pm_labeller()
    records, owner = [], None
    for r in rows_of(july):
        if r == 1:
            continue
        cells = row_cells(july, r)
        if cells.get("B"):
            owner = cells["B"]
        story = cells.get("E", "")
        if not story:
            continue
        # Two cells in this column are status notes rather than work items, and
        # one of them records a person's leave. Neither is an allocation.
        if re.search(r"on leave|finished current stories", story, re.I):
            continue
        k = key(owner or "")
        start, target = serial_to_date(cells.get("H", "")), serial_to_date(cells.get("I", ""))
        records.append({
            "n": len(records) + 1,
            "story_id": " ".join(str(cells.get("D", "")).split()),
            "pm": pm_label(cells.get("F", "")),
            "owner": people.get(k, "Designer"),
            "discipline": disciplines.get(k, ""),
            "squad": " ".join(str(cells.get("C", "")).split()),
            "story": " ".join(str(story).split()),
            "status": " ".join(str(cells.get("G", "")).split()),
            "start": nice(cells.get("H", "")),
            "target": nice(cells.get("I", "")),
            "start_iso": start.isoformat() if start else "",
            "target_iso": target.isoformat() if target else "",
        })

    july_head = [" ".join(str(v).split())
                 for (r, _ci), (c, v) in sorted(july.items(), key=lambda x: x[0][1]) if r == 1]

    return {"fields": fields, "stages": stages, "vocab": vocab, "exemplar": exemplar,
            "july_fields": july_head, "records": records,
            "pm_count": len(pm_label.seen)}


# --------------------------------------------------------------------------- #
# availability
# --------------------------------------------------------------------------- #
def build_availability(book, people):
    sheet = next(g for n, g in book.items() if n.startswith("Weekly Leave Tracker"))
    header = row_cells(sheet, 3)
    marks = row_cells(sheet, 2)

    # Column order for the week columns, and the month each one belongs to.
    week_cols = sorted(
        [(ci, c) for (r, ci), (c, v) in sheet.items() if r == 3 and v.startswith("Week")]
    )
    month_at = {}
    for (r, ci), (c, v) in sheet.items():
        if r == 2:
            d = serial_to_date(v)
            if d:
                month_at[ci] = d.strftime("%b")
    months, current = [], None
    for ci, c in week_cols:
        current = month_at.get(ci, current)
        months.append(current or "")

    def state(v):
        s = str(v).strip().lower()
        if not s:
            return ""
        if s == "available":
            return "available"
        if s == "leave":
            return "leave"
        # Anything else is a hand-typed day or day range. The planning signal is
        # "part of this week is gone"; the dates themselves are personal and are
        # deliberately not carried into the JSON.
        return "partial"

    rows = []
    for r in rows_of(sheet):
        if r <= 3:
            continue
        cells = row_cells(sheet, r)
        name = cells.get("B", "")
        if not name:
            continue
        k = key(name)
        cs = [state(cells.get(c, "")) for _ci, c in week_cols]
        if not any(cs):
            continue
        rows.append({
            "res": "ME" if k == "arushi" else people.get(k, "Designer"),
            "self": k == "arushi",
            "squad": (cells.get("E", "") or cells.get("C", "") or "").strip(),
            "cells": cs,
        })

    tally = {"available": 0, "leave": 0, "partial": 0, "": 0}
    for row in rows:
        for c in row["cells"]:
            tally[c] += 1
    return {
        "months": months,
        "weeks": [header[c] for _ci, c in week_cols],
        "rows": rows,
        "tally": tally,
        "span": "%s - %s" % (
            (serial_to_date(marks.get("F", "")) or EPOCH).strftime("%b %Y"),
            (serial_to_date(marks.get("AN", "")) or EPOCH).strftime("%b %Y"),
        ),
    }


# --------------------------------------------------------------------------- #
# OKRs
# --------------------------------------------------------------------------- #
def split_blurb(v):
    """A theme cell is a short title, a newline, then a long description."""
    raw = str(v).strip()
    if "\n" in raw:
        head, rest = raw.split("\n", 1)
        return head.strip(" -–"), " ".join(rest.split())
    # A few track cells use " - " on one line instead of a newline.
    m = re.match(r"^(.{0,44}?)\s+[-–]\s+(.*)$", " ".join(raw.split()))
    if m and m.group(2):
        return m.group(1).strip(), m.group(2).strip()
    return " ".join(raw.split()), ""


def build_framework(grid, label, source):
    themes = []
    theme_at = {}
    for (r, ci), (c, v) in sorted(grid.items(), key=lambda x: x[0][1]):
        if r == 1:
            name, blurb = split_blurb(v)
            themes.append({"col": c, "ci": ci, "name": name, "blurb": blurb, "tracks": []})
            theme_at[ci] = len(themes) - 1
    bounds = [t["ci"] for t in themes] + [10 ** 6]
    for (r, ci), (c, v) in sorted(grid.items(), key=lambda x: x[0][1]):
        if r != 2:
            continue
        for i in range(len(themes)):
            if bounds[i] <= ci < bounds[i + 1]:
                name, blurb = split_blurb(v)
                themes[i]["tracks"].append({"col": c, "name": name, "blurb": blurb})
                break
    for t in themes:
        t.pop("ci", None)
    return {"label": label, "source": source, "themes": themes}


def build_cascade(grid, people):
    """Role rows under the themes, anonymised, with empties preserved."""
    out = []
    for r in rows_of(grid):
        if r < 3:
            continue
        cells = row_cells(grid, r)
        name = cells.get("A", "")
        if not name:
            continue
        k = key(name)
        entries = {c: scrub(" ".join(str(v).split()), people)
                   for c, v in cells.items() if c != "A" and str(v).strip()}
        out.append({
            "who": "Me" if k == "arushi" else
                   ("Design lead" if k == "zia" else people.get(k, "Designer")),
            "self": k == "arushi",
            "lead": k == "zia",
            "entries": entries,
            "filled": len(entries),
        })
    return out


def build_mine(grid, people):
    """Arushi's own quarter sheet: themes across, quarters down."""
    themes = [{"col": c, "name": " ".join(str(v).split())}
              for (r, _ci), (c, v) in sorted(grid.items(), key=lambda x: x[0][1]) if r == 1]
    tracks = [{"col": c, "name": " ".join(str(v).split())}
              for (r, _ci), (c, v) in sorted(grid.items(), key=lambda x: x[0][1]) if r == 2]

    quarters, current = [], None
    for r in rows_of(grid):
        cells = row_cells(grid, r)
        if r <= 2:
            continue
        head = cells.get("A", "")
        if head and head.startswith("Q"):
            current = {"name": head.replace("\n", " ").strip(), "items": {}}
            quarters.append(current)
        if current is None:
            continue
        for c, v in cells.items():
            if c == "A":
                continue
            text = scrub(" ".join(str(v).split()), people)
            if not text or text.startswith("All items marked"):
                continue
            current["items"].setdefault(c, []).append(text)
    return {"themes": themes, "tracks": tracks, "quarters": quarters}


# --------------------------------------------------------------------------- #
def main():
    src = Path(sys.argv[1] if len(sys.argv) > 1 else
               "/Users/arushi.prasad/Desktop/Portfolio/03. Design Ops/"
               "1. Planning & Resource Management")
    if not src.exists():
        raise SystemExit("source folder not found: %s" % src)

    alloc_book = dict(load(src / "Allocation Planning.xlsx"))
    okr_a = dict(load(src / "Everybody OKRs.xlsx"))
    okr_b = dict(load(src / "Everybody OKRs1.xlsx"))

    disciplines, _squads = build_people(alloc_book["Roles"])

    # Label people in the order the July sheet introduces them, then absorb any
    # name that only appears in the tracker or the OKR sheets.
    july = alloc_book["July Allocation Sheet"]
    order = [v for (r, _ci), (c, v) in sorted(july.items()) if c == "B" and r > 1]
    tracker = next(g for n, g in alloc_book.items() if n.startswith("Weekly Leave Tracker"))
    order += [v for (r, _ci), (c, v) in sorted(tracker.items()) if c == "B" and r > 3]
    order += [v for (r, _ci), (c, v) in sorted(okr_a["OKRs"].items()) if c == "A" and r >= 3]
    order = [n for n in order if key(n) not in ("arushi", "zia", "designer")]
    people = label_people(disciplines, order)

    data = {
        "source": {
            "files": ["Allocation Planning.xlsx", "Everybody OKRs.xlsx", "Everybody OKRs1.xlsx"],
            "sheets": sorted(alloc_book) + ["OKRs", "Arushi Prasad", "Sheet1"],
            "note": "Private workbooks. Names removed, leave dates reduced to a "
                    "three-state signal, levelling table excluded.",
        },
        "allocation": build_allocation(alloc_book, people, disciplines),
        "availability": build_availability(alloc_book, people),
        "okr": {
            "a": dict(build_framework(okr_a["OKRs"], "Framework as first written",
                                      "Everybody OKRs.xlsx / OKRs"),
                      cascade=build_cascade(okr_a["OKRs"], people)),
            "b": build_framework(okr_b["Sheet1"], "Framework as later revised",
                                 "Everybody OKRs1.xlsx / Sheet1"),
            "mine": build_mine(okr_a["Arushi Prasad"], people),
        },
        "roster": {
            "counted": len(people),
            "disciplines": sorted(set(disciplines.values())),
        },
    }

    OUT.write_text(json.dumps(data, indent=1, sort_keys=False) + "\n", encoding="utf-8")

    a = data["allocation"]
    v = data["availability"]
    print("wrote %s" % OUT.name)
    print("  allocation records  %d  (squads %d, statuses %d)" % (
        len(a["records"]), len(set(r["squad"] for r in a["records"])),
        len(set(r["status"] for r in a["records"] if r["status"]))))
    print("  availability        %d resources x %d weeks  %s" % (
        len(v["rows"]), len(v["weeks"]), v["span"]))
    print("  okr framework A     %d themes / %d tracks / %d role rows" % (
        len(data["okr"]["a"]["themes"]),
        sum(len(t["tracks"]) for t in data["okr"]["a"]["themes"]),
        len(data["okr"]["a"]["cascade"])))
    print("  okr framework B     %d themes / %d tracks" % (
        len(data["okr"]["b"]["themes"]),
        sum(len(t["tracks"]) for t in data["okr"]["b"]["themes"])))
    print("  my own sheet        %d quarters" % len(data["okr"]["mine"]["quarters"]))
    print("  people anonymised   %d" % len(people))


if __name__ == "__main__":
    sys.exit(main())
