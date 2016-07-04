#!/usr/bin/env python3
import glob
import os
import struct
import sys
import io
import codecs

__dir__ = os.path.dirname(os.path.realpath(__file__))
sys.path.append(__dir__ + '/../Bgi_asdis')

import asdis
import bpop
import config

def get_code_end(data):
    pos = -1
    while 1:
        res = data.find(b'\x17', pos+1)   # find last 0x17 pos
        if res == -1:
            break
        pos = res
    return pos+1

def insert(data, texts):
    hdrsize, = struct.unpack('<I', data[0:4])
    code = data[hdrsize:]

    bpop.clear_offsets()
    size = get_code_end(code)
    pos = 0
    pos_text = size
    while pos_text % 0x10 != 0:
        pos_text += 1
    
    code_out = io.BytesIO()
    string_out = io.BytesIO()

    while pos < size:
        addr = pos
        op = code[addr]
        if op not in bpop.ops:
            raise Exception('size unknown for op %02x @ offset %05x' % (op, addr))
        pos += 1

        instr = struct.pack('<B', op)
        fmt, pfmt, fcn = bpop.ops[op]
        if fmt:
            n = struct.calcsize(fmt)
            if op != 0x05: # push_string
                instr += code[pos:pos+n]
            else:
                args = struct.unpack(fmt, code[pos:pos+n])
                instr += struct.pack(fmt, pos_text-addr)

                line = texts.pop(0).split('\n')[1]
                line = asdis.unescape(line)
                if line[:3] == '>> ':
                    text = line[3:].encode(bpconfig.senc)
                    string_out.write(text + b'\0')
                    pos_text += len(text)+1
                elif line[:3] == '<< ':
                    text = line[3:].encode(bpconfig.ienc)
                    string_out.write(text + b'\0')
                    pos_text += len(text)+1
                else:
                    raise "格式错误！"
            pos += n

        code_out.write(instr)

    while string_out.tell() % 0x10 != 0:
        string_out.write(b'\0')
    while code_out.tell() % 0x10 != 0:
        code_out.write(b'\0')
    code_out.write(string_out.getvalue())
    out_code = code_out.getvalue()
    out_hdr = struct.pack('<IIII', 0x10, len(out_code), 0, 0)
    return out_hdr+out_code

def insert_text(file):
    fi = open(file, 'r', encoding='utf-8')
    texts = fi.read().split('\n\n')
    fi.close()
    
    bp_file = os.path.splitext(file)[0] + '._bp'
    fbp = open(bp_file, 'rb')
    data = fbp.read()
    fbp.close()

    out = insert(data, texts)

    fbp = open(bp_file, 'wb')
    fbp.write(out)
    fbp.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: bp_dump.py <file(s)>')
        print('(only files with extension .txt among <file(s)> will be processed)')
        sys.exit(1)
    for arg in sys.argv[1:]:
        for script in glob.glob(arg):
            base, ext = os.path.splitext(script)
            if ext == '.txt':
                print('Inserting %s...' % script)
                insert_text(script)