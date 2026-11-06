"""Render a gx3gen rung list as an ASCII ladder diagram.

The spec file (e.g. tools/conveyor.py) is read with ast, not executed, so its
write_project call does not run. Each rung is (branches, series, outputs) as in gx3gen.

usage: python -I tools/gx3ascii.py [SPEC.py]   (default: tools/conveyor.py)
"""
import ast
import os
import sys

CELL = 9  # width of one contact: '───┤ ├───'


def load_rungs(path):
    src = open(path, encoding='utf-8').read()
    lines = src.splitlines()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Assign) and any(getattr(t, 'id', None) == 'R' for t in node.targets):
            rungs = []
            for elt in node.value.elts:
                line = lines[elt.lineno - 1]
                note = line.split('#', 1)[1].strip() if '#' in line else ''
                rungs.append((ast.literal_eval(elt), note))
            return rungs
    raise SystemExit('no R = [...] in ' + path)


def contact(name):
    nc = name.startswith('/')
    dev = name[1:] if nc else name
    return dev.center(CELL), '───┤' + ('/' if nc else ' ') + '├───'


def output_box(o):
    parts = o.split()
    if len(parts) == 1:
        return '( %s )' % o
    if parts[0] == 'OUT':
        return '( %s )' % ' '.join(parts[1:])
    return '[ %s ]' % o


def content_end(rung):
    branches, series, _ = rung
    return 1 + max(len(b) for b in branches) * CELL + 1 + len(series) * CELL


def put(row, x, text):
    row[x:x + len(text)] = list(text)


def render_rung(rung, x_out, width):
    branches, series, outs = rung
    nb, no = len(branches), len(outs)
    nrows = max(nb, no)
    lab = [[' '] * width for _ in range(nrows)]
    wire = [[' '] * width for _ in range(nrows)]
    for r in range(nrows):
        lab[r][0] = lab[r][-1] = '│'
        wire[r][0] = '├' if r < nb else '│'
        wire[r][-1] = '┤' if r < no else '│'

    x_or = 1 + max(len(b) for b in branches) * CELL
    for r, row in enumerate(branches):
        x = 1
        for c in row:
            top, mid = contact(c)
            put(lab[r], x, top)
            put(wire[r], x, mid)
            x += CELL
        put(wire[r], x, '─' * (x_or - x))
    if nb > 1:
        wire[0][x_or] = '┬'
        for r in range(1, nb):
            lab[r][x_or] = '│'
            wire[r][x_or] = '┘' if r == nb - 1 else '┤'
    else:
        wire[0][x_or] = '─'

    x = x_or + 1
    for c in series:
        top, mid = contact(c)
        put(lab[0], x, top)
        put(wire[0], x, mid)
        x += CELL
    put(wire[0], x, '─' * (x_out - x))

    for r, o in enumerate(outs):
        if no > 1:
            wire[r][x_out] = '┬' if r == 0 else ('└' if r == no - 1 else '├')
            if r:
                lab[r][x_out] = '│'
        else:
            wire[r][x_out] = '─'
        box = '──' + output_box(o)
        put(wire[r], x_out + 1, box + '─' * (width - 2 - x_out - len(box)))
    out = []
    for r in range(nrows):
        out.append(''.join(lab[r]))
        out.append(''.join(wire[r]))
    return out


def render(rungs):
    x_out = max(content_end(r) for r, _ in rungs) + 2
    width = x_out + 1 + max(len(output_box(o)) for r, _ in rungs for o in r[2]) + 6
    lines = []
    for rung, note in rungs:
        # the spec comment ("4 run self-hold") opens a section; uncommented rungs continue it
        head = '│ ' + note if note else '│'
        lines.append(head + ' ' * (width - 1 - len(head)) + '│')
        lines.extend(render_rung(rung, x_out, width))
    end = '──[ END ]'
    lines.append('│' + ' ' * (width - 2) + '│')
    lines.append('├' + '─' * (x_out - 1) + '─' + end + '─' * (width - 2 - x_out - len(end)) + '┤')
    return '\n'.join(lines)


if __name__ == '__main__':
    spec = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'conveyor.py')
    sys.stdout.reconfigure(encoding='utf-8')
    print(render(load_rungs(spec)))
