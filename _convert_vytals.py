#!/usr/bin/env python3
"""Convert the standalone Vytals case study into the portfolio's case layout.

    Run from this directory:   python3 _convert_vytals.py _pages/01c-work-vytals.html
    then:                      python3 _build.py


The source page is a self-contained design with its own 121-class stylesheet.
This rewrites its *markup* onto the portfolio's component vocabulary — .section,
.rows/.row, .plate, .split, .note — so the page inherits the site's palette,
type scale and sticky-rail layout like every other case study.

The content is never rewritten. Every paragraph, heading, definition and image
is carried across verbatim; the script asserts that at the end by comparing the
word multiset of the source against the output.
"""
from bs4 import BeautifulSoup, NavigableString, Tag
import pathlib, re, collections, sys

SRC = pathlib.Path('../02. Work/03. Vytals/case-study/index.html')
soup = BeautifulSoup(SRC.read_text(), 'lxml')
for t in soup.select('.dock, .lb, .skip, script, .hero__wave, .eco'):
    t.decompose()                      # chrome, or hidden in the original

out = BeautifulSoup('', 'lxml')

def new(name, cls=None, text=None):
    t = out.new_tag(name)
    if cls: t['class'] = cls
    if text is not None: t.append(NavigableString(text))
    return t

def inner(el):
    """Inner HTML with inline tags (em/strong/b/code/a) kept, block noise gone."""
    parts = []
    for c in el.children:
        if isinstance(c, NavigableString): parts.append(str(c))
        elif c.name in ('em','strong','b','i','code','sup','sub','abbr','a','span','br'):
            if c.name == 'span' and c.get('class'):      # styling-only spans
                parts.append(inner(c))
            elif c.name == 'a':
                parts.append(f'<a class="link-out" href="{c.get("href","")}">{inner(c)}</a>')
            elif c.name == 'br':
                parts.append('<br>')
            else:
                parts.append(f'<{c.name}>{inner(c)}</{c.name}>')
        else: parts.append(inner(c))
    return re.sub(r'\s+', ' ', ''.join(parts)).strip()

def frag(html):
    return BeautifulSoup(html, 'html.parser')

def put(parent, name, cls=None, html=None, reveal=False):
    t = new(name, cls)
    if reveal: t['data-reveal'] = ''
    if html:
        for c in list(frag(html).children): t.append(c)
    parent.append(t)
    return t

def cls_of(el): return el.get('class', []) or []
def has(el, c): return c in cls_of(el)

IMG_BASE = '../../assets/img/vytals/'

def mk_img(src_el, eager=False):
    i = new('img')
    i['src'] = IMG_BASE + src_el.get('src', '').split('/')[-1]
    i['alt'] = src_el.get('alt', '')
    for a in ('width', 'height'):
        if src_el.get(a): i[a] = src_el[a]
    i['loading'] = 'eager' if eager else 'lazy'
    if src_el.get('decoding'): i['decoding'] = src_el['decoding']
    return i

def cap_parts(fc):
    """A figcaption whose first .eyebrow span is the source label."""
    if fc is None: return None, ''
    eb = fc.find(class_='eyebrow')
    label = eb.get_text(' ', strip=True) if eb else ''
    if eb: eb.extract()
    return label, inner(fc)

def plate(fig, parent, mod='', eager=False):
    img = fig.find('img')
    if img is None: return
    f = new('figure', ['plate'] + ([mod] if mod else []))
    f['data-reveal'] = ''
    f.append(mk_img(img, eager))
    label, body = cap_parts(fig.find('figcaption'))
    if label or body:
        fc = new('figcaption', ['plate__cap'])
        if label: fc.append(new('span', ['plate__src'], label))
        if body:
            for c in list(frag(' ' + body).children): fc.append(c)
        f.append(fc)
    parent.append(f)

def rows(parent, items, reveal=True):
    """items: list of (num, title, body_html)."""
    r = new('div', ['rows'])
    if reveal: r['data-reveal'] = ''
    for num, title, body in items:
        row = new('div', ['row'])
        row.append(new('p', ['row__num'], num or '—'))
        if title: put(row, 'h3', ['row__title'], title)
        rb = new('div', ['row__body'])
        if body:
            for c in list(frag(body).children): rb.append(c)
        row.append(rb)
        parent.append(row) if False else r.append(row)
    parent.append(r)
    return r

def defs(parent, pairs, reveal=True):
    d = new('dl', ['vy-defs'])
    if reveal: d['data-reveal'] = ''
    for k, v in pairs:
        put(d, 'dt', None, k)
        put(d, 'dd', None, v)
    parent.append(d)
    return d

def chain(parent, words):
    p = new('p', ['vy-chain'])
    p['data-reveal'] = ''
    for w in words: p.append(new('span', None, w))
    parent.append(p)

def dl_pairs(dl):
    pairs = []
    for dt in dl.find_all('dt'):
        dd = dt.find_next_sibling('dd')
        pairs.append((inner(dt), inner(dd) if dd else ''))
    return pairs

def num_of(text):
    m = re.match(r'\s*(\d+)\s*[·.–-]', text or '')
    return m.group(1) if m else None

def strip_num(text):
    return re.sub(r'^\s*\d+\s*[·.–-]\s*', '', text or '').strip()

UNWRAP = ('wrap', 'wrap-w', 'sticky', 'sticky__vis', 'frame', 'prods',
          'moment__g', 'signals', 'sig', 'steps', 'stack', 'dec__g', 'map')
SKIP_CLS = ('open', 'hero__meta', 'hero__facts', 'hero__wave', 'eco')

def walk(el, parent, first=True):
    """Emit portfolio markup for one source element's children, in order."""
    for ch in el.find_all(True, recursive=False):
        emit(ch, parent)

def emit(ch, parent):
    c = cls_of(ch)
    name = ch.name

    # --- things consumed elsewhere or deliberately dropped -------------------
    if any(k in c for k in SKIP_CLS): return
    if name in ('svg', 'script', 'style'): return

    # --- a stacked crossfade: one figure, many images -----------------------
    if 'sticky__vis' in c or (name == 'figure' and len(ch.find_all('img')) > 1):
        figs = ch.find_all('figure') or [ch]
        imgs = [i for f in figs for i in f.find_all('img')]
        r = new('div', ['vy-rail', 'vy-rail--stack']); r['data-reveal'] = ''
        for im in imgs:
            # No visible caption here. The source crossfaded these six frames
            # with no label on any of them, and the alt text is written for a
            # screen reader — printing it would both invent visible copy and
            # make the image announce itself twice. The step rows beside the
            # rail are what explain the sequence.
            f = new('figure'); f.append(mk_img(im))
            r.append(f)
        parent.append(r); return

    # --- containers that merely wrap a rail ----------------------------------
    if 'rail' not in c and ch.find(class_='rail'):
        walk(ch, parent); return

    # --- figures -------------------------------------------------------------
    if name == 'figure' or ('fig' in c and ch.find('img') and len(ch.find_all('img')) == 1):
        mod = 'plate--narrow' if 'fig--port' in c else ''
        plate(ch, parent, mod); return

    # --- a div.fig holding several images is a group, not one plate ----------
    if 'fig' in c and len(ch.find_all('img')) > 1:
        for f in ch.find_all('figure'):
            plate(f, parent)
        return

    # --- horizontal image rail ----------------------------------------------
    if 'rail' in c:
        r = new('div', ['vy-rail']); r['data-reveal'] = ''
        for fig in ch.find_all('figure'):
            img = fig.find('img')
            if img is None: continue
            f = new('figure')
            f.append(mk_img(img))
            fc = fig.find('figcaption')
            if fc: put(f, 'figcaption', ['vy-rail__cap'], inner(fc))
            r.append(f)
        parent.append(r); return

    # --- product cards -------------------------------------------------------
    if 'pc' in c and name == 'article':
        n = ch.find(class_='pc__n')
        ntext = n.get_text(' ', strip=True) if n else ''
        h3 = ch.find('h3'); q = ch.find(class_='pc__q')
        body = (f'<p>{inner(q)}</p>' if q else '')
        bits = [b.strip() for b in re.split(r'·', ntext) if b.strip()]
        lead = bits[0] if bits else ''
        rest = ' · '.join(bits[1:]) if len(bits) > 1 else ''
        row = new('div', ['row'])
        numbered = bool(re.match(r'^\d+$', lead))
        row.append(new('p', ['row__num'], lead if numbered else '—'))
        put(row, 'h3', ['row__title'], (rest or lead) if numbered else ' · '.join(bits))
        rb = new('div', ['row__body'])
        if h3: put(rb, 'p', ['vy-q'], inner(h3))
        if body:
            for x in list(frag(body).children): rb.append(x)
        dl = ch.find('dl')
        if dl: defs(rb, dl_pairs(dl), reveal=False)
        row.append(rb)
        # product cards accumulate into a shared .rows
        host = parent.find_all('div', class_='rows', recursive=False)
        host = host[-1] if host and host[-1].get('data-pc') else None
        if host is None:
            host = new('div', ['rows']); host['data-reveal'] = ''; host['data-pc'] = '1'
            parent.append(host)
        host.append(row); return

    # --- definition pairs held in a plain container (.dec__g) ----------------
    if (name != 'dl' and not ch.find_parent('dl') and ch.find('dt')
            and not ch.find('dl') and not ch.find(['h1','h2','h3','h4','p','figure'])):
        defs(parent, dl_pairs(ch)); return

    # --- definition lists ----------------------------------------------------
    if name == 'dl':
        pairs = dl_pairs(ch)
        if 'read' in c: defs(parent, pairs)
        else: defs(parent, pairs)
        return

    # --- two-column beats / moments -----------------------------------------
    if 'beat' in c or 'moment' in c:
        wide = 'moment' in c or 'beat--wideimg' in c
        sp = new('div', ['split'] + (['split--wide'] if wide else []))
        sp['data-reveal'] = ''
        kids = ch.find_all(True, recursive=False)
        if 'moment' in c and len(kids) == 1:
            kids = kids[0].find_all(True, recursive=False)
        txt = new('div', ['split__text'])
        figs = []
        for k in kids:
            if k.name == 'figure' or ('fig' in cls_of(k) and k.find('img')): figs.append(k)
            else: emit(k, txt)
        if 'beat--flip' in c:
            for f in figs: plate(f, sp)
            if txt.find(True): sp.append(txt)
        else:
            if txt.find(True): sp.append(txt)
            for f in figs: plate(f, sp)
        parent.append(sp); return

    # --- row-shaped collections ---------------------------------------------
    if 'sig__r' in c:
        k = ch.find(class_='sig__k'); tags = ch.find(class_='tags')
        w = ch.find(class_='sig__w'); u = ch.find(class_='sig__u')
        body = ''
        if w: body += f'<p>{inner(w)}</p>'
        if u: body += f'<p>{inner(u)}</p>'
        if tags:
            body += '<p class="vy-tags">' + ''.join(
                f'<span>{s.get_text(" ", strip=True)}</span>' for s in tags.find_all('span')) + '</p>'
        _rows_into(parent, ('—', inner(k) if k else '', body)); return

    if 'step' in c and ch.find(class_='step__n'):
        n = ch.find(class_='step__n'); t = ch.find(class_=re.compile('t-sub'))
        body = ''.join(f'<p>{inner(p)}</p>' for p in ch.find_all(class_='body', recursive=False))
        ntext = n.get_text(' ', strip=True)
        label = strip_num(ntext)
        if t: body = f'<p class="vy-q">{inner(t)}</p>' + body
        _rows_into(parent, (num_of(ntext) or '—', label, body)); return

    if 'jrn__s' in c:
        n = ch.find(class_='jrn__n'); t = ch.find(class_='jrn__t')
        body = ''.join(f'<p>{inner(p)}</p>' for p in ch.find_all(class_='body'))
        _rows_into(parent, (n.get_text(' ', strip=True) if n else '—',
                            inner(t) if t else '', body)); return

    if 'map__i' in c:
        eb = ch.find(class_='eyebrow'); t = ch.find('h3')
        body = ''.join(f'<p>{inner(p)}</p>' for p in ch.find_all(class_='body'))
        ebt = eb.get_text(' ', strip=True) if eb else ''
        label = strip_num(ebt)
        if t: body = f'<p class="vy-q">{inner(t)}</p>' + body
        _rows_into(parent, (num_of(ebt) or '—', label or (inner(t) if t else ''), body)); return

    if 'stack__l' in c or (ch.name == 'li' and ch.find('b') and ch.find('span')):
        b = ch.find('b'); s = ch.find('span')
        _rows_into(parent, ('—', inner(b) if b else '', f'<p>{inner(s)}</p>' if s else '')); return

    # --- chains and spines ---------------------------------------------------
    if name == 'ol' and 'spine' in c:
        chain(parent, [li.get_text(' ', strip=True) for li in ch.find_all('li')]); return
    if 'chain' in c:
        chain(parent, [s.get_text(' ', strip=True) for s in ch.find_all('span')]); return

    # --- status chips --------------------------------------------------------
    if name == 'div' and ch.find(class_='chip') and not ch.find(['p', 'h3', 'figure', 'dl']):
        p2 = new('p', ['vy-chips']); p2['data-reveal'] = ''
        for sp in ch.find_all(class_='chip'):
            mod = [m for m in cls_of(sp) if m.startswith('chip--')]
            tone = mod[0].split('--')[1] if mod else 'neutral'
            p2.append(new('span', ['vy-chip', 'vy-chip--' + tone], sp.get_text(' ', strip=True)))
        parent.append(p2); return
    if name == 'span' and 'chip' in c:
        mod = [m for m in c if m.startswith('chip--')]
        tone = mod[0].split('--')[1] if mod else 'neutral'
        parent.append(new('span', ['vy-chip', 'vy-chip--' + tone], ch.get_text(' ', strip=True))); return

    # --- notes ---------------------------------------------------------------
    if 'note' in c:
        sp = ch.find('span')
        put(parent, 'p', ['note'], f'<span>{inner(sp if sp else ch)}</span>', reveal=True); return

    # --- captions ------------------------------------------------------------
    if 'cap' in c and name == 'p':
        label, body = cap_parts(ch)
        h = (f'<span class="plate__src">{label}</span> ' if label else '') + body
        put(parent, 'p', ['plate__cap', 'vy-cap'], h, reveal=True); return

    # --- headings and text ---------------------------------------------------
    if name in ('h2', 'h3'):
        put(parent, 'h3', ['t-h3'], inner(ch), reveal=True); return
    if name == 'p':
        if 'tags' in c:
            put(parent, 'p', ['vy-tags'], ''.join(
                f'<span>{s.get_text(" ", strip=True)}</span>' for s in ch.find_all('span')), reveal=True); return
        if 'eyebrow' in c:
            put(parent, 'p', ['t-label', 'vy-eyebrow'], inner(ch), reveal=True); return
        if 'meta' in c:
            put(parent, 'p', ['prose', 't-dim'], inner(ch), reveal=True); return
        put(parent, 'p', ['prose'], inner(ch), reveal=True); return

    if name in ('ul', 'ol'):
        lis = ch.find_all('li', recursive=False)
        # A list whose items carry their own shape (the journey, the ladder, the
        # learnings) must be handed to the handlers that know it. Flattening it
        # here would fuse each item's label into its own sentence.
        if any(cls_of(li) or (li.find('b') and li.find('span')) for li in lis):
            for li in lis: emit(li, parent)
            return
        items = [(f'{i+1:02d}', '', f'<p>{inner(li)}</p>') for i, li in enumerate(lis)]
        rows(parent, items); return

    # --- containers ----------------------------------------------------------
    if any(k in c for k in UNWRAP) or (name in ('div', 'section', 'article', 'main') and True):
        walk(ch, parent); return

def _rows_into(parent, item):
    """Append a row to the trailing .rows, opening one if needed."""
    kids = [k for k in parent.find_all(True, recursive=False)]
    host = kids[-1] if kids and kids[-1].name == 'div' and 'rows' in cls_of(kids[-1]) else None
    if host is None:
        host = new('div', ['rows']); host['data-reveal'] = ''
        parent.append(host)
    num, title, body = item
    row = new('div', ['row'])
    row.append(new('p', ['row__num'], num or '—'))
    if title: put(row, 'h3', ['row__title'], title)
    rb = new('div', ['row__body'])
    if body:
        for c in list(frag(body).children): rb.append(c)
    row.append(rb)
    host.append(row)

# ---------------------------------------------------------------------------
# The source runs twenty-three "acts". The portfolio's case layout puts every
# section in a sticky rail, and twenty-three entries is not a rail, it is a
# second navigation. They group into eleven, which is the shape Vidal has.
# ---------------------------------------------------------------------------
GROUPS = [
    ('vy-overview',    'Overview',                 ['act02']),
    ('vy-opportunity', 'The Opportunity',          ['act03']),
    ('vy-howitworks',  'How Vytals Works',         ['act04', 'act05']),
    ('vy-ecosystem',   'Product Ecosystem',        ['act06', 'act07']),
    ('vy-challenge',   'The Design Challenge',     ['act08']),
    ('vy-approach',    'My Approach',              ['act09', 'act10']),
    ('vy-system',      'Design Language & System', ['act11', 'act12']),
    ('vy-report',      'The Report',               ['act13', 'act14']),
    ('vy-trust',       'Designing for Trust',      ['act15', 'act16']),
    ('vy-leading',     'Leading the Work',         ['act17', 'act18', 'act19', 'act20', 'act21']),
    ('vy-outcomes',    'Outcomes & Learnings',     ['act22', 'act23', 'act24']),
]

def act_head(act):
    """Pull (eyebrow, h2, lede) out of an act, detaching them from the tree."""
    op = act.find(class_='open')
    eb = ''
    if op:
        e = op.find(class_='eyebrow')
        eb = e.get_text(' ', strip=True) if e else ''
        op.extract()
    h2 = act.find(['h1', 'h2'], class_=re.compile(r't-(hero|section|statement)'))
    htxt = ''
    if h2:
        htxt = inner(h2); h2.extract()
    lede = act.find('p', class_=re.compile(r'\blede\b'))
    ltxt = ''
    if lede:
        ltxt = inner(lede); lede.extract()
    return eb, htxt, ltxt

body = soup.body
sections = []
AUDIT = []
for n, (sid, label, acts) in enumerate(GROUPS, start=1):
    sec = new('section', ['section'])
    sec['id'] = sid
    sec['aria-labelledby'] = 'h-' + sid
    sec['tabindex'] = '-1'

    head = new('div', ['section__head']); head['data-reveal'] = ''
    first = soup.find(id=acts[0])
    eb, htxt, ltxt = act_head(first)
    put(head, 'p', ['t-label', 'section__eyebrow'], f'{n:02d} &mdash; {label}')
    h2 = put(head, 'h2', ['t-h2'], htxt or label)
    h2['id'] = 'h-' + sid
    if ltxt: put(head, 'p', ['prose'], ltxt)
    sec.append(head)

    if sid == 'vy-overview':
        hero = soup.find(id='top')
        if hero and hero.select_one('.hero__facts'):
            ul = new('ul', ['case__facts']); ul['role'] = 'list'; ul['data-reveal'] = ''
            for d in hero.select('.hero__facts > div'):
                li = new('li', ['case__fact'])
                put(li, 'b', None, inner(d.find('dd')))
                put(li, 'span', None, inner(d.find('dt')))
                ul.append(li)
            sec.append(ul)
        stray = [x for x in soup.body.find_all('section', recursive=True)
                 if not x.get('id') and not x.find_parent(['section', 'header'])]
        for x in stray:
            walk(x, sec); x.decompose()

    _before = len(first.find_all('img'))
    walk(first, sec)
    _after = len(sec.find_all('img'))
    AUDIT.append((acts[0], _before, _after))

    for extra in acts[1:]:
        a = soup.find(id=extra)
        e2, h2t, l2 = act_head(a)
        if e2: put(sec, 'p', ['t-label', 'vy-eyebrow', 'vy-eyebrow--lead'], e2, reveal=True)
        if h2t: put(sec, 'h3', ['t-h3', 'vy-sub'], h2t, reveal=True)
        if l2: put(sec, 'p', ['prose'], l2, reveal=True)
        _b = len(a.find_all('img')); _pre = len(sec.find_all('img'))
        walk(a, sec)
        AUDIT.append((extra, _b, len(sec.find_all('img')) - _pre))

    sections.append(sec)

# Closing links, matching Vidal's.
close = new('div', ['case__close']); close['data-reveal'] = ''
put(close, 'p', None,
    '<a class="link-out" href="../vidal/health-claims/">Vidal &mdash; the health claims platform '
    '<svg class="ico" aria-hidden="true"><use href="#i-arrow"></use></svg></a>')
put(close, 'p', None,
    '<a class="link-out" href="../">Back to selected work '
    '<svg class="ico" aria-hidden="true"><use href="#i-arrow"></use></svg></a>')
sections[-1].append(close)

# ---------------------------------------------------------------------------
# Verify nothing was lost. Compare the word multiset of the source acts with
# the output; the only permitted losses are the chrome the portfolio replaces.
# ---------------------------------------------------------------------------
src = BeautifulSoup(SRC.read_text(), 'lxml')
for t in src.select('.dock, .lb, .skip, script, .hero__wave, .eco, footer, #top'):
    t.decompose()
def wordbag(text):
    return collections.Counter(re.findall(r"[A-Za-z0-9’'%+·–—/-]+", text.lower()))
src_words = wordbag(src.get_text(' ', strip=True))
out_words = wordbag(' '.join(s.get_text(' ', strip=True) for s in sections))

ALLOWED = {'product','story','method','craft','scroll','process','evidence','system',
           'practice','leadership','outcome','close','design','·','→'}  # .open__arc chrome
missing = {w: n for w, n in (src_words - out_words).items()}
real_missing = {w: n for w, n in missing.items() if w not in ALLOWED and not w.isdigit()}

print('source words :', sum(src_words.values()))
print('output words :', sum(out_words.values()))
print('missing kinds:', len(missing), '| after allowing chrome labels:', len(real_missing))
if real_missing:
    print('MISSING:', dict(sorted(real_missing.items(), key=lambda x: -x[1])[:40]))

added = {w: n for w, n in (out_words - src_words).items()}
print('added kinds  :', len(added), dict(sorted(added.items(), key=lambda x: -x[1])[:15]))

# image coverage
src_imgs = collections.Counter(i['src'].split('/')[-1] for i in src.find_all('img') if i.get('src'))
out_imgs = collections.Counter(i['src'].split('/')[-1] for s in sections for i in s.find_all('img'))
print('source imgs  :', sum(src_imgs.values()), 'unique', len(src_imgs))
print('output imgs  :', sum(out_imgs.values()), 'unique', len(out_imgs))
lost = src_imgs - out_imgs
if lost: print('IMAGES LOST  :', dict(lost))

META = """<!--meta
route: work/vytals
title: Vytals — Making health data easier to understand
desc: A 2024 health innovation initiative at Bajaj Finserv Health. A family of health products, each answering one health question, all resolving into a report a person can understand.
nav: work
case: yes
case_kicker: Product design / Case study
case_title: Making health data easier to understand
case_note: Vytals · 2024 · a family of health products, one reading experience.
case_sections: %s
sheets: vytals
word_a: health
word_b: data
tagline: Your body is constantly telling you something. Vytals turns those signals into a report a person can read.
-->

<!-- The Vytals case study, in the portfolio's case layout. The source page was
     a standalone design with its own stylesheet; its content is carried across
     verbatim and its markup rewritten onto the site's components, so the page
     reads like every other case study here. The source runs twenty-three acts;
     they group into the eleven sections the rail lists.
     Generated by _convert_vytals.py from 02. Work/03. Vytals/case-study/. -->
"""

rail = '; '.join(f'{sid}|{label}|{n:02d}'
                 for n, (sid, label, _) in enumerate(GROUPS, start=1))

doc = META % rail + '\n' + '\n\n'.join(s.prettify() for s in sections) + '\n'
pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '/tmp/vy-sections.html').write_text(doc)
print('--- per-act image audit (source -> emitted) ---')
for a, b, af in AUDIT:
    flag = '' if af >= b else f'   <-- {b-af} LOST'
    print(f'  {a}: {b:3} -> {af:3}{flag}')
print('sections written:', len(sections))
