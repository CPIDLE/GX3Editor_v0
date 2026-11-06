"""Experiment: replace one rung in a GX-compiled .gx3 using only cc's compiler.

Updates LDDB (translated=1), MIL, PouPCode, ProgramFilePCode and the code section
of Program.qpg (+ its file-size field). Deliberately leaves the qpg 8-byte value
and the LZMA bundle untouched, to test whether GX Works3 / GX Simulator3 check them.

usage: python selfcompile_patch.py SRC.gx3 DST.gx3
"""
import os
import sqlite3
import sys
import tempfile
import uuid
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gx3gen import build_rung          # noqa: E402
from gx3comp import compile_rung       # noqa: E402

OLD = ([['M39']], [], ['Y4'])
NEW = ([['SM400']], [], ['Y4'])
QPG = 'ConvertData\\4320229097374566601\\Program.qpg'
PFP = 'ConvertData\\4320229097374566601\\ProgramFilePCode.pcode'
POU = 'ConvertData\\7866903914637004290\\PouPCode.pcode'

src, dst = sys.argv[1], sys.argv[2]
zin = zipfile.ZipFile(src)
files = {i.orig_filename.replace('/', '\\'): (i, zin.read(i)) for i in zin.infolist()}
tmp = tempfile.mkdtemp()

old_mil, old_steps, old_code = compile_rung(*OLD)
new_mil, new_steps, new_code = compile_rung(*NEW)
assert old_steps == new_steps
new_lddb, rows = build_rung(*NEW)


def patch_db(name, fn):
    info, data = files[name]
    p = os.path.join(tmp, 'x.db')
    open(p, 'wb').write(data)
    c = sqlite3.connect(p)
    fn(c)
    c.commit()
    c.close()
    files[name] = (info, open(p, 'rb').read())


mil_name = next(n for n in files if n.endswith('_MilDB.db'))
lddb_name = next(n for n in files if n.endswith('_LDDB.db'))
target = {}


def fix_mil(c):
    hits = [r for r in c.execute('select id from MIL where data=?', (old_mil,))]
    assert len(hits) == 1, hits
    target['id'] = hits[0][0]
    c.execute('update MIL set data=? where id=?', (new_mil, target['id']))


def fix_lddb(c):
    n = c.execute('update LadderBlocks set data=?, rowsize=?, translated=1 where id=?',
                  (new_lddb, rows, target['id'])).rowcount
    assert n == 1


patch_db(mil_name, fix_mil)
patch_db(lddb_name, fix_lddb)

# PouPCode: rewrite the one record
info, pou = files[POU]
gid = uuid.UUID(target['id'].split('/')[1])
out, i = bytearray(pou[:1]), 1
while i < len(pou):
    ln = int.from_bytes(pou[i:i + 4], 'little')
    rec = pou[i:i + ln]
    if rec[5:21] == gid.bytes_le:
        assert rec[21:] == old_code
        rec = (21 + len(new_code)).to_bytes(4, 'little') + rec[4:21] + new_code
    out += rec
    i += ln
files[POU] = (info, bytes(out))

# ProgramFilePCode and Program.qpg code section
for name in (PFP, QPG):
    info, data = files[name]
    assert data.count(old_code) == 1, name
    data = data.replace(old_code, new_code)
    if name == QPG:
        data = data[:12] + len(data).to_bytes(4, 'little') + data[16:]
    files[name] = (info, data)

zout = zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED)
for i in zin.infolist():
    name = i.orig_filename.replace('/', '\\')
    zi = zipfile.ZipInfo(i.orig_filename, i.date_time)
    zi.filename = i.orig_filename
    zi.compress_type = i.compress_type
    zi.external_attr = i.external_attr
    zi.create_system = i.create_system
    zout.writestr(zi, files[name][1])
zout.close()
print('patched block', target['id'], 'code', len(old_code), '->', len(new_code), 'bytes')
