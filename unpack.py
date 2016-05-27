import glob
import struct
import sys
import os

import arc


def unpack(file):
    print()
    print('File:', file)

    f = open(file, 'rb')

    base, ext = os.path.splitext(file)
    os.makedirs(base, exist_ok=True)

    magic, fileCount = struct.unpack('<12sL', f.read(0x10))
    if not magic.startswith(b'PackFile'):
        return
    
    entryRaw = f.read(0x20*fileCount)
    # print(f.tell())
    dataOffset = f.tell()
    # dataRaw = f.read()
    print('Count:', fileCount)

    entryList = []

    for name, offset, size, _, _ in struct.iter_unpack('<16sLLLL', entryRaw):

        name = name.rstrip(b'\x00').decode('ascii')
        # print(entryName, offset, size)
        f.seek(dataOffset + offset)
        entryData = f.read(size)
        decryptData = None
        entryType = 'NONE'
        # print(len(entryData))

        if entryData.startswith(b'CompressedBG___'):
            # print('CompressedBG___', size)
            entryType = 'CompressedBG___'
            entryData = arc.cbg_decrypt(entryData)
            name += '.png'
        elif entryData.startswith(b'DSC FORMAT 1.00'):
            # print('DSC FORMAT 1.00', name, size)
            entryData = arc.dsc_decrypt(entryData)
            entryType = 'DSC FORMAT 1.00'

            # check audio
            magic = struct.unpack_from('<4s', entryData, 4)[0]
            if magic.startswith(b'bw'):
                name += '.ogg'
        elif entryData.startswith(b'SDC FORMAT 1.00'):
            # print('SDC FORMAT 1.00', size)
            entryType = 'SDC FORMAT 1.00'
    
        fn = os.path.join(base, name)
        print(fn)
        of = open(fn, 'wb')
        of.write(entryData)
        of.close()

        entryList.append((name, entryType))

    fn = os.path.join(base, 'list.txt')
    of = open(fn, 'w');
    for e in entryList:
        of.write('%s %s\n' % e)
    of.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: unpack.py <arc file(s)>')
        print('BGI unpack arc package')
        sys.exit(1)
    for arg in sys.argv[1:]:
        for file in glob.glob(arg):
            base, ext = os.path.splitext(file)
            if ext == '.arc':
                unpack(file)
