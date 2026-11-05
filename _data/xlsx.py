"""A very small read-only .xlsx reader: stdlib only, values not formulas.

Returns sheets in workbook order as (name, {(row, col_index): (col_letter, value)}).
Enough for the planning workbooks, and deliberately not a general library.
"""
import re
import zipfile
from xml.etree import ElementTree as ET

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


def _col_index(ref):
    letters = re.match(r"[A-Z]+", ref).group(0)
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return letters, n


def _shared_strings(z):
    try:
        root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    out = []
    for si in root.findall(NS + "si"):
        out.append("".join(t.text or "" for t in si.iter(NS + "t")))
    return out


def load(path):
    z = zipfile.ZipFile(path)
    strings = _shared_strings(z)

    rels = {
        r.get("Id"): r.get("Target")
        for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    }
    sheets = []
    for sh in ET.fromstring(z.read("xl/workbook.xml")).iter(NS + "sheet"):
        target = rels.get(sh.get(REL + "id"), "")
        sheets.append((sh.get("name"), "xl/" + target.lstrip("/").replace("xl/", "", 1)))

    out = []
    for name, part in sheets:
        grid = {}
        for c in ET.fromstring(z.read(part)).iter(NS + "c"):
            ref = c.get("r")
            if not ref:
                continue
            v = c.find(NS + "v")
            if c.get("t") == "inlineStr" or c.find(NS + "is") is not None:
                text = "".join(t.text or "" for t in c.iter(NS + "t"))
            elif c.get("t") == "s" and v is not None:
                idx = int(v.text)
                text = strings[idx] if idx < len(strings) else ""
            elif v is not None:
                text = v.text or ""
            else:
                text = ""
            text = text.strip()
            if text:
                letters, ci = _col_index(ref)
                grid[(int(re.search(r"\d+", ref).group(0)), ci)] = (letters, text)
        out.append((name, grid))
    return out
