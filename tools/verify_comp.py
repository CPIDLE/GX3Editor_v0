"""Compile the conveyor rungs and compare MIL / steps / code with what GX Works3 produced."""
import os
import sqlite3
import sys
import uuid

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
from gx3comp import compile_rung, END_MIL, END_CODE  # noqa: E402

ns = {'__file__': os.path.join(sys.argv[2], 'conveyor.py')}
exec(open(os.path.join(sys.argv[2], 'conveyor.py'), encoding='utf-8').read().split('write_project(')[0], ns)
R = ns['R']
post = sys.argv[1]

mil_rows = list(sqlite3.connect(post + '/dfa771664b93e92f_MilDB.db').execute('select id,pos,data from MIL order by pos'))
st = sqlite3.connect(post + '/7866903914637004290_StepInfo.db')
pou = open(post + '/ConvertData/7866903914637004290/PouPCode.pcode', 'rb').read()
pfp = open(post + '/ConvertData/4320229097374566601/ProgramFilePCode.pcode', 'rb').read()

# parse PouPCode records
recs, i = [], 1
while i < len(pou):
    ln = int.from_bytes(pou[i:i + 4], 'little')
    recs.append((str(uuid.UUID(bytes_le=pou[i + 5:i + 21])), pou[i + 21:i + ln]))
    i += ln

bad = 0
my_pfp = b''
for idx, rung in enumerate(R):
    gid, pos, real_mil = mil_rows[idx]
    mil, steps, code = compile_rung(*rung)
    real_steps = [s for (s,) in st.execute('select StepSize from T_Step where BlockID=? order by MilID',
                                            ('{' + gid.split('/')[1].upper() + '}',))]
    real_code = dict(recs)[gid.split('/')[1]]
    ok = (mil == real_mil, steps == real_steps, code == real_code)
    my_pfp += code
    if not all(ok):
        bad += 1
        print('MISMATCH rung', idx + 1, ok)
        if not ok[0]:
            print('  mine', mil)
            print('  real', real_mil)
        if not ok[1]:
            print('  steps', steps, real_steps)
        if not ok[2]:
            print('  mine', code.hex(' '))
            print('  real', real_code.hex(' '))
my_pfp += END_CODE
end_ok = (mil_rows[-1][2] == END_MIL, recs[-1][1] == END_CODE)
print('END ok', end_ok)
print('ProgramFilePCode identical:', my_pfp == pfp, len(my_pfp), len(pfp))
print('total steps mine', sum(sum(compile_rung(*r)[1]) for r in R) + 1)
print('rungs mismatched:', bad, 'of', len(R))
