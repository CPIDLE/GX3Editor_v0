"""Compile the rung model of gx3gen.py into GX Works3 (FX5U) compiled artefacts:
MIL text, per-instruction step sizes and machine code.

All encodings were read from a program that GX Works3 1.007H compiled itself
(FX5U_conveyor.gx3, 2026-11-06). Anything not seen there raises an error.
"""
import re

from gx3gen import dev, output_spec  # noqa: F401  (output_spec kept for symmetry)

DEVCODE = {'M': 0x01, 'SM': 0x02, 'X': 0x10, 'Y': 0x11, 'D': 0x20, 'T': 0x42, 'C': 0x46}
CONTACT_OP = {('l', 'a'): 0x00, ('l', 'b'): 0x01, ('a', 'a'): 0x02, ('a', 'b'): 0x03,
              ('o', 'a'): 0x04}          # ORI (o,b) never observed -> not allowed
WORD_DEVS = {'T', 'C'}                  # RST on these takes 3 steps


def num_bytes(n):
    if 0 <= n < 0x80:
        return bytes([n])
    if 0x100 <= n < 0x8000:
        return n.to_bytes(2, 'little')
    raise ValueError(f'number encoding not observed for {n}')


def operand_dev(text):
    t, n = dev(text)
    body = bytes([0xa0, DEVCODE[t]]) + num_bytes(n)
    ln = len(body) + 2
    return bytes([ln]) + body + bytes([ln])


def operand_k(k):
    body = bytes([0xa0, 0xa1]) + num_bytes(k)
    ln = len(body) + 2
    return bytes([ln]) + body + bytes([ln])


def instr(group, steps, op, operands):
    return bytes([0x07, group, steps, op, 0x00, 0xff, 0x07]) + b''.join(operands)


def d_arg(n):
    return 'd{s=#:a=%d:vt=nn}' % n


def compile_contact(lt, text):
    role = 'b' if text.startswith('/') else 'a'
    name = text.lstrip('/')
    t, n = dev(name)
    if (lt, role) not in CONTACT_OP:
        raise ValueError(f'contact form not observed: {lt}{role} {text}')
    mil_tok = ['A' if role == 'a' else 'B', t]
    mil_el = 'mc{op=lct{op=#:lt=%s:ct=a:as=[as{vt=Abl}]}:as=[%s]}' % (lt, d_arg(n))
    code = instr(0x00, 0x02, CONTACT_OP[(lt, role)], [operand_dev(name)])
    return mil_tok, mil_el, 2, code


def compile_output(text):
    parts = text.split()
    if len(parts) == 1:
        t, n = dev(parts[0])
        return (['OUT', t], 'mc{op=cl{op=#:ct=a:as=[as{vt=Abl}]}:as=[%s]}' % d_arg(n), 2,
                instr(0x02, 0x02, 0x00, [operand_dev(parts[0])]))
    op, args = parts[0], parts[1:]
    if op in ('SET', 'RST'):
        t, n = dev(args[0])
        steps = 3 if (op == 'RST' and t in WORD_DEVS) else 2
        if op == 'SET' and t in WORD_DEVS:
            raise ValueError('SET on T/C not observed')
        return ([op, t], 'mc{op=cl{op=#:ct=a:as=[as{vt=Abl}]}:as=[%s]}' % d_arg(n), steps,
                instr(0x02, steps, 0x03 if op == 'SET' else 0x04, [operand_dev(args[0])]))
    if op == 'PLS':
        t, n = dev(args[0])
        return (['OUT', t], 'mc{op=cl{op=#:ct=p:as=[as{vt=Abl}]}:as=[%s]}' % d_arg(n), 3,
                instr(0x02, 0x03, 0x05, [operand_dev(args[0])]))
    if op == 'OUT':
        t, n = dev(args[0])
        k = int(args[1][1:])
        return (['OUT', t, 'K_1'],
                'mc{op=cl{op=#:ct=a:as=[as{vt=Abl}:as{vt=A16}]}:as=[%s:c{s=#:v=%d:si=s}]}' % (d_arg(n), k), 5,
                instr(0x02, 0x05, 0x01, [operand_dev(args[0]), operand_k(k)]))
    if op == 'INC':
        t, n = dev(args[0])
        return (['INC', t], 'mc{op=cl{op=#:ct=a:as=[as{vt=A16s}]}:as=[%s]}' % d_arg(n), 3,
                instr(0x22, 0x03, 0x00, [operand_dev(args[0])]))
    if op == 'MOV':
        (t1, n1), (t2, n2) = dev(args[0]), dev(args[1])
        return (['MOV', t1, t2],
                'mc{op=cl{op=#:ct=a:as=[as{vt=A16}:as{vt=A16}]}:as=[%s:%s]}' % (d_arg(n1), d_arg(n2)), 5,
                instr(0x24, 0x05, 0x00, [operand_dev(args[0]), operand_dev(args[1])]))
    if op == 'ZRST':
        (t1, n1), (t2, n2) = dev(args[0]), dev(args[1])
        return (['RST', t1, t2],
                'mc{op=cl{op=#:ct=a:as=[as{vt=Aea}:as{vt=Aea}]}:as=[%s:%s]}' % (d_arg(n1), d_arg(n2)), 4,
                instr(0x2b, 0x04, 0x19, [operand_dev(args[0]), operand_dev(args[1])]))
    raise ValueError(f'output not supported: {text}')


END_MIL = 'V1:1:3:END:ms{el=[mc{op=cl{op=#:ct=a}}]}'
END_CODE = bytes([0x07, 0x02, 0x01, 0x15, 0x00, 0xff, 0x07])


def compile_rung(branches, series, outputs):
    """-> (mil_text, [step sizes], code bytes)"""
    items = []
    if len(branches) > 1 and any(len(b) != 1 for b in branches):
        raise ValueError('OR branches with several contacts need ORB, not observed')
    for y, row in enumerate(branches):
        for x, c in enumerate(row):
            lt = 'l' if (y == 0 and x == 0) else ('o' if y > 0 else 'a')
            items.append(compile_contact(lt, c))
    for c in series:
        items.append(compile_contact('a', c))
    for o in outputs:
        items.append(compile_output(o))
    toks = [t for it in items for t in it[0]]
    mil = 'V1:%d:%s:%s:ms{el=[%s]}' % (len(toks), ':'.join(str(len(t)) for t in toks), ':'.join(toks),
                                       ':'.join(it[1] for it in items))
    return mil, [it[2] for it in items], b''.join(it[3] for it in items)
