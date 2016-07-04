#!/usr/bin/env python3
import glob
import os
import struct
import sys
import base64
import re
import io
import codecs

import asdis
import bgiop


def get_string(code, addr, pos0):
    pos1 = code.find(b'\x00', pos0)
    string = code[pos0:pos1].decode('cp932')
    # string = asdis.escape(string)
    return string

# def get_code_end(data):
#     pos = -1
#     while 1:
#         res = data.find(b'\x1B\x00\x00\x00', pos+1)
#         if res == -1:
#             break
#         pos = res
#     return pos + 4

def get_code_end(data):
    a, b = struct.unpack('<II', data[0x0c:0x14])
    if a == 3:
        return b
    else:
        raise Exception('code end unknown')

def error_handler(err):
    s = err.object
    c = s[err.start:err.end]
    if c == '\u30fb':
        return ('·', err.end)

    c = c.encode('gbk', 'backslashreplace')
    print('error code:', c)
    return (c, err.end)

codecs.register_error('gbk_err', error_handler)

def parse(data, texts):
    hdrsize = 0x1C + struct.unpack('<I', data[0x1C:0x20])[0]
    hdr = data[:hdrsize]
    code = data[hdrsize:]

    bgiop.clear_offsets()
    size = get_code_end(code)
    pos = 0

    code_out = io.BytesIO()
    string_out = io.BytesIO()
    strings = []
    stringsTable = {}

    def getStringOffset(s):
        if s in stringsTable:
            return stringsTable[s]
        o = string_out.tell() + size
        string_out.write(s.encode('gbk', 'gbk_err') + b'\0')
        stringsTable[s] = o
        return o

    def clearStrings():
        for s, o in strings:
            code_out.seek(o, 0)
            code_out.write(struct.pack('<I', getStringOffset(s)))
            code_out.seek(0, 2)
        strings.clear()

    while pos < size:
        addr = pos
        instr = code[addr:addr+4]
        op, = struct.unpack('<I', instr)
        if op not in bgiop.ops:
            raise Exception('size unknown for op %02x @ offset %05x' % (op, addr))
        pos += 4

        if op == 0x003: # push_string
            fmt, _, _ = bgiop.ops[op]
            n = struct.calcsize(fmt)

            instr += code[pos:pos+n]
            pos0 = struct.unpack(fmt, code[pos:pos+n])[0]
            s = get_string(code, addr, pos0)
            strings.append((s, code_out.tell()+4))
            
            pos += n
        elif op == 0x07F: # line
            fmt, _, _ = bgiop.ops[op]
            n = struct.calcsize(fmt)
            
            pos0, lno = struct.unpack(fmt, code[pos:pos+n])
            s = get_string(code, addr, pos0)
            o = getStringOffset(s)
            instr += struct.pack(fmt, o, lno)
            
            pos += n
        elif 0x140 <= op <= 0x160: # msg_::f_
            if op == 0x140:
                if len(strings) == 1:
                    t = texts.pop(0)
                    _, o = strings[0]
                    code_out.seek(o, 0)
                    code_out.write(struct.pack('<I', getStringOffset(t)))
                    code_out.seek(0, 2)
                elif len(strings) == 2:
                    t = texts.pop(0)

                    _, o = strings[0]
                    code_out.seek(o, 0)
                    code_out.write(struct.pack('<I', getStringOffset(t[0])))
                    _, o = strings[1]
                    code_out.seek(o, 0)
                    code_out.write(struct.pack('<I', getStringOffset(t[1])))

                    code_out.seek(0, 2)
                else:
                    raise Exception("len(strings) = %d" % len(strings))
                strings.clear()
            else:
                clearStrings()
        else:
            clearStrings()
            fmt, _, _ = bgiop.ops[op]
            if fmt:
                n = struct.calcsize(fmt)
                instr += code[pos:pos+n]
                pos += n

        code_out.write(instr)

    return hdr + code_out.getvalue() + string_out.getvalue()

def handleTexts(text):
    t = text[1]
    tt = re.split(r'\s*†\s*', t)
    if len(tt) == 2:
        t1 = tt[0].strip()
        t2 = asdis.unescape(tt[1].strip())
        return (t1, t2)
    else:
        t = asdis.unescape(t.strip())
        return t

def insert(file):
    fi = open(file, 'r', encoding='utf-8')
    texts = fi.read()
    fi.close()
    
    # print(texts)
    texts = re.findall(r'^●(\d+)●\s*(.*)', texts, re.MULTILINE)
    texts = map(handleTexts, texts)
    texts = list(texts)

    bin_file = os.path.splitext(file)[0]
    # print(bin_file)
    fo = open(bin_file, 'rb')
    data = fo.read()
    fo.close()

    out = parse(data, texts)

    fo = open(bin_file, 'wb')
    fo.write(out)
    fo.close()


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
