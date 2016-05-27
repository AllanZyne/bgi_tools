import glob
import struct
import sys
import os

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: unpack.py <arc file(s)>')
        print('BGI/ unpack arc package')
        sys.exit(1)
    for arg in sys.argv[1:]:
        for file in glob.glob(arg):
            base, ext = os.path.splitext(file)
            if ext == '.arc':
                unpack(file)
