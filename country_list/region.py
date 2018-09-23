# Copyright 2018 Weiyi Wang
# Licensed under GPLv2 or any later version
# Refer to the license.txt file included.

import sys
sys.path.append('../')
from common.lz import decompressFile
from common.lz_compress import compressLz
from parse_name import parseName, parseSort, writeName, writeSort
import os.path
import io
import struct


def loadRegionFromArchive(archivePath, code):
    result = {}
    result["region"] = code
    with open(os.path.join(archivePath, code, "country_LZ.bin"), 'rb') as file:
        decompressedData = decompressFile(file)
        decompressed = io.BytesIO(decompressedData)
        for section in range(2):
            entryCount, = struct.unpack('<I', decompressed.read(4))
            entryList = result["countries" if section == 0 else "countriesPatch"] = [{} for x in range(entryCount)]
            for entry in range(entryCount):
                entryResult = entryList[entry]
                p0, p1, p2, countryId = struct.unpack('BBBB', decompressed.read(4))
                assert p0 == 0
                assert p1 == 0
                assert p2 == 0
                entryResult['country'] = countryId

                divisionCount, = struct.unpack('<I', decompressed.read(4))
                entryResult['divisionCount'] = divisionCount

                what, = struct.unpack('<I', decompressed.read(4))
                assert what == 0

                entryResult["name"] = parseName(decompressed)
                entryResult["sort"] = parseSort(decompressed)

                zeros = decompressed.read(0x20)
                assert zeros == b'\x00' * 0x20

        countries = result["countries"]
        for i in range(len(countries)):
            sort = parseSort(decompressed)
            assert countries[i]["sort"] == sort

        tailLen = len(countries) // 32 + 1
        tail = [struct.unpack('<I', decompressed.read(4))[0] for _ in range(tailLen)]
        assert len(decompressed.read()) == 0
        for i in range(len(countries)):
            countries[i]["eshopLock"] = ((tail[i // 32] >> (i % 32)) & 1) == 1

        return result

def writeRegionToArchive(archivePath, region):
    file = io.BytesIO()
    for section in [region["countries"], region["countriesPatch"]]:
        file.write(struct.pack('<I', len(section)))
        for entry in section:
            file.write(struct.pack('BBBB', 0, 0, 0, entry["country"]))
            file.write(struct.pack('<I', entry["divisionCount"]))
            file.write(struct.pack('<I', 0))
            writeName(file, entry["name"])
            writeSort(file, entry["sort"])
            file.write(b'\x00' * 0x20)
    for entry in region["countries"]:
        writeSort(file, entry["sort"])

    countries = region["countries"]
    tailLen = len(countries) // 32 + 1
    tail = [0] * tailLen
    for i in range(len(countries)):
        if countries[i]["eshopLock"]:
            tail[i // 32] |= 1 << (i % 32)
    for t in tail:
        file.write(struct.pack('<I', t))

    with open(os.path.join(archivePath, region["region"], "country_LZ.bin"), 'wb') as realFile:
        compressLz(file.getvalue(), realFile)
