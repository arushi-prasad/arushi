"""Lift the WorkPerks design-system stylesheet out of the documentation file
and scope every selector under .wpds, so the real component CSS can be used
in the portfolio case study without colliding with the site's own wp-* classes
(.wp-status exists in both) or leaking tokens onto the page."""
import re, sys

SRC = "/Users/arushi.prasad/Desktop/Portfolio/02. Work/01. Workperks/Design System/workperks-design-system.html"
OUT = "/Users/arushi.prasad/Desktop/Portfolio/07. Interactive Portfolio/assets/css/wpds.css"
SCOPE = ".wpds"

html = open(SRC, encoding='utf-8').read()
def block(sid):
    m = re.search(r'<style id="%s">(.*?)</style>' % sid, html, re.S)
    return m.group(1)

css = block('wpTokens') + "\n" + block('wpType') + "\n" + block('wpComp')

def split_rules(s):
    """Yield (prelude, body_or_None). body None means a statement like @import."""
    out, depth, start, i = [], 0, 0, 0
    while i < len(s):
        c = s[i]
        if c == '{':
            if depth == 0:
                prelude_end = i
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                out.append((s[start:prelude_end], s[prelude_end+1:i]))
                start = i + 1
        i += 1
    tail = s[start:].strip()
    if tail:
        out.append((tail, None))
    return out

def scope_selector(sel):
    # Comments live in the prelude in this source ("/* --- Button --- */"
    # sits before the selector). Strip them: left in place they survive as
    # whitespace and still work, but a comma inside one would split a
    # selector in half.
    sel = re.sub(r'/\*.*?\*/', ' ', sel, flags=re.S).strip()
    if not sel: return sel
    parts = []
    for one in sel.split(','):
        one = one.strip()
        if not one: continue
        if one == ':root' or one == 'html' or one == 'body':
            parts.append(SCOPE)
        elif one.startswith(':root'):
            parts.append(SCOPE + one[len(':root'):])
        elif one.startswith('[data-theme'):
            parts.append(SCOPE + one)
        elif one.startswith('@'):
            parts.append(one)
        else:
            parts.append(SCOPE + ' ' + one)
    return ', '.join(parts)

def emit(rules, indent=''):
    out = []
    for prelude, body in rules:
        p = prelude.strip()
        if body is None:
            continue
        if p.startswith('@keyframes') or p.startswith('@font-face'):
            # keyframes keep their own name; font-face is replaced below
            if p.startswith('@font-face'):
                continue
            out.append(f'{indent}{p}{{{body}}}')
        elif p.startswith('@media') or p.startswith('@supports'):
            inner = emit(split_rules(body), indent + '  ')
            out.append(f'{indent}{p}{{\n{inner}\n{indent}}}')
        else:
            out.append(f'{indent}{scope_selector(p)}{{{body.strip()}}}')
    return '\n'.join(out)

scoped = emit(split_rules(css))

header = """/* ============================================================================
   wpds.css — the WorkPerks design system's own stylesheet, scoped.

   NOT WRITTEN BY HAND AND NOT TO BE EDITED HERE. It is lifted verbatim from
   the three <style> blocks of
     02. Work/01. Workperks/Design System/workperks-design-system.html
   by _extract_wpds.py, which prefixes every selector with .wpds.

   Why scope it: the documentation's classes are all wp-* and so are this case
   study's own (.wp-ia, .wp-pr, .wp-arch). .wp-status exists in both and means
   different things. Scoping also keeps the system's :root tokens from
   repainting the portfolio, which has its own.

   What this buys the page: the component specimens in chapter 14 are the real
   components running the real CSS, not a redraw of them. If the system
   changes, re-run the extractor.

   Anton and Figtree were data URIs inside that file; they are extracted to
   assets/fonts/ and declared below rather than re-inlined.
   ========================================================================= */

@font-face{
  font-family:'Anton';
  font-style:normal; font-weight:400; font-display:swap;
  src:url('../fonts/anton.woff2') format('woff2');
}
@font-face{
  font-family:'Figtree';
  font-style:normal; font-weight:300 900; font-display:swap;
  src:url('../fonts/figtree.woff2') format('woff2');
}

/* The scope itself. The documentation set these on :root / body. */
.wpds{
  font:var(--wp-body-md);
  letter-spacing:var(--wp-body-md-tracking);
  color:var(--wp-text-primary);
  -webkit-font-smoothing:antialiased;
}
.wpds *,.wpds *::before,.wpds *::after{ box-sizing:border-box; }

"""
open(OUT, 'w', encoding='utf-8').write(header + scoped + "\n")
print('wrote', OUT)
