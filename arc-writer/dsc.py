import io
import struct
import sys
from pprint import pprint


class BitsIO:
    def __init__(self, b):
        self.__closed = False
        self.__end = False

        if hasattr(b, '__next__'):
            self.__genBytes = b
            self.__bytesBuffer = bytearray()
        else:
            self.__genBytes = None
            self.__bytesBuffer = bytearray(b)

        self.__bitMask = 0x80
        self.__offsetBytes = -1
        self.__offsetBits = 0
        self.__currentByte = None

        self.__nextByte__()

    def __nextByte__(self):
        ''' 当没有新的字节时抛出异常 '''
        if not self.__end:
            off = self.__offsetBytes + 1
            if len(self.__bytesBuffer) > off:
                self.__currentByte = self.__bytesBuffer[off]
                self.__offsetBytes = off
                self.__bitMask = 0x80
            elif self.__genBytes:
                b = next(self.__genBytes)
                self.__currentByte = b
                self.__bytesBuffer.append(b)
                self.__offsetBytes += 1
                self.__bitMask = 0x80
            else:
                raise IndexError()

    def __nextBit__(self):
        if not self.__end:
            if not self.__bitMask:
                self.__nextByte__()
            v = self.__currentByte & self.__bitMask
            # print('byte', hex(self.__currentByte))
            self.__bitMask >>= 1
            self.__offsetBits += 1
            if v:
                return 1
            else:
                return 0

    def read(self, size=-1):
        if not self.__end:
            v = None
            try:
                v = self.__nextBit__()
                if size == 1:
                    return v

                if size == -1:
                    while True:
                        vv = self.__nextBit__()
                        v <<= 1
                        v |= vv
                else:
                    for _ in range(size-1):
                        vv = self.__nextBit__()
                        v <<= 1
                        v |= vv
                    return v
            except:
                self.__end = True
                return v
        else:
            return None

    def write(self, b):
        pass

    def seek(offset, whence=io.SEEK_SET):
        pass

    def tell(self):
        return self.__offsetBits


# bb = BitsIO(b'\xff\x80\x01')
# while True:
#     f = bb.tell()
#     v = bb.read(1)
#     if v == None:
#         break
#     print(f, hex(v), bb.tell())

# sys.exit()


class HuffmanNode:
    def __init__(self):
        self.left = None
        self.right = None
        self.code = None

    def __str__(self):
        if (self.left is not None) and (self.right is not None):
            return '<HuffmanNode %d %d>' % (self.left, self.right)
        elif self.code is not None:
            return '<HuffmanNode (%d)>' % self.code
        else:
            return '<HuffmanNode>'


def HuffmanTree(leafNodes):
    huffmanNodes = []
    huffmanNodeIndex = 1
    nodeIndex0 = [0]*512
    nodeIndex1 = [0]*512
    depth = 0
    depthNodesCount = 1
    n = 0

    # print('HuffmanTree')
    # for l, r in leafNodes:
    #     print(hex((l<<16)+r))

    for _ in range(1024):
        huffmanNodes.append(HuffmanNode())

    # huffmanNodes[0].left = 1
    # huffmanNodes[0].right = 1
    # print(huffmanNodes[0])
    # print(huffmanNodes[1])

    # print(leafNodes)
    # print('ln', len(leafNodes))

    while n < len(leafNodes):
        nodeIndex0, nodeIndex1 = nodeIndex1, nodeIndex0

        # print(depth, n)

        leafNodeCount = 0
        while (n < len(leafNodes)) and (leafNodes[n][0] == depth):
            node = huffmanNodes[nodeIndex0[leafNodeCount]]
            node.code = leafNodes[n][1]
            n += 1
            leafNodeCount += 1

        interNodeCount = depthNodesCount - leafNodeCount
        # print(depth, leafNodeCount, interNodeCount)
        for i in range(interNodeCount):
            # try:
            # print('n', nodeIndex0[leafNodeCount + i])
            node = huffmanNodes[nodeIndex0[leafNodeCount + i]]
            # except Exception as e:
            #     print('leaf', leafNodeCount, nodeIndex0[leafNodeCount + i])
            #     print(e)
            #     sys.exit(-1)
            nodeIndex1[i*2] = node.left = huffmanNodeIndex
            nodeIndex1[i*2+1] = node.right = huffmanNodeIndex + 1
            huffmanNodeIndex += 2

        depthNodesCount = interNodeCount*2
        depth += 1
        # if depth == 5:
        #     break

    return huffmanNodes

decompressResult = []


def decompress(tree, fi, decCount):
    global decompressResult

    #print('decompress', fi.tell())

    bits = BitsIO(fi.read())
    out = io.BytesIO()
    for _ in range(decCount):
        node = 0
        while True:
            bit = bits.read(1)
            # print('bit:', bit)
            if bit:
                node = tree[node].right
            else:
                node = tree[node].left
            # print('node', hex(node))
            if tree[node].code is not None:
                break
        code = tree[node].code

        # print('code', code)
        # if _ == 0:
        #     break

        if code < 256:
            out.write(bytes([code]))
            decompressResult.append((code, None))
        else:
            count = (code & 0xff) + 2
            offset = bits.read(12) + 2
            for _ in range(count):
                out.seek(out.tell() - offset)
                v = out.read(1)
                out.seek(0, 2)
                out.write(v)
            decompressResult.append((code, offset-2))

    return out.getvalue()


from collections import deque

matchtable = {}
matchPos = 0


def findLongestMatch(data, charPos):
    dataSize = len(data)

    def match(pos0, pos1):
        _pos0 = pos0
        while (pos1 < dataSize) and (data[pos0] == data[pos1]):
            pos0 += 1
            pos1 += 1
        return pos0 - _pos0

    # winPos = charPos - 2
    # if winPos <= 0xfff:
    #     winPos = 0
    # else:
    #     winPos -= 0xfff

    # update matchtable
    global matchtable
    global matchPos

    for pos in range(matchPos, charPos-1):
        ch = data[pos:pos+2]
        if ch in matchtable:
            matchtable[ch].append(pos+2)
        else:
            matchtable[ch] = deque([pos+2])
    matchPos = charPos-1

    # 最小匹配长度2
    mch = data[charPos:charPos+2]
    if mch in matchtable:
        maxPos = -1
        maxSize = -1

        matches = matchtable[mch]
        while len(matches):
            if (charPos - matches[0]) > 0xfff:
                matches.popleft()
            else:
                break

        for pos in matches:
            size = match(pos, charPos+2)
            if size >= maxSize:
                maxPos = charPos - pos
                maxSize = size

        if maxSize != -1:
            return maxPos, maxSize
    return None


def compress(data):
    # 得到code和offset，
    # 窗口大小：0xFFF，偏移
    # code:
    # 0-255: 字符
    # 1:0-1:255: 匹配 2-257 个字符
    # distance:
    # [0x2, 0xfff+2]
    # data = fi.read()

    out = [(data[0], None), (data[1], None)]
    charPos = 2

    global matchtable
    global matchPos
    matchtable = {}
    matchPos = 0

    dataSize = len(data)

    while True:
        result = findLongestMatch(data, charPos)
        # print(result, charPos)
        if not result:
            out.append((data[charPos], None))
            charPos += 1
        else:
            pos, size = result
            out.append((size + 0x100, pos))
            charPos += size + 2
        if charPos >= dataSize:
            break
        # if charPos % 0xfff == 0:
        # print(charPos, dataSize)
    return out

# o = compress(b'aacaacabcabaaac')
# print(o)
# print(matchtable)

# sys.exit()

# def keyGen(key):
#     while True:
#         k1 = (key >> 16) * 20021
#         k2 = (key & 0xffff) * 20021
#         k3 = (key * 346) & 0xffffffff
#         k4 = (k1 + k2 + k3) & 0xffffffff
#         yield k4 & 0xff
#         key = ((k4 << 16)&0xffffffff) + (20021 * (key & 0xffff)) + 1
#         key &= 0xffffffff


def keyGen(key):
    while True:
        a = (key & 0xffff) * 20021
        b = (key >> 16) * 20021
        c1 = (key * 346) & 0xffffffff
        c2 = (c1 + b) & 0xffffffff
        c = (c2 + (a >> 16)) & 0xffffffff
        yield c & 0xff
        key = (((c & 0xffff) << 16) + (a & 0xffff) + 1) & 0xffffffff


def walkTree(tree):
    print()
    print('walkTree')
    print()

    # stack = [0]

    # while True:
    #     newStack = []
    #     # print(stack)
    #     for n in stack:
    #         # print(n)
    #         node = tree[n]
    #         # print(node)
    #         if node.code == None:
    #             if node.left != None:
    #                 newStack.append(node.left)
    #                 newStack.append(node.right)
    #                 # print('.', end=' ')
    #         else:
    #             # print(node.code, end=' ')
    #     print()
    #     if not len(newStack):
    #         break
    #     stack = newStack

    code = {}

    def _walk(node, prefix=''):
        n = tree[node]
        if n.code is None:
            # _walk(n.left, prefix+'0')
            # _walk(n.right, prefix+'1')
            _walk(n.left, prefix+'1')
            _walk(n.right, prefix+'0')
        else:
            code[prefix] = n.code
            # code[n.code] = prefix

    _walk(0)
    pprint(code)


def dsc_decrypt(data):
    fi = io.BytesIO(data)
    magic = fi.read(16)
    # reserved = 0
    key, size, decCount, reserved = struct.unpack('<IIII', fi.read(16))

    print('m', magic)
    print('k', hex(key), 's', hex(size))
    print('dc', decCount)
    print('r', reserved)

    newKey = keyGen(key)
    leafNodes = []

    for i in range(512):
        key = next(newKey)
        # print(hex(key))
        # if i == 10:
        #     sys.quit()
        depth = (fi.read(1)[0] - key) & 0xff
        # print(i, depth)
        if depth:
            leafNodes.append((depth, i))

    leafNodes = sorted(leafNodes)

    # for n in leafNodes:
    #     print(hex(n[0]), hex(n[1]))
    # sys.exit()

    tree = HuffmanTree(leafNodes)

    # for i in range(len(tree)):
    #     print(tree[i])
    # sys.exit()

    # walkTree(tree)
    # sys.exit()
    # print(fi.tell())
    # print('decompress')
    return decompress(tree, fi, decCount)

from queue import PriorityQueue

# Canonical Huffman Coding
#
def huffmanCoding(data):
    weights = [0]*0x1ff

    for code, pos in data:
        weights[code] += 1

    def _length(code, length):
        return (code + length) >> 1

    p = PriorityQueue()
    for w in weights:
        p.putvalue(w)


import glob


for file in glob.glob('sysgrp\\_SGMusic600000'):
# for file in glob.glob('sysprg\\*._bp'):
# for file in ['sysprg\\usdtwnd._bp']:
    print(file)
    fi = open(file, 'rb')
    data = fi.read()
    fi.close()

    decompressResult = []
    # print('--decript')
    out = dsc_decrypt(data)

    fo = open(file + '.pydec', 'wb')
    fo.write(out)
    fo.close()

    break
    # print('--compress')
    # import profile
    # profile.run("compress(out)", "prof.txt")
    out2 = compress(out)

    # print(out2)
    # print(decompressResult)
    # print('--compare')
    if out2 != decompressResult:
        print('!!!!!!!!!')
        f1 = open('diff0.txt', 'w')
        for a in out2:
            f1.write(a.__str__() + '\n')
        f1.close()

        f1 = open('diff1.txt', 'w')
        for a in decompressResult:
            f1.write(a.__str__() + '\n')
        f1.close()
