#!/usr/bin/env python3

# Copyright 2018 Weiyi Wang
# Licensed under GPLv2 or any later version
# Refer to the license.txt file included.

import country
import region
import json
import os
import shutil
import sys
import tempfile
import romfs

def loadFromArchive(path):
    result = {}

    regions = result["regions"] = []
    for regionCode in ["CN", "EU", "JP", "KR", "TW", "US"]:
        regions.append(region.loadRegionFromArchive(path, regionCode))

    countries = result["countries"] = []

    for i in range(256):
        countryResult = country.loadCountryFromArchive(path, i)
        if countryResult is not None:
            countries.append(countryResult)

    return result

def writeToArchive(path, archive):
    for regionCode in ["CN", "EU", "JP", "KR", "TW", "US"]:
        os.mkdir(os.path.join(path, regionCode))

    for x in archive["regions"]:
        region.writeRegionToArchive(path, x)


    for x in archive["countries"]:
        country.writeCountryToArchive(path, x)


def main():
    def printHelp():
        print("Usage: {} [-x|-c] INPUT OUTPUT".format(sys.argv[0]))
        exit(-1)

    if len(sys.argv) < 4:
        printHelp()

    inPath = sys.argv[2]
    outPath = sys.argv[3]

    if sys.argv[1] == "-x":
        d = tempfile.mkdtemp()
        romfs.extractRomfs(inPath, d)
        archive = loadFromArchive(d)
        shutil.rmtree(d)
        with open(outPath, "wt") as f:
            json.dump(archive, f, indent = 2)
    elif sys.argv[1] == "-c":
        with open(inPath, "rt") as f:
            archive = json.load(f)
        d = tempfile.mkdtemp()
        writeToArchive(d, archive)
        romfs.buildRomfs(d, outPath)
        shutil.rmtree(d)
    else:
        printHelp()


if __name__ == "__main__":
    main()
