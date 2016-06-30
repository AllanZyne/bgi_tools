
import io
from pprint import pprint
from queue import PriorityQueue


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
        return
    length = bytearray()
    while True:
        c = v & 0x7f
        v >>= 7
        if c:
            length.append(c if not v else c|0x80)
        if not v:
            break
    # print(length)
    # biDst.write(bytes(length))
    biDst.write(length)

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

# biDst = io.BytesIO()
# writeLength(biDst, 0x2323)
# print(biDst.getvalue())
# biDst.seek(0)
# print(hex(readLength(biDst)))

################################################################################

# print()
# print('RLC')

# Run Length Code
#
def writeRLC(biSrc, biDst):
    def getNZero():
        buf = bytearray()
        while True:
            c = biSrc.read(1)
            if c == b'':
                return buf
            elif c != b'\0':
                buf.append(c[0])
            else:
                biSrc.seek(biSrc.tell()-1)
                return buf
    def getZero():
        count = 0
        while True:
            c = biSrc.read(1)
            # print('z', c)
            if c == b'':
                return count
            elif c == b'\0':
                count += 1
            else:
                biSrc.seek(biSrc.tell()-1)
                return count

    size = biSrc.seek(0, 2)
    biSrc.seek(0)
    while biSrc.tell() < size:
        buf = getNZero()
        # print(biSrc.tell(), len(buf))
        writeLength(biDst, len(buf))
        biDst.write(buf)
        # print(biDst.getvalue())
        if biSrc.tell() == size:
            return buf
        count = getZero()
        # print(biSrc.tell(), count)
        if count:
            writeLength(biDst, count)
            # print(biDst.getvalue())

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
    dataDst = []
    while pos < size:
        b = coding[pos:pos+8]
        pos += 8
        dataDst.append(int(b.ljust(8, '0'), 2))
    # dataDst = bytes(dataDst)
    # print(dataSrc)
    # print(dataDst)
    return freqs, len(dataSrc), bytes(dataDst)

def huffmanDecoding(freqs, size, biSrc):
    # t0 = time.perf_counter()
    tree = huffTree(freqs)
    # t1 = time.perf_counter()

    t2 = time.perf_counter()
    dstData = bytearray(size)
    ch = biSrc.read(1)[0]
    mask = 0x80
    for i in range(size):
        node = tree
        while node.left:
            node = node.right if ch & mask else node.left
            mask >>= 1
            if not mask:
                ch = biSrc.read(1)[0]
                mask = 0x80
        dstData[i] = node.info
    t3 = time.perf_counter()

    # print('huffTree', t1 - t0)
    # print('walkTree', t3 - t2)
    
    return bytes(dstData)

class Node:
    def __init__(self, Fr=0, Left=None, Right=None):
        self.Val = Fr > 0
        self.Fr = Fr
        self.Left = Left
        self.Right = Right

def walkNodesArr(NodesArr):
    code = {}
    def _walkNodesArr(node, prefix=''):
        if node < 256:
            code[node]  = prefix
        else:
            _walkNodesArr(NodesArr[node].Left, prefix+'0')
            _walkNodesArr(NodesArr[node].Right, prefix+'1')
    _walkNodesArr(len(NodesArr)-1)
    return code

def huffmanDecoding1(freqs, size, biSrc):
    NodesArr = []
    FTotal = 0
    # t0 = time.perf_counter()
    for i in range(256):
        NodesArr.append(Node(freqs[i], i, i))
        FTotal += freqs[i]

    while True:
        ch = [0xFFFFFFFF, 0xFFFFFFFF]
        frec = 0
        for i in range(2):
            fmin = 0xFFFFFFFF
            for j in range(len(NodesArr)):
                if NodesArr[j].Val and (NodesArr[j].Fr < fmin):
                    fmin = NodesArr[j].Fr
                    ch[i]  = j
            if ch[i] != 0xFFFFFFFF:
                NodesArr[ch[i]].Val = False
                frec += NodesArr[ch[i]].Fr
        NodesArr.append(Node(frec, ch[0], ch[1]))
        if frec == FTotal:
            break
    # t1 = time.perf_counter()

    # print(len(NodesArr), hex(len(NodesArr)))
    # code = walkNodesArr(NodesArr)
    # return code

    ## Walk Tree

    t2 = time.perf_counter()

    HummfArr = [0]*size
    workb = biSrc.read(1)[0]
    mask = 0x80
    root = len(NodesArr) - 1
    for i in range(size):
        node = root
        while node >= 256:
            node = NodesArr[node].Right if workb & mask else NodesArr[node].Left
            mask >>= 1
            if not mask:
                workb = biSrc.read(1)[0]
                mask = 0x80
        HummfArr[i] = node

    t3 = time.perf_counter()

    # print('huffTree', t1 - t0)
    print('walktree', t3 - t2)

    return bytes(HummfArr)


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
    result = []
    newKey = keyGen(key)
    chkSum = 0
    chkXor = 0
    for ch in data:
        chkSum = (chkSum + ch)%256
        chkXor ^= ch
        result.append((ch + next(newKey))%256)
    return bytes(result), chkSum, chkXor

def decryptData(data, key, chkSum, chkXor):
    result = []
    newKey = keyGen(key)
    _chkSum = 0
    _chkXor = 0
    for ch in data:
        nch = (ch - next(newKey))%256
        result.append(nch)
        _chkSum = (_chkSum + nch)%256
        _chkXor = _chkXor ^ nch
    if (chkSum != _chkSum) or (_chkXor != chkXor):
        raise Exception('decryptData fail')

    return bytes(result)

# print()
# print('encrypt')

################################################################################

import struct

fo = open('bg07_s01', 'rb')
hdr = fo.read(0x10)
w, h, bpp, r1, r2 = struct.unpack('<HHIII', fo.read(0x10))
size, key, eLen, chkSum, chkXor, ver = struct.unpack('<IIIBBH', fo.read(0x10))
eData = fo.read(eLen)

print('w', w, 'h', h, 'bpp', bpp)
print('key', hex(key), 'len', eLen)
print('chkSum', hex(chkSum), 'chkXor', hex(chkXor))
print()

deData = decryptData(eData, key, chkSum, chkXor)
# nData, _Sum, _Xor = cryptData(deData, key)
# print(nData[:10], hex(_Sum), hex(_Xor))
# newkey = keyGen(key)
# for _ in range(10):
#     # print(hex(), hex())
#     next(newkey)

dataFreqs = []
biData = io.BytesIO(deData)
for _ in range(256):
    dataFreqs.append(readLength(biData))
print('Freqs')
print('AssertEqual', len(deData), biData.tell())
print()
# print(dataFreqs)

import time
off = fo.tell()
print('huffmanDecoding')
t0 = time.perf_counter()
r1 = huffmanDecoding(dataFreqs, size, fo)
t1 = time.perf_counter()
print(t1 - t0)

fo.seek(off)
print('huffmanDecoding1')
t2 = time.perf_counter()
r2 = huffmanDecoding1(dataFreqs, size, fo)
t3 = time.perf_counter()
print(t3 - t2)

print(size)
print(len(r1), len(r2))
flag = True
for i in range(size):
    if r1[i] != r2[i]:
        flag = False
        print(i)
        break
print(flag)

# off2 = fo.tell()
# print(off, fo.seek(0, 2), off2)



fo.close()

# huffmanDecoding1()
# pprint(code)

# for i in range(256):
#     # if code1[i] != code0[i]:
#     print(i, code1[i], code0[i])


import sys
sys.exit()

print('readRLC')
colorData = readRLC(io.BytesIO(huffData))
print('assertEqual', len(colorData), w*h*(bpp>>3))

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

