#!/usr/bin/env python3
import glob
import os
import struct
import sys
import base64

import asdis
import bgiop


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

def get_string(code, addr, pos0):
    pos1 = code.find(b'\x00', pos0)
    string = code[pos0:pos1].decode('cp932')
    string = asdis.escape(string)
    return string

def parse(code):
    bgiop.clear_offsets()

    size = get_code_end(code)
    pos = 0
    texts = []
    strings = []
    while pos < size:
        addr = pos
        op, = struct.unpack('<I', code[addr:addr+4])
        if op not in bgiop.ops:
            raise Exception('size unknown for op %02x @ offset %05x' % (op, addr))
        pos += 4

        if op == 0x003: # push_string
            fmt, _, _ = bgiop.ops[op]
            n = struct.calcsize(fmt)

            pos0 = struct.unpack(fmt, code[pos:pos+n])[0]
            s = get_string(code, addr, pos0)
            s = asdis.escape(s)
            strings.append(s)

            pos += n
        elif 0x140 <= op <= 0x160: # msg_::f_
            if op == 0x140: #or op == 0x143 or op == 0x151 or op == 0x150:
                if len(strings) == 1:
                    texts.append({ "name":None, "text":strings[0], "opcode":op })
                elif len(strings) == 2:
                    texts.append({ "name":strings[0], "text":strings[1], "opcode":op })
                else:
                    raise Exception("len(strings) = %d" % len(strings))
            # else:
            #     raise Exception("msg_op=0x%x" % op)
            strings.clear()
        else:
            strings.clear()
            fmt, _, _ = bgiop.ops[op]
            if fmt:
                n = struct.calcsize(fmt)
                pos += n

    return texts

# import codecs
# def error_handler(err):
#     s = err.object
#     c = s[err.start:err.end]
#     if c == '\u30fb':
#         return ('·', err.end)
#     print('!!!!!!', c.encode('gbk', 'xmlcharrefreplace'))
# codecs.register_error('gbk_err', error_handler)

def out(fo, texts):
    for ii in range(len(texts)):
        t = texts[ii]
        line0 = '='*80 + '\n'
        line1 = ''
        if t['name']:
            line1 = (' %s' % t['name']) + ' † ' + t['text'] + '\n'
        else:
            line1 = ' ' + t['text'] + '\n'
        # print(line0)
        # fo.write(line0)
        fo.write(('○%05d○' % ii) + line1)
        # fo.write(line0)
        fo.write(('●%05d●' % ii) + line1)
        # fo.write(line0)
        fo.write('\n')

def dump(file):
    fi = open(file, 'rb')
    hdr_test = fi.read(0x20)
    if not hdr_test.startswith(b'BurikoCompiledScriptVer1.00\x00'):
        return

    hdrsize = 0x1C + struct.unpack('<I', hdr_test[0x1C:0x20])[0]
    fi.seek(hdrsize, 0)
    code = fi.read()
    fi.close()
    
    texts = parse(code)
    if not len(texts):
        return

    ofile = os.path.splitext(file)[0] + '.txt'
    fo = open(ofile, 'w', encoding='utf-8')
    out(fo, texts)
    fo.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: bgidump.py <file(s)>')
        print('(only extension-less files amongst <file(s)> will be processed)')
        sys.exit(1)
    for arg in sys.argv[1:]:
        for script in glob.glob(arg):
            base, ext = os.path.splitext(script)
            if not ext and os.path.isfile(script):
                print('Disassembling %s...' % script)
                dump(script)
