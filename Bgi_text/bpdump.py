#!/usr/bin/env python3
import glob
import os
import struct
import sys

import asdis
import bpop
import bpconfig


def get_code_end(data):
    pos = -1
    while 1:
        res = data.find(b'\x17', pos+1)   # find last 0x17 pos
        if res == -1:
            break
        pos = res
    return pos+1

def get_string(code, addr, args):
    pos0 = addr + args
    pos1 = code.find(b'\x00', pos0)
    try:
        string = '>> ' + code[pos0:pos1].decode(bpconfig.senc)
    except Exception:
        string = '<< ' + code[pos0:pos1].decode(bpconfig.ienc)
    string = asdis.escape(string)
    return string

def parse(code):
    bpop.clear_offsets()
    texts = []
    size = get_code_end(code)
    pos = 0
    while pos < size:
        addr = pos
        op = code[addr]
        if op not in bpop.ops:
            raise Exception('size unknown for op %02x @ offset %05x' % (op, addr))
        pos += 1
        fmt, pfmt, fcn = bpop.ops[op]
        if fmt:
            n = struct.calcsize(fmt)
            if op == 0x05:      # push_string
                args, = struct.unpack(fmt, code[pos:pos+n])
                s = get_string(code, addr, args)
                texts.append(s)
            pos += n
    return texts

def out(fo, texts):
    ss = []
    for t in texts:
        ss.append(t)
        ss.append('\n')
        ss.append(t)
        ss.append('\n')
        ss.append('\n')
    ss.pop()
    fo.write(''.join(ss))

def dump_text(file):
    fbp = open(file, 'rb')
    hdrsize, = struct.unpack('<I', fbp.read(4))
    fbp.seek(hdrsize, 0)
    code = fbp.read()
    fbp.close()
    texts = parse(code)

    dump_file = os.path.splitext(file)[0] + '.txt'
    fo = open(dump_file, 'w', encoding='utf-8')
    out(fo, texts)
    fo.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: bp_dump.py <file(s)>')
        print('(only files with extension ._bp among <file(s)> will be processed)')
        sys.exit(1)
    for arg in sys.argv[1:]:
        for script in glob.glob(arg):
            base, ext = os.path.splitext(script)
            if ext == '._bp':
                print('Dumping %s...' % script)
                dump_text(script)
