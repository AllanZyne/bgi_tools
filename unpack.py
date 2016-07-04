import glob
import struct
import sys
import os
import io


from PIL import Image

import arc


def checkAudio(data):
    magic = struct.unpack_from('<4s', data, 4)[0]
    return magic.startswith(b'bw  ')

def checkGRPImage(data):
    width, height, bpp = struct.unpack_from('<HHH', data, 0)
    if not (bpp == 8 or bpp == 24 or bpp == 32):
        return
    return int(width*height*bpp/8)+16 == len(data)

def unpackGRPImage(data):
    width, height, bpp = struct.unpack_from('<HHH', data, 0)
    if bpp == 8:
        pass
    elif bpp == 24:
        pass
    elif bpp == 32:
        pixels = [(r, g, b, a) for b, g, r, a in struct.iter_unpack('<BBBB', data[16:])]
        im = Image.new('RGBA', (width, height))
        im.putdata(pixels)
        out = io.BytesIO()
        im.save(out, format='PNG')
        return out.getvalue()

def unpack(file, args):

    print(file)
    print('--------------------')

    f = open(file, 'rb')

    base, ext = os.path.splitext(file)
    os.makedirs(base, exist_ok=True)

    magic, fileCount = struct.unpack('<12sL', f.read(0x10))
    if not magic.startswith(b'PackFile'):
        print('不能识别该文件！')
        return
    
    entryRaw = f.read(0x20*fileCount)
    dataOffset = f.tell()
    entryList = []
    ii = 1

    for name, offset, size, _, _ in struct.iter_unpack('<16sLLLL', entryRaw):

        name = name.rstrip(b'\x00').decode('ascii')

        if args.list:
            print("(%d/%d)" % (ii, fileCount), name)
            ii += 1
            continue

        f.seek(dataOffset + offset)
        entryData = f.read(size)
        decryptData = None
        entryType = 'NONE'
        # print(len(entryData))

        if not args.raw:
            if entryData.startswith(b'CompressedBG___'):
                # print('CompressedBG___', size)
                entryType = 'CompressedBG___'
                entryData = arc.cbg_decrypt(entryData)
                name += '.png'
            elif entryData.startswith(b'DSC FORMAT 1.00'):
                # print('DSC FORMAT 1.00', name, size)
                entryData = arc.dsc_decrypt(entryData)
                entryType = 'DSC FORMAT 1.00'

                if checkAudio(entryData):
                    name += '.ogg'
                elif checkGRPImage(entryData):
                    name += '.png'
                    entryData = unpackGRPImage(entryData)
            elif entryData.startswith(b'SDC FORMAT 1.00'):
                # print('SDC FORMAT 1.00', size)
                entryType = 'SDC FORMAT 1.00'
            # check bmp
    
        fn = os.path.join(base, name)

        print("(%d/%d)" % (ii, fileCount), fn)
        ii += 1

        of = open(fn, 'wb')
        of.write(entryData)
        of.close()

        entryList.append((name, entryType))

    # fn = os.path.join(base, 'list.txt')
    # of = open(fn, 'w');
    # for e in entryList:
    #     of.write('%s %s\n' % e)
    # of.close()

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-r", "--raw", action='store_true', help="不解码文件")
parser.add_argument("-l", "--list", action='store_true', help="列出文件")
parser.add_argument("-d", "--dir", help="输出文件夹（默认与arc文件一个目录）")
parser.add_argument('files', nargs='+', help="arc文件")


if __name__ == '__main__':
    args = parser.parse_args()
    # print(args)
    # print("raw {} list {} dir {} files {}".format(args.raw, args.list, args.dir, args.files))

    for file in args.files:
        for f in glob.glob(file):
            base, ext = os.path.splitext(f)
            if ext == '.arc':
                unpack(f, args)

