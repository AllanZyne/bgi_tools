from cffi import FFI
from PIL import Image

import os
import struct
import io


ffi = FFI()

ffi.cdef("""
    uint8_t * cbg_decrypt(uint8_t * crypted, uint32_t * pSize, uint32_t * pWidth, uint32_t * pHeight, uint32_t * pBitDepth);
    void cbg_free(uint8_t * decrypted);
    uint8_t * dsc_decrypt(uint8_t * crypted, uint32_t crypted_size, uint32_t * decrypted_size);
    void dsc_free(uint8_t * decrypted);
""")

__dirname = os.path.dirname(__file__)
arc = ffi.dlopen(os.path.join(__dirname, "arc.dll"))


def cbg_decrypt(crypted):
    fsize = ffi.new("uint32_t *")
    width = ffi.new("uint32_t *")
    height = ffi.new("uint32_t *")
    bbp = ffi.new("uint32_t *")
    data = arc.cbg_decrypt(crypted, fsize, width, height, bbp)
    buf = ffi.buffer(data, fsize[0])

    im = None
    if bbp[0] == 8 or bbp[0] == 24:
        pixels = [(r, g, b) for r, g, b, a in struct.iter_unpack('<BBBB', bytes(buf))]
        im = Image.new('RGB', (width[0], height[0]))
        im.putdata(pixels)
        out = io.BytesIO()
        im.save(out, format='PNG')
        return out.getvalue()
    elif bbp[0] == 32:
        im = Image.frombytes('RGBA', (width[0], height[0]), bytes(buf))
        out = io.BytesIO()
        im.save(out, format='PNG', bits=bbp[0])
        return out.getvalue()

def dsc_decrypt(crypted):
    fsize = ffi.new('uint32_t *');
    data = arc.dsc_decrypt(crypted, len(crypted), fsize)
    buf = ffi.buffer(data, fsize[0])
    # arc.dsc_free(data)
    return bytes(buf)

# def bse_decrypt(crypted):
#     data = ffi.new('char[]', crypted);
#     arc.bse_decrypt(data)

