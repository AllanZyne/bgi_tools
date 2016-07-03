
import io
from pprint import pprint
from queue import PriorityQueue

import sys


def bytesAddition(b0, b1):
    a0 = bytearray(len(b0))
    for i in range(len(b0)):
        a0[i] = (b0[i] + b1[i]) & 0xff
    return bytes(a0)

def bytesSubtraction(b0, b1):
    a0 = bytearray(len(b0))
    for i in range(len(b0)):
        a0[i] = (b0[i] - b1[i]) & 0xff
    return bytes(a0)

def bytesAverage(b0, b1):
    a0 = bytearray(len(b0))
    for i in range(len(b0)):
        a0[i] = (b0[i] + b1[i]) >> 1  # not ((b0[i] + b1[i])&0xff) >> 1
    return bytes(a0)

def colorTransform(biData, width, height, bpp):
    pixelLength = bpp >> 3
    lineLength = width * pixelLength
    pos = 0
    lastLine = None
    lastBytes = None
    lastLineBytes = None
    for y in range(height):
        curLine = biData.read(lineLength)
        biData.seek(pos)
        for x in range(width):
            if x == 0 and y == 0:
                lastBytes = curLine[0:pixelLength]
                biData.seek(pixelLength)
            elif y == 0:
                curIndex = x*pixelLength
                curBytes = curLine[curIndex:curIndex+pixelLength]
                # print(curBytes, lastBytes)
                deltaBytes = bytesSubtraction(curBytes, lastBytes)
                lastBytes = curBytes
                biData.write(deltaBytes)
            elif x == 0:
                curBytes = curLine[0:pixelLength]
                lastLineBytes = lastLine[0:pixelLength]
                deltaBytes = bytesSubtraction(curBytes, lastLineBytes)
                lastBytes = curBytes
                biData.write(deltaBytes)
            else:
                curIndex = x*pixelLength
                curBytes = curLine[curIndex:curIndex+pixelLength]
                lastLineBytes = lastLine[curIndex:curIndex+pixelLength]
                avgBytes = bytesAverage(lastBytes, lastLineBytes)
                deltaBytes = bytesSubtraction(curBytes, avgBytes)
                lastBytes = curBytes
                biData.write(deltaBytes)
        lastLine = curLine
        pos += lineLength

# def sprint(bb):
#     s = '0x'
#     for b in bb:
#         s += '%02x' % b
#     return s

def colorRetransform(biData, width, height, bpp):
    pixelLength = bpp >> 3
    lineLength = width * pixelLength
    pos = 0
    lastBytes = None
    lastLineBytes = None
    for y in range(height):
        for x in range(width):
            # print('Pos', pos, biData.tell())
            curBytes = biData.read(pixelLength)
            if x == 0 and y == 0:
                lastBytes = curBytes
            elif y == 0:
                lastBytes = bytesAddition(lastBytes, curBytes)
            elif x == 0:
                # print('LastLinePos', pos-lineLength)
                biData.seek(pos - lineLength)
                lastLineBytes = biData.read(pixelLength)
                # print(lastLineBytes, curBytes)
                lastBytes = bytesAddition(lastLineBytes, curBytes)
            else:
                biData.seek(pos - lineLength)
                lastLineBytes = biData.read(pixelLength)
                avgBytes = bytesAverage(lastBytes, lastLineBytes)
                # print(sprint(lastBytes), sprint(lastLineBytes), sprint(avgBytes))
                lastBytes = bytesAddition(avgBytes, curBytes)
            biData.seek(pos)
            biData.write(lastBytes)
            pos += pixelLength

# def aprint(a, w, h):
#     # print('[', end='')
#     print()
#     for y in range(h):
#         for x in range(w):
#             print('0x%02x,' % a[x+y*w], end='')
#         print()
#     # print(']')
#     print()
#
# src = [
# 0xff, 0xfe, 0x01, 0xf2, 0xff, 0xff,
# 0x07, 0xff, 0x89, 0x10, 0x71, 0x12,
# 0xf0, 0xe3, 0x45, 0x55, 0x92, 0x13,
# 0xe7, 0x08, 0x58, 0x60, 0x11, 0x12,
# ]

# bData = io.BytesIO(bytes(src))
# aprint(bData.getvalue(), 6, 4)
# bData.seek(0)
# colorTransform(bData, 3, 4, 16)
# aprint(bData.getvalue(), 6, 4)
# # print('Len', len(bytes(src)))
# bData.seek(0)
# colorRetransform(bData, 3, 4, 16)
# aprint(bData.getvalue(), 6, 4)

# import sys
# sys.exit()

################################################################################

# v != 0
def writeLength(biDst, v):
    if v == 0:
        biDst.write(b'\0')
    else:
        length = bytearray()
        while True:
            c = v & 0x7f
            v >>= 7
            if v:
                length.append(c|0x80)
            elif c:
                length.append(c)
                biDst.write(length)
                return

def readLength(biSrc):
    v = 0
    s = 0
    while True:
        b = biSrc.read(1)
        if b == b'':
            return v
        b = b[0]
        v |= (b & 0x7f) << s
        s += 7
        if not (b & 0x80):
            break
    return v

# for v in range(0xFFFFFFFF):
#     biDst = io.BytesIO()
#     writeLength(biDst, v)
#     biDst.seek(0)
#     if readLength(biDst) != v:
#         print(hex(v))
#         print(biDst.getvalue())
#         raise Exception('!!!')
#
# sys.exit()

################################################################################

# print()
# print('RLC')

# Run Length Code
#
def writeRLC(biSrc, _SrcData):

    def getNZero():
        buf = bytearray()
        while True:
            c = biSrc.read(1)
            if c == b'':
                return buf
            elif c != b'\0':
                buf.append(c[0])
            else:
                cc = biSrc.read(1)
                if cc == b'\0':
                    biSrc.seek(biSrc.tell()-2)
                    return buf
                else:
                    buf.append(0)
                    if cc == b'':
                        return buf
                    buf.append(cc[0])

    def getZero():
        count = 0
        while True:
            c = biSrc.read(1)
            if c == b'':
                return count, False
            elif c == b'\0':
                count += 1
            else:
                biSrc.seek(biSrc.tell()-1)
                return count, True

    # _biSrc = io.BytesIO(_SrcData)

    biDst = io.BytesIO()
    while True:
        off = biSrc.tell()

        buf = getNZero()
        if not len(buf):
            break

        writeLength(biDst, len(buf))
        biDst.write(buf)

        # l = readLength(_biSrc)
        # if len(buf) != l:
        #     raise Exception('!! 0x%x: 0x%x 0x%x' % (off, l, len(buf)))
        # _biSrc.read(l)

        off = biSrc.tell()

        count, status = getZero()
        if status:
            writeLength(biDst, count)
        elif count:
            writeLength(biDst, count)
            break
        else:
            break
        # c = readLength(_biSrc)
        # if c != count:
        #     raise Exception('!! 0x%x: 0x%x 0x%x' % (off, c, count))

    return biDst.getvalue()

def readRLC(biSrc):
    biDst = io.BytesIO()
    size = biSrc.seek(0, 2)
    biSrc.seek(0)
    while biSrc.tell() < size:
        nzCount = readLength(biSrc)
        # print('nzCount', nzCount)
        biDst.write(biSrc.read(nzCount))
        zCount = readLength(biSrc)
        # print('zCount', zCount)
        biDst.write(bytes(zCount))
    return biDst.getvalue()

# testSrc = io.BytesIO(bytes([0,0, 1,2,3,4,5,6, 0,0,0,0,0,0, 1,2,3]))
# testDst = io.BytesIO()
# testDst2 = io.BytesIO()

# writeRLC(testSrc, testDst)
# readRLC(testDst, testDst2)

# print(testDst.getvalue())
# print(testDst2.getvalue())

# print(biSrc.getvalue())

################################################################################

class HuffNode:
    index = 0
    def __init__(self, info=None, left=None, right=None):
        self.left = left
        self.right = right
        self.info = info
        # 排序用，新节点总小于旧节点
        self._index = HuffNode.index  
        HuffNode.index += 1
    def __lt__(self, node):
        return self._index < node._index
    def __str__(self):
        if self.info != None:
            return '<HuffNode info=0x%x>' % (self.info)
        else:
            return '<HuffNode>'

def huffTree(freqs):
    p = PriorityQueue()
    for i, fr in enumerate(freqs):
        if fr:
            # print(i, fr)
            p.put((fr, HuffNode(info=i)))

    while p.qsize() > 1:
        l, r = p.get(), p.get()
        n = HuffNode(left=l[1], right=r[1])
        p.put((l[0]+r[0], n))

    return p.get()[1]


def walkTree(rootNode):
    code = {}
    def _walkTree(node, prefix=""):
        # print('walkTree', node)
        if node.info == None:
            _walkTree(node.left, prefix+'0')
            _walkTree(node.right, prefix+'1')
        else:
            code[node.info] = prefix
    _walkTree(rootNode)
    return code

def huffmanCoding(biSrc):
    freqs = [0] * 0x100
    dataSrc = biSrc.read()
    for c in dataSrc:
        freqs[c] += 1
    
    tree = huffTree(freqs)
    code = walkTree(tree)

    coding = ''
    for c in dataSrc:
        coding += code[c]

    pos = 0
    size = len(coding)
    dataDst = bytearray()
    while pos < size:
        b = coding[pos:pos+8]
        pos += 8
        dataDst.append(int(b.ljust(8, '0'), 2))

    return freqs, len(dataSrc), dataDst

def huffmanDecoding(freqs, size, biSrc):
    tree = huffTree(freqs)

    dstData = bytearray(size)
    ch = biSrc.read(1)
    mask = 0x80
    for i in range(size):
        node = tree
        while node.left:
            node = node.right if ch[0] & mask else node.left
            mask >>= 1
            if not mask:
                ch = biSrc.read(1)
                mask = 0x80
        dstData[i] = node.info
    
    return dstData

#
# 另一种写法
#
# class Node:
#     def __init__(self, Fr=0, Left=None, Right=None):
#         self.Val = Fr > 0
#         self.Fr = Fr
#         self.Left = Left
#         self.Right = Right

# def walkNodesArr(NodesArr):
#     code = {}
#     def _walkNodesArr(node, prefix=''):
#         if node < 256:
#             code[node]  = prefix
#         else:
#             _walkNodesArr(NodesArr[node].Left, prefix+'0')
#             _walkNodesArr(NodesArr[node].Right, prefix+'1')
#     _walkNodesArr(len(NodesArr)-1)
#     return code

# def huffmanDecoding1(freqs, size, biSrc):
#     NodesArr = []
#     FTotal = 0
#     # t0 = time.perf_counter()
#     for i in range(256):
#         NodesArr.append(Node(freqs[i], i, i))
#         FTotal += freqs[i]

#     while True:
#         ch = [0xFFFFFFFF, 0xFFFFFFFF]
#         frec = 0
#         for i in range(2):
#             fmin = 0xFFFFFFFF
#             for j in range(len(NodesArr)):
#                 if NodesArr[j].Val and (NodesArr[j].Fr < fmin):
#                     fmin = NodesArr[j].Fr
#                     ch[i]  = j
#             if ch[i] != 0xFFFFFFFF:
#                 NodesArr[ch[i]].Val = False
#                 frec += NodesArr[ch[i]].Fr
#         NodesArr.append(Node(frec, ch[0], ch[1]))
#         if frec == FTotal:
#             break
#     # t1 = time.perf_counter()

#     # print(len(NodesArr), hex(len(NodesArr)))
#     # code = walkNodesArr(NodesArr)
#     # return code

#     ## Walk Tree

#     # t2 = time.perf_counter()

#     HummfArr = [0]*size
#     workb = biSrc.read(1)[0]
#     mask = 0x80
#     root = len(NodesArr) - 1
#     for i in range(size):
#         node = root
#         while node >= 256:
#             node = NodesArr[node].Right if workb & mask else NodesArr[node].Left
#             mask >>= 1
#             if not mask:
#                 workb = biSrc.read(1)[0]
#                 mask = 0x80
#         HummfArr[i] = node

#     # t3 = time.perf_counter()

#     # print('huffTree', t1 - t0)
#     print('walktree', t3 - t2)

#     return bytes(HummfArr)


# print()
# print('huffmanCoding')
# testSrc.seek(0)
# data0 = b'\x11\x01\x01\x7e\xff\x85\x20\x01\x01\x00\x00\x24\x50\x12\x10\x10\x10\x10\x10\x01\x01'
# print(data0)
# freqs, size, data1 = huffmanCoding(io.BytesIO(data0))
# print(data1)
# data2 = huffmanDecoding(freqs, size, io.BytesIO(data1))
# print(data2)

################################################################################

def keyGen(key):
    while True:
        a = (key & 0xffff) * 20021
        b = (key >> 16) * 20021
        c1 = (key * 346) & 0xffffffff
        c2 = (c1 + b) & 0xffffffff
        c = (c2 + (a >> 16)) & 0xffffffff
        yield c & 0xff
        key = (((c & 0xffff) << 16) + (a & 0xffff) + 1) & 0xffffffff

def cryptData(data, key):
    result = bytearray()
    newKey = keyGen(key)
    chkSum = 0
    chkXor = 0
    for ch in data:
        chkSum = (chkSum + ch) & 0xff
        chkXor ^= ch
        nch = (ch + next(newKey)) & 0xff
        result.append(nch)
    return result, chkSum, chkXor

def decryptData(data, key, chkSum, chkXor):
    result = bytearray()
    newKey = keyGen(key)
    _chkSum = 0
    _chkXor = 0

    for ch in data:
        nch = (ch - next(newKey)) & 0xff
        result.append(nch)
        _chkSum = (_chkSum + nch) & 0xff
        _chkXor = _chkXor ^ nch

    if (chkSum != _chkSum) or (_chkXor != chkXor):
        raise Exception('decryptData fail')

    return result

# print()
# print('encrypt')

################################################################################

import struct


testFile = '01ayua02s01'

fo = open(testFile, 'rb')
hdr = fo.read(0x10)
w, h, bpp, r1, r2 = struct.unpack('<HHIII', fo.read(0x10))
size, key, cryptLen, chkSum, chkXor, ver = struct.unpack('<IIIBBH', fo.read(0x10))

print('w', w, 'h', h, 'bpp', bpp)
print('key', hex(key), 'clen', cryptLen)
print('chkSum', hex(chkSum), 'chkXor', hex(chkXor))
print('size', size, 'ver', ver)
print()

print('decryptData')
cryptFreqsData = fo.read(cryptLen)
decryptFreqsData = decryptData(cryptFreqsData, key, chkSum, chkXor)

freqsData = []
biData = io.BytesIO(decryptFreqsData)
for i in range(256):
    fr = readLength(biData)
    freqsData.append(fr)
print('==', len(decryptFreqsData), biData.tell())


# # print(hex(off))
print('huffmanDecoding')
off = fo.tell()
unhuffData = fo.read()
fo.seek(off)
huffData = huffmanDecoding(freqsData, size, fo)

fo.close()

print('readRLC')
colorData = readRLC(io.BytesIO(huffData))
print('==', len(colorData), w*h*(bpp>>3))

print('colorRetransform')
bColorData = io.BytesIO(colorData)
colorRetransform(bColorData, w, h, bpp)


print('image')

from PIL import Image

if bpp == 24:
    pixels = [(r, g, b) for b, g, r in struct.iter_unpack('<BBB', bColorData.getvalue())]
    im = Image.new('RGB', (w, h))
    im.putdata(pixels)
    # im = Image.frombytes('RGB', (w, h), bColorData.getvalue())
    im.show()
elif bpp == 32:
    # im = Image.frombytes('RGBA', (w, h), bColorData.getvalue())
    pixels = [(r, g, b, a) for b, g, r, a in struct.iter_unpack('<BBBB', bColorData.getvalue())]
    im = Image.new('RGBA', (w, h))
    im.putdata(pixels)
    im.show()
elif bpp == 8:
    im = Image.frombytes('L', (w, h), bColorData.getvalue())
    im.show()

im.save(testFile + '.png')

################################################################################

from PIL import Image

im = Image.open(testFile + '.png')

w, h = im.size
bpp = None
pixelsData = None

if im.mode == 'RGB':
    bpp = 24
    pixelsData = bytearray()
    for r, g, b in im.getdata():
        pixelsData.append(b)
        pixelsData.append(g)
        pixelsData.append(r)
elif im.mode == 'RGBA':
    bpp = 32
    # pixelsData = im.tobytes()
    pixelsData = bytearray()
    for r, g, b, a in im.getdata():
        pixelsData.append(b)
        pixelsData.append(g)
        pixelsData.append(r)
        pixelsData.append(a)
elif im.mode == 'L':
    bpp = 8
    pixelsData = im.tobytes()
else:
    raise Exception('im.mode: ' + im.mode)

print()
print('w', w, 'h', h, 'bpp', bpp)


pixelsData = io.BytesIO(pixelsData)

print('colorTransform')
colorTransform(pixelsData, w, h, bpp)

colorData2 = pixelsData.getvalue()
print('==', len(colorData), len(colorData2))
if colorData2 != colorData:
    print('false')
# sys.exit()

f = open('bin1', 'wb')
f.write(colorData2)
f.close()

print('writeRLC')
pixelsData.seek(0)
rlcData = writeRLC(pixelsData, huffData)
# 

print('readRLC')
# if readRLC(io.BytesIO(rlcData)) != colorData2:
if huffData != rlcData:
    print('false')
    f = open('bin0', 'wb')
    f.write(huffData)
    f.close()
    f = open('bin2', 'wb')
    f.write(rlcData)
    f.close()

print('huffmanCoding')
freqs, size, huffData = huffmanCoding(io.BytesIO(rlcData))

if huffData != unhuffData:
    print('false')
    
print('cryptData')
freqsData = io.BytesIO()
for fr in freqs:
    writeLength(freqsData, fr)

if decryptFreqsData != freqsData.getvalue():
    print('false')

_cryptFreqsData, chckSum, chckXor = cryptData(freqsData.getvalue(), key)
if _cryptFreqsData != cryptFreqsData:
    print('false')


print('write file')
fo = open(testFile + '.bin', 'wb')
fo.write(b'CompressedBG___\0')
# w, h, bpp, r1, r2 = struct.unpack('<HHIII', fo.read(0x10))
# size, key, enLen, chkSum, chkXor, ver = struct.unpack('<IIIBBH', fo.read(0x10))
fo.write(struct.pack('<HHIII', w, h, bpp, 0, 0))
fo.write(struct.pack('<IIIBBH', size, key, len(_cryptFreqsData), chckSum, chckXor, 1))
fo.write(_cryptFreqsData)
fo.write(huffData)
fo.close()
