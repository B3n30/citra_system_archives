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

def loadCountryFromArchive(archivePath, code):
    result = {}
    result["code"] = code
    regions = ["CN", "EU", "JP", "KR", "TW", "US"]
    for regionCandidate in regions:
        path = os.path.join(archivePath, regionCandidate, "{}_LZ.bin".format(code))
        if os.path.exists(path):
            result["region"] = regionCandidate
            break
    else:
        return
    with open(path, 'rb') as file:
        decompressedData = decompressFile(file)
        decompressed = io.BytesIO(decompressedData)

        for section in range(2):
            entryCount, = struct.unpack("<I", decompressed.read(4))
            if section == 0:
                entryCount += 1
            entryList = result["divisions" if section == 0 else "divisionsPatch"] = [{} for x in range(entryCount)]
            for entry in range(entryCount):
                entryResult = entryList[entry]
                p0, p1, division, country = struct.unpack('BBBB', decompressed.read(4))
                entryResult["division"] = division
                assert country == code
                assert p0 == 0
                assert p1 == 0

                entryResult["name"] = parseName(decompressed)
                entryResult["sort"] = parseSort(decompressed)
                latitude, longitude = struct.unpack('<HH', decompressed.read(4))
                entryResult["latitude"] = latitude
                entryResult["longitude"] = longitude

        divisions = result["divisions"]
        for i in range(len(divisions)):
            divisions[i]["sortPatch"] = parseSort(decompressed)

        tailLen = len(divisions) // 32 + 1
        tail = [struct.unpack('<I', decompressed.read(4))[0] for _ in range(tailLen)]
        assert len(decompressed.read()) == 0
        for i in range(len(divisions)):
            divisions[i]["eshopLock"] = ((tail[i // 32] >> (i % 32)) & 1) == 1

        return result


def writeCountryToArchive(archivePath, country):
    file = io.BytesIO()
    firstSection = True
    for section in [country["divisions"], country["divisionsPatch"]]:
        entryCount = len(section)
        entryCountWrite = entryCount
        if firstSection:
            firstSection = False
            entryCountWrite -= 1
        file.write(struct.pack('<I', entryCountWrite))
        for entry in section:
            file.write(struct.pack('BBBB', 0, 0, entry["division"], country["code"]))
            writeName(file, entry["name"])
            writeSort(file, entry["sort"])
            file.write(struct.pack('<HH', entry["latitude"], entry["longitude"]))
    for entry in country["divisions"]:
        writeSort(file, entry["sortPatch"])

    divisions = country["divisions"]
    tailLen = len(divisions) // 32 + 1
    tail = [0] * tailLen
    for i in range(len(divisions)):
        if divisions[i]["eshopLock"]:
            tail[i // 32] |= 1 << (i % 32)
    for t in tail:
        file.write(struct.pack('<I', t))

    path = os.path.join(archivePath, country["region"], "{}_LZ.bin".format(country["code"]))
    with open(path, 'wb') as realFile:
        compressLz(file.getvalue(), realFile)
