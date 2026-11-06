"""Generate GX Works3 (FX5U) ladder blocks in the LDDB text format.

Encodings verified against blocks that GX Works3 1.007H itself saved
(reference/S_samples.gx3, 2026-11-06).

Rung model:
  branches: list of contact rows OR-ed together at the left, each a list of
            contact strings like 'X0', '/X1' (NC).  The OR group is followed by
            `series` contacts on row 0.
  outputs:  list of output strings: 'Y0', 'SET M20', 'RST C0', 'PLS M10',
            'OUT T0 K50', 'MOV C0 D1', 'INC D10', 'ZRST M30 M32'.
"""
import re
import sqlite3
import uuid
import zipfile

WIDTH = 12
CONTACT = 'e{{s=ce{{op=ct{{op=#:ct=a:as=[as{{vt=Abl}}]}}:args=[d{{s=#:a={n}:vt=nn}}]}}:pos={x},{y}}}'
WIRE = 'e{{s=-:pos={x},{y}}}'
OCTAL = {'X', 'Y'}


def dev(text):
    m = re.fullmatch(r'([A-Z]+)(\d+)', text)
    if not m:
        raise ValueError(text)
    t, num = m.group(1), m.group(2)
    return t, int(num, 8) if t in OCTAL else int(num)


def d_arg(n):
    return 'd{s=#:a=%d:vt=nn}' % n


def output_spec(text):
    """-> (header tokens, element body without pos, column)"""
    parts = text.split()
    if len(parts) == 1:                                   # coil
        t, n = dev(parts[0])
        body = 'ce{op=cl{op=#:ct=a:as=[as{vt=Abl}]}:args=[%s]}' % d_arg(n)
        return ['c', t], body, None          # coil: placed right after the contacts
    op, args = parts[0], parts[1:]
    if op in ('SET', 'RST', 'PLS'):
        t, n = dev(args[0])
        ct = 'p' if op == 'PLS' else 'a'
        body = 'ce{op=cl{op=#:ct=%s:as=[as{vt=Abl}]}:args=[%s]}' % (ct, d_arg(n))
        return [op, t], body, WIDTH - 2
    if op == 'INC':
        t, n = dev(args[0])
        body = 'ce{op=cl{op=#:ct=a:as=[as{vt=A16s}]}:args=[%s]}' % d_arg(n)
        return [op, t], body, WIDTH - 2
    if op == 'OUT':                                       # timer / counter with K
        t, n = dev(args[0])
        k = int(args[1][1:])
        body = ('ce{op=cl{op=#:ct=a:as=[as{vt=Abl}:as{vt=A16}]}:args=[%s:c{s=#:v=%d:si=s}]}'
                % (d_arg(n), k))
        return ['OUT__16', t, 'K_1'], body, WIDTH - 3
    if op in ('MOV', 'ZRST'):
        (t1, n1), (t2, n2) = dev(args[0]), dev(args[1])
        vt = 'A16' if op == 'MOV' else 'Aea'
        body = ('ce{op=cl{op=#:ct=a:as=[as{vt=%s}:as{vt=%s}]}:args=[%s:%s]}'
                % (vt, vt, d_arg(n1), d_arg(n2)))
        return [op, t1, t2], body, WIDTH - 3
    raise ValueError(text)


def build_rung(branches, series, outputs):
    """Return (data, rowsize). Elements are emitted row by row, column order."""
    nrows_or = len(branches)
    or_len = max(len(b) for b in branches)
    k = or_len + len(series)                      # column where outputs branch
    nrows = max(nrows_or, len(outputs))
    if nrows_or > 1 and len(outputs) > 1:
        raise ValueError('OR group and multiple outputs on one rung not supported')
    grid = {}                                     # (y) -> list of (x, tokens, element)
    verticals = []
    for y, row in enumerate(branches):
        for x, c in enumerate(row):
            role = 'b' if c.startswith('/') else 'a'
            t, n = dev(c.lstrip('/'))
            grid.setdefault(y, []).append((x, [role, t], CONTACT.format(n=n, x=x, y=y)))
        for x in range(len(row), or_len):         # pad short OR rows
            grid.setdefault(y, []).append((x, [], WIRE.format(x=x, y=y)))
        if y > 0:
            verticals.append('v{pos=%d,%d}' % (or_len, y))
    for i, c in enumerate(series):
        x = or_len + i
        role = 'b' if c.startswith('/') else 'a'
        t, n = dev(c.lstrip('/'))
        grid.setdefault(0, []).append((x, [role, t], CONTACT.format(n=n, x=x, y=0)))
    for y, out in enumerate(outputs):
        toks, body, col = output_spec(out)
        if col is None:
            col = k
        start = k
        for x in range(start, col):
            grid.setdefault(y, []).append((x, [], WIRE.format(x=x, y=y)))
        grid.setdefault(y, []).append((col, toks, 'e{s=%s:pos=%d,%d}' % (body, col, y)))
        if y > 0:
            verticals.append('v{pos=%d,%d}' % (k, y))
    tokens, elems = [], []
    for y in range(nrows):
        for x, toks, el in sorted(grid.get(y, []), key=lambda e: e[0]):
            tokens += toks
            elems.append(el)
    header = 'V1:%d:%s:%s:' % (len(tokens), ':'.join(str(len(t)) for t in tokens), ':'.join(tokens))
    data = header + 'cb{fg=fg{dim=%dx%d:es=[%s]' % (WIDTH, nrows, ':'.join(elems))
    if verticals:
        data += ':vs=[%s]' % ':'.join(verticals)
    return data + '}}', nrows


def write_project(base, dst, rungs, tmpdir):
    """Replace the program of `base` with `rungs` (list of (branches, series, outputs))."""
    import os
    zin = zipfile.ZipFile(base)
    zout = zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED)
    for i in zin.infolist():
        data = zin.read(i)
        if i.orig_filename.endswith('_LDDB.db'):
            p = os.path.join(tmpdir, 'gen.db')
            open(p, 'wb').write(data)
            c = sqlite3.connect(p)
            first_id = c.execute('select id from LadderBlocks where blocktype=0 order by pos').fetchone()[0]
            c.execute('delete from LadderBlocks where blocktype=0 and id<>?', (first_id,))
            for idx, (br, se, outs) in enumerate(rungs):
                d, rows = build_rung(br, se, outs)
                pos = 500000.0 + idx * 10000.0
                if idx == 0:   # reuse the existing block so StepInfo/pcode GUIDs stay referenced
                    c.execute('update LadderBlocks set pos=?, data=?, rowsize=?, translated=0 where id=?',
                              (pos, d, rows, first_id))
                else:
                    c.execute('insert into LadderBlocks(id,pos,blocktype,data,rowsize,translated,ConvTarget) '
                              'values(?,?,0,?,?,0,0)', ('_guid/' + str(uuid.uuid4()), pos, d, rows))
            c.commit()
            c.close()
            data = open(p, 'rb').read()
            os.remove(p)
        zi = zipfile.ZipInfo(i.orig_filename, i.date_time)
        zi.filename = i.orig_filename
        zi.compress_type = i.compress_type
        zi.external_attr = i.external_attr
        zi.create_system = i.create_system
        zout.writestr(zi, data)
    zout.close()
