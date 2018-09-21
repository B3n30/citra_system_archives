'''
Adapted from https://github.com/magical/nlzss/

Copyright (C) magical

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''

from struct import pack, unpack

__all__ = ('decompressFile')


def bits(byte):
    return ((byte >> 7) & 1,
            (byte >> 6) & 1,
            (byte >> 5) & 1,
            (byte >> 4) & 1,
            (byte >> 3) & 1,
            (byte >> 2) & 1,
            (byte >> 1) & 1,
            (byte) & 1)

def decompress_raw(indata, decompressed_size):
    """Decompress LZSS-compressed bytes. Returns a bytearray."""
    data = bytearray()

    it = iter(indata)

    def writebyte(b):
        data.append(b)
    def readbyte():
        return next(it)
    def copybyte():
        data.append(next(it))

    while len(data) < decompressed_size:
        b = readbyte()
        flags = bits(b)
        for flag in flags:
            if flag == 0:
                copybyte()
            else:
                b = readbyte()
                indicator = b >> 4

                if indicator == 0:
                    # 8 bit count, 12 bit disp
                    # indicator is 0, don't need to mask b
                    count = (b << 4)
                    b = readbyte()
                    count += b >> 4
                    count += 0x11
                elif indicator == 1:
                    # 16 bit count, 12 bit disp
                    count = ((b & 0xf) << 12) + (readbyte() << 4)
                    b = readbyte()
                    count += b >> 4
                    count += 0x111
                else:
                    # indicator is count (4 bits), 12 bit disp
                    count = indicator
                    count += 1

                disp = ((b & 0xf) << 8) + readbyte()
                disp += 1

                for _ in range(count):
                    writebyte(data[-disp])

            if decompressed_size <= len(data):
                break

    assert len(data) == decompressed_size

    return data

def decompressFile(f):
    header = f.read(4)
    assert header[0] == 0x11
    decompressed_size, = unpack("<L", header[1:] + b'\x00')
    data = f.read()
    return decompress_raw(data, decompressed_size)
