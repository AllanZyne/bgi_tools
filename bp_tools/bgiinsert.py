#!/usr/bin/env python3
import glob
import os
import struct
import sys
import base64
import re
import io

import asdis
import bgiop


def parse(data, texts):
    hdrsize = 0x1C + struct.unpack('<I', data[0x1C:0x20])[0]
    hdr = data[:hdrsize]
    code = data[hdrsize:]

    bgiop.clear_offsets()
    size = get_code_end(code)
    pos = 0

    code_out = io.BytesIO()
    string_out = io.BytesIO()

    while pos < size:
        addr = pos
        instr = code[addr:addr+4]
        op, = struct.unpack('<I', instr)
        if op not in bgiop.ops:
            raise Exception('size unknown for op %02x @ offset %05x' % (op, addr))
        pos += 4

        if op == 0x003: # push_string
            fmt, _, _ = bgiop.ops[op]
            
            pos0 = struct.unpack(fmt, code[pos:pos+n])[0]
            s = get_string(code, addr, pos0)
            strings.append(s)

            n = struct.calcsize(fmt)
            pos += n
        elif 0x140 <= op <= 0x160: # msg_::f_
            if op == 0x140: #or op == 0x143 or op == 0x151 or op == 0x150:
                if len(strings) == 1:
                    texts.append({ "name":None, "text":strings[0], "opcode":op })
                elif len(strings) == 2:
                    texts.append({ "name":strings[0], "text":strings[1], "opcode":op })
        else:
            strings.clear()
            fmt, _, _ = bgiop.ops[op]
            if fmt:
                n = struct.calcsize(fmt)
                pos += n

        code_out.write(instr)

def handleTexts(text):
    t = text[1]
    tt = re.split(r'\s*†\s*', t)
    return tt

def insert(file):
    fi = open(file, 'r', encoding='utf-8')
    texts = fi.read()
    fi.close()
    
    # print(texts)
    texts = re.findall(r'^●(\d+)●\s(.*)', texts, re.MULTILINE)
    texts = map(handleTexts, texts)

    bin_file = os.path.splitext(file)[0] + '._bp'
    fo = open(bin_file, 'rb')
    data = fo.read()
    fo.close()

    out = parse(data, texts)

    # fbp = open(bp_file, 'wb')
    # fbp.write(out)
    # fbp.close()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: bgidump.py <file(s)>')
        print('(only extension-less files amongst <file(s)> will be processed)')
        sys.exit(1)
    for arg in sys.argv[1:]:
        for script in glob.glob(arg):
            base, ext = os.path.splitext(script)
            if ext == '.txt' and os.path.isfile(script):
                print('Disassembling %s...' % script)
                insert(script)
