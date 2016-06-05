#!/usr/bin/env python3
import glob
import os
import struct
import sys
import base64

import asdis
import bgiop

def parse(code):
    pass

def out(f, texts):
    pass

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

    ofile = os.path.splitext(file)[0] + '.bsd'
    fo = open(ofile, 'w', encoding='utf-8')
    out(fo, texts)
    fo.close()
    pass


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: bgidis.py <file(s)>')
        print('(only extension-less files amongst <file(s)> will be processed)')
        sys.exit(1)
    for arg in sys.argv[1:]:
        for script in glob.glob(arg):
            base, ext = os.path.splitext(script)
            if not ext and os.path.isfile(script):
                print('Disassembling %s...' % script)
                dump(script)
