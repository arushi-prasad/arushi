#!/usr/bin/env python3
"""SUPERSEDED — kept for reference, and it no longer runs.

WorkPerks is now a page fragment like every other case study: edit
`_pages/01b-work-workperks.html` and run `_build.py`. That fragment carries the
content of the authored draft rewritten onto the site's own components, so the
page reads like Vytals and Vidal rather than like a second site inside this one.

This script did something different and incompatible: it copied the standalone
draft at 02. Work/01. Workperks/case-study/ wholesale into work/workperks/,
stylesheet and all, then stripped its authoring scaffolding from the copy.
Running it now would delete work/workperks/ and put the old standalone page
back, losing the build. The guard below stops that.

If you ever do want the old page again, delete the guard — the authored
original it copies from was never modified, so nothing has been lost.

Everything below this line is the original script, unchanged.
--------------------------------------------------------------------------
Publish the WorkPerks case study into the portfolio, minus its draft scaffolding.

The authored page at 02. Work/01. Workperks/ is a working draft. It carries an
internal audit section, 100-odd "[ADD … HERE]" placeholders and a set of
"Confirm" authoring markers, all of which render visibly. The page's own legend
describes those markers as "not public copy".

This copies the page to work/workperks/ and removes that scaffolding from the
copy only. The authored original is never written to, so the to-do list it
carries is not lost.

What is deliberately KEPT:
  - the Built / Specified / Concept / Verified status labels, which tell a
    reader what exists versus what is designed. They are the honest part.
  - every disclosure of the form "not measured, not claimed".

Run:  python3 _publish_workperks.py   (then python3 _build.py)
"""
from bs4 import BeautifulSoup
import pathlib, shutil, re, sys

sys.exit(
    "_publish_workperks.py is superseded and will not run.\n"
    "WorkPerks is built from _pages/01b-work-workperks.html like every other\n"
    "case study. Edit that fragment and run:  python3 _build.py\n"
    "Running this script would replace the built page with the old standalone\n"
    "draft. See the module docstring if that is genuinely what you want."
)

SRC = pathlib.Path('../02. Work/01. Workperks/case-study')
DST = pathlib.Path('work/workperks')
log = []

if DST.exists(): shutil.rmtree(DST)
shutil.copytree(SRC, DST)
log.append(f'copied {sum(1 for p in DST.rglob("*") if p.is_file())} files')

page = DST / 'index.html'
soup = BeautifulSoup(page.read_text(), 'lxml')

# ---- 1. the internal audit section ---------------------------------------
sec = soup.find(id='s-internal')
if sec:
    log.append(f'removed #s-internal ({len(sec.get_text(" ", strip=True).split())} words)')
    sec.decompose()
for a in soup.find_all('a', href='#s-internal'): a.decompose()

# ---- 2. the legend entries that define the authoring markers -------------
n = 0
for el in soup.select('.states__i, .legend__i'):
    if el.select_one('.tag--confirm, .tag--metric'):
        el.decompose(); n += 1
log.append(f'removed {n} legend entries defining Confirm / Metric needed')

# ---- 3. blocks whose whole content is an authoring note ------------------
# Each of these reads as an instruction to the author, not as copy.
WHOLE_BLOCK = [
    'Exact composition and titles',
    'This table is carried over from the earlier draft',
    'Which of the two documents is current',
    'An earlier draft of this page carried a figure for organisations',
]
n = 0
for el in list(soup.select('.tag--confirm')):
    par = el.parent
    if par is None: continue
    txt = re.sub(r'\s+', ' ', par.get_text(' ', strip=True))
    if any(k in txt for k in WHOLE_BLOCK):
        # a <dd> loses its <dt> too, or the label is left pointing at nothing
        if par.name == 'dd':
            dt = par.find_previous_sibling('dt')
            host = par.parent
            if dt: dt.decompose()
            par.decompose()
            if host and not host.get_text(strip=True): host.decompose()
        else:
            par.decompose()
        n += 1
log.append(f'removed {n} blocks that were entirely an authoring note')

# ---- 4. table cells whose only content is a marker -----------------------
n = 0
for el in list(soup.select('.tag--confirm')):
    par = el.parent
    if par is not None and par.name == 'td':
        par.clear(); par.append('—'); n += 1   # keep the row intact
log.append(f'removed {n} marker-only table cells (replaced with an em dash)')

# ---- 5. the remaining Confirm chips, and the clause each introduces ------
# The surrounding prose is hers and stays; only the open question goes.
CLAUSE = re.compile(
    r'\s*Confirm (?:whether|the current provider|adoption|current status|what is live)[^.]*\.?',
    re.I)
n = chips = 0
for el in list(soup.select('.tag--confirm')):
    par = el.parent
    if par is None: continue
    el.decompose(); chips += 1
    html = par.decode_contents()
    new = CLAUSE.sub('', html)
    # "[CONFIRM CURRENT SDK BEFORE PUBLISHING]" and friends
    new2 = re.sub(r'\[\s*CONFIRM[^\]]*\]\s*', '', new, flags=re.I)
    if new2 != html:
        par.clear()
        for c in list(BeautifulSoup(new2, 'html.parser').children): par.append(c)
        n += 1
log.append(f'removed {chips} Confirm chips and {n} open-question clauses')

# ---- 6. the [ADD … HERE] placeholders and the empty frames they sat in ---
FIELD = ('slot', 'slot__f', 'terr__f', 'dec__row')
BRACKET = re.compile(r'\[(?:ADD|CONFIRM)[^\]]*\]', re.I)
n = 0
for el in list(soup.find_all(True)):
    if el.find(True) or not el.get_text(strip=True): continue
    if not BRACKET.search(el.get_text()): continue
    host = el
    for anc in el.parents:
        if anc.name in ('body', 'html') or anc is None: break
        if any(c in FIELD for c in (anc.get('class') or [])): host = anc; break
        host = el
    (host if host is not el else el).decompose(); n += 1
log.append(f'removed {n} "[ADD … HERE]" placeholders and their empty frames')

# ---- 7. containers left empty by the above -------------------------------
n = 0
for _ in range(4):           # removals can empty their own parents
    for el in list(soup.select('.pair, .proof, .slot__fields, .terr__fields, .iter__fields, .itslot__pair')):
        if not el.get_text(strip=True) and not el.find('img'):
            el.decompose(); n += 1
log.append(f'removed {n} containers left empty')

out = str(soup)

# ---- 8. the back-link pointed outside the site ---------------------------
old = '../../../../00.Homepage/Final%20Homepage%20Design.html'
if old in out:
    out = out.replace(old, '../').replace('← Back to portfolio', '← Back to selected work')
    log.append('repointed the back-link to the Work index')

page.write_text(out)
print('\n'.join('  ' + l for l in log))
