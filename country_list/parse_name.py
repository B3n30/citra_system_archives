# Copyright 2018 Weiyi Wang
# Licensed under GPLv2 or any later version
# Refer to the license.txt file included.

import itertools

def parseName(file):
    r = []
    for i in range(16):
        r.append(file.read(0x80).decode(encoding="utf_16_le").rstrip('\0'))
    assert r[12] == r[1]
    assert r[13] == r[1]
    assert r[14] == r[1]
    assert r[15] == r[1]
    return r[0:12]

def writeName(file, nameList):
    for i in itertools.chain(range(12), [1, 1, 1, 1]):
        encoded = nameList[i].encode(encoding="utf_16_le").ljust(0x80, b'\0')
        file.write(encoded)

def parseSort(file):
    data = file.read(16)
    r = [int(x) for x in data]
    assert r[12] == r[0]
    assert r[13] == r[0]
    assert r[14] == r[0]
    assert r[15] == r[0]
    return r[0:12]

def writeSort(file, sort):
    for i in itertools.chain(range(12), [0, 0, 0, 0]):
        file.write(sort[i].to_bytes(1, byteorder='little'))
