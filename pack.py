import glob
import struct
import sys
import os
import io

from PIL import Image


def packFile(file):
    base, ext = os.path.splitext(file)    
    name = os.path.basename(base)
    size = None
    data = None

    # 过滤掉txt文件
    if ext == '.txt':
        return None
        
    # 去掉png和ogg的后缀，其他后缀保留
    if ext != '.png' and ext != '.ogg':
        name += ext
    
    print(file)

    if ext == '.png':
        im = Image.open(file)
        out = io.BytesIO()
        im.save(out, format='BMP')
        data = out.getvalue()
        size = len(data)

    return {
        'name': bytes(name, 'ascii'),
        'size': size or os.path.getsize(file),
        'file': file,
        'data': data
    }

def pack(file):
    packName = file + '.arc'
    print()
    print('package:', packName)
    files = map(lambda x: os.path.join(file, x), os.listdir(file))
    packEntries = map(packFile, files)
    packEntries = filter(lambda x: x, packEntries)
    packEntries = list(packEntries)
    # print(packEntries)

    p = open(packName, 'wb')
    p.write(struct.pack('<12sL', b'PackFile    ', len(packEntries)))

    dataOffset = p.tell() + len(packEntries)*struct.calcsize('<16sLLLL');
    entryOffset = 0
    for entry in packEntries:
        p.write(struct.pack('<16sLLLL', entry['name'], entryOffset, entry['size'], 0, 0))
        entryOffset += entry['size']
    for entry in packEntries:
        # print(entry['file'])
        if entry['data']:
            p.write(entry['data'])
        else:
            e = open(entry['file'], 'rb')
            p.write(e.read())
            e.close()
    p.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: pack.py <dirs>')
        print('BGI pack arc package')
        sys.exit(1)
    for arg in sys.argv[1:]:
        for file in glob.glob(arg):
            if os.path.isdir(file):
                pack(file)
