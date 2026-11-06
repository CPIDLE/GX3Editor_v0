"""Render a gx3gen rung list as an ASCII ladder diagram in the GX Works3 display style.

GX Works3 elements drawn (names as in the GX Works3 Operating Manual):
- step number: the start step of each ladder block, left of the left rail (from gx3comp; blank if
  gx3comp cannot compile the rung)
- line statement: comment lines attached to a ladder block, drawn above it
- device comment: drawn under each contact / coil / instruction, wrapped at 8 columns, up to 4 lines
  (for an instruction, the comment of its destination for MOV, otherwise its first device)

The spec file (e.g. tools/conveyor.py) is read with ast, not executed, so its write_project call does
not run. It provides R = [(branches, series, outputs), ...] as in gx3gen, optional line statements as
trailing comments ("# <title> | <line>、<line>"), and an optional device comment dict DC.

usage: python -I tools/gx3ascii.py [SPEC.py]   (default: tools/conveyor.py)
"""
import ast
import os
import sys
import unicodedata

CELL = 9        # width of one contact: '───┤ ├───'
CMT_W = 8       # device comment columns per line
CMT_ROWS = 4    # device comment lines at most
GUTTER = 5      # step number column left of the rail


def load_spec(path):
    src = open(path, encoding='utf-8').read()
    lines = src.splitlines()
    rungs, dc = None, {}
    for node in ast.walk(ast.parse(src)):
        if not isinstance(node, ast.Assign):
            continue
        names = [getattr(t, 'id', None) for t in node.targets]
        if 'R' in names:
            rungs = []
            for elt in node.value.elts:
                line = lines[elt.lineno - 1]
                note = line.split('#', 1)[1].strip() if '#' in line else ''
                rungs.append((ast.literal_eval(elt), note))
        elif 'DC' in names:
            dc = ast.literal_eval(node.value)
    if rungs is None:
        raise SystemExit('no R = [...] in ' + path)
    return rungs, dc


def step_counts(rungs):
    """Steps per rung from gx3comp, or None when gx3comp cannot compile the program."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        from gx3comp import compile_rung
        return [sum(compile_rung(*r)[1]) for r, _ in rungs]
    except Exception:
        return None


def cw(ch):
    return 2 if unicodedata.east_asian_width(ch) in 'WF' else 1


def dw(s):
    """Display width: CJK wide/fullwidth characters take two columns."""
    return sum(cw(ch) for ch in s)


def wrap(text, cols=CMT_W, rows=CMT_ROWS):
    out, cur = [], ''
    for ch in text:
        if dw(cur) + cw(ch) > cols:
            out.append(cur)
            cur = ''
        cur += ch
    if cur:
        out.append(cur)
    return out[:rows]


def put(row, x, text):
    """Write text into a grid row; a wide character fills its second column with ''."""
    for ch in text:
        row[x] = ch
        if cw(ch) == 2:
            row[x + 1] = ''
        x += cw(ch)


def centered(text, width):
    pad = width - dw(text)
    return ' ' * (pad // 2) + text + ' ' * (pad - pad // 2)


def contact_parts(name):
    nc = name.startswith('/')
    dev = name[1:] if nc else name
    return dev, '───┤' + ('/' if nc else ' ') + '├───'


def output_box(o):
    parts = o.split()
    if len(parts) == 1:
        return '( %s )' % o
    if parts[0] == 'OUT':
        return '( %s )' % ' '.join(parts[1:])
    return '[ %s ]' % o


def output_dev(o):
    parts = o.split()
    if len(parts) == 1:
        return o
    return parts[-1] if parts[0] == 'MOV' else parts[1]


def content_end(rung):
    branches, series, _ = rung
    return 1 + max(len(b) for b in branches) * CELL + 1 + len(series) * CELL


def render_rung(rung, x_out, width, dc):
    branches, series, outs = rung
    nb, no = len(branches), len(outs)
    nrows = max(nb, no)

    # device comments per row -> row heights
    def cmt(dev):
        return wrap(dc.get(dev, ''))
    row_cmts = []
    for r in range(nrows):
        devs = [contact_parts(c)[0] for c in (branches[r] if r < nb else [])]
        if r == 0:
            devs += [contact_parts(c)[0] for c in series]
        if r < no:
            devs.append(output_dev(outs[r]))
        row_cmts.append(max((len(cmt(d)) for d in devs), default=0))
    tops = []
    y = 0
    for k in row_cmts:
        tops.append(y)
        y += 2 + k
    height = y
    grid = [[' '] * width for _ in range(height)]
    for g in grid:
        g[0] = g[-1] = '│'

    def wire_y(r):
        return tops[r] + 1

    def place(r, x, cellw, dev, symbol):
        put(grid[tops[r]], x, centered(dev, cellw))
        put(grid[wire_y(r)], x, symbol)
        for i, line in enumerate(cmt(dev)):
            put(grid[wire_y(r) + 1 + i], x, centered(line, cellw))

    def vertical(x, rows, chars):
        """Join rows at column x: chars = (first, middle, last); '│' on the lines between."""
        for i, r in enumerate(rows):
            grid[wire_y(r)][x] = chars[0] if i == 0 else (chars[2] if i == len(rows) - 1 else chars[1])
            if i:
                for yy in range(wire_y(rows[i - 1]) + 1, wire_y(r)):
                    grid[yy][x] = '│'

    for r in range(nrows):
        grid[wire_y(r)][0] = '├' if r < nb else '│'
        grid[wire_y(r)][-1] = '┤' if r < no else '│'

    x_or = 1 + max(len(b) for b in branches) * CELL
    for r, row in enumerate(branches):
        x = 1
        for c in row:
            dev, sym = contact_parts(c)
            place(r, x, CELL, dev, sym)
            x += CELL
        put(grid[wire_y(r)], x, '─' * (x_or - x))
    if nb > 1:
        vertical(x_or, list(range(nb)), '┬┤┘')
    else:
        grid[wire_y(0)][x_or] = '─'

    x = x_or + 1
    for c in series:
        dev, sym = contact_parts(c)
        place(0, x, CELL, dev, sym)
        x += CELL
    put(grid[wire_y(0)], x, '─' * (x_out - x))

    if no > 1:
        vertical(x_out, list(range(no)), '┬├└')
    else:
        grid[wire_y(0)][x_out] = '─'
    for r, o in enumerate(outs):
        box = output_box(o)
        put(grid[wire_y(r)], x_out + 1, '──' + box + '─' * (width - 4 - x_out - len(box)))
        for i, line in enumerate(cmt(output_dev(o))):
            put(grid[wire_y(r) + 1 + i], x_out + 3, line)
    return [''.join(g) for g in grid], wire_y(0)


def text_line(text, width):
    return ' ' * GUTTER + text + ' ' * (width - 1 - dw(text)) + '│'


def statement_lines(comment, width):
    """'title | line1、line2' -> line statements inside the rails, wrapped to the diagram width."""
    title, _, rest = (p.strip() for p in comment.partition('|'))
    out = [text_line('│ ' + title, width)] if title else []
    cur = ''
    for item in (rest.split('、') if rest else []):
        piece = item if not cur else '、' + item
        if cur and dw('│ ' + cur + piece) > width - 2:
            out.append(text_line('│ ' + cur, width))
            cur = item
        else:
            cur += piece
    if cur:
        out.append(text_line('│ ' + cur, width))
    return out


def render(rungs, dc):
    x_out = max(content_end(r) for r, _ in rungs) + 2
    width = x_out + 3 + max(max(len(output_box(o)) for r, _ in rungs for o in r[2]), CMT_W) + 4
    steps = step_counts(rungs)
    lines, step = [], 0
    for i, (rung, comment) in enumerate(rungs):
        # a statement with a title opens a rung group; a rung without one continues it
        if not comment.split('|')[0].strip():
            lines.append(text_line('│', width))
        if comment:
            lines.extend(statement_lines(comment, width))
        body, wy = render_rung(rung, x_out, width, dc)
        for j, b in enumerate(body):
            num = str(step) if (j == wy and steps) else ''
            lines.append(num.rjust(GUTTER - 1) + ' ' + b)
        if steps:
            step += steps[i]
    end = '──[ END ]'
    lines.append(text_line('│', width))
    lines.append((str(step) if steps else '').rjust(GUTTER - 1) + ' ' +
                 '├' + '─' * x_out + end + '─' * (width - 2 - x_out - len(end)) + '┤')
    return '\n'.join(lines)


if __name__ == '__main__':
    spec = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'conveyor.py')
    sys.stdout.reconfigure(encoding='utf-8')
    print(render(*load_spec(spec)))
