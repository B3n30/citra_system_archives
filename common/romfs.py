# Copyright 2018 Weiyi Wang
# Licensed under GPLv2 or any later version
# Refer to the license.txt file included.

import os
import struct

INVALID = 0xFFFFFFFF


def getHashTableLength(numEntries):
    count = numEntries
    if numEntries < 3:
        count = 3
    elif numEntries < 19:
        count |= 1
    else:
        while (count % 2 == 0
            or count % 3 == 0
            or count % 5 == 0
            or count % 7 == 0
            or count % 11 == 0
            or count % 13 == 0
            or count % 17 == 0):
            count += 1
    return count

def calcPathHash(Name, ParentOffset):
    hash = ParentOffset ^ 123456789
    for j in range(len(Name) // 2):
        i = j * 2
        hash = (hash >> 5) | (hash << 27)
        hash ^= (Name[i]) | (Name[i + 1] << 8)
        hash &= 0xFFFFFFFF
    return hash

class BaseEntry:
    def __init__(self):
        self.selfoffset = 0
        self.parentoffset = 0
        self.nextoffset = INVALID
        self.name = ""
        self.utf16name = b""
        self.nextcollision = INVALID

    def setName(self, name):
        self.name = name
        self.utf16name = name.encode(encoding="utf_16_le")

    def needPadding(self):
        return len(self.utf16name) % 4 != 0

    def calcHash(self):
        return calcPathHash(self.utf16name, self.parentoffset)

class RomfsDir(BaseEntry):
    def __init__(self):
        super().__init__()
        self.subdiroffset = INVALID
        self.subfileoffset = INVALID

        self.subdir = []
        self.subfile = []
        self.totaldir = 1
        self.totalfile = 0

    def entrySize(self):
        return 0x18 + len(self.utf16name) + (2 if self.needPadding() else 0)

    def toBytes(self):
        return struct.pack("<IIIIII",
            self.parentoffset, self.nextoffset, self.subdiroffset, self.subfileoffset, self.nextcollision, len(self.utf16name)) \
            + self.utf16name \
            + (b"\0\0" if self.needPadding() else b"")


class RomfsFile(BaseEntry):
    def __init__(self):
        super().__init__()
        self.dataoffset = 0
        self.size = 0
        self.data = None

    def entrySize(self):
        return 0x20 + len(self.utf16name) + (2 if self.needPadding() else 0)

    def toBytes(self):
        return struct.pack("<IIQQII",
            self.parentoffset, self.nextoffset, self.dataoffset, self.size, self.nextcollision, len(self.utf16name)) \
            + self.utf16name \
            + (b"\0\0" if self.needPadding() else b"")

def loadRomfsTree(path):
    dir = RomfsDir()

    for entry in os.listdir(path):
        subpath = os.path.join(path, entry)
        if os.path.isdir(subpath):
            subdir = loadRomfsTree(subpath)
            subdir.setName(entry)
            dir.subdir.append(subdir)
            dir.totaldir += subdir.totaldir
            dir.totalfile += subdir.totalfile
        else:
            subfile = RomfsFile()
            subfile.setName(entry)
            with open(subpath, "rb") as f:
                subfile.data = f.read()
            subfile.size = len(subfile.data)
            if len(subfile.data) % 16 != 0:
                subfile.data += b'\0' * (16 - len(subfile.data) % 16)
            dir.subfile.append(subfile)
            dir.totalfile += 1

    dir.subdir.sort(key = lambda c: c.name.upper())
    dir.subfile.sort(key = lambda c: c.name.upper())
    return dir



def fillTree(tree, dirmetaoffset, filemetaoffset, filedataoffset, dirhashtable, filehashtable):
    prevdir = None
    for subdir in tree.subdir:
        subdir.selfoffset = dirmetaoffset
        if prevdir is not None:
            prevdir.nextoffset = subdir.selfoffset
        subdir.parentoffset = tree.selfoffset

        hashentry = subdir.calcHash() % len(dirhashtable)
        subdir.nextcollision = dirhashtable[hashentry]
        dirhashtable[hashentry] = subdir.selfoffset

        dirmetaoffset += subdir.entrySize()
        prevdir = subdir

    prevfile = None
    for subfile in tree.subfile:
        subfile.selfoffset = filemetaoffset
        subfile.dataoffset = filedataoffset
        if prevfile is not None:
            prevfile.nextoffset = subfile.selfoffset
        subfile.parentoffset = tree.selfoffset

        hashentry = subfile.calcHash() % len(filehashtable)
        subfile.nextcollision = filehashtable[hashentry]
        filehashtable[hashentry] = subfile.selfoffset

        filemetaoffset += subfile.entrySize()
        filedataoffset += len(subfile.data)
        prevfile = subfile

    for subdir in tree.subdir:
        if len(subdir.subdir) != 0:
            subdir.subdiroffset = dirmetaoffset
        if len(subdir.subfile) != 0:
            subdir.subfileoffset = filemetaoffset
        dirmetaoffset, filemetaoffset, filedataoffset = \
           fillTree(subdir, dirmetaoffset, filemetaoffset, filedataoffset, dirhashtable, filehashtable)

    return dirmetaoffset, filemetaoffset, filedataoffset

def treeToData(tree, dirmeta, filemeta, filedata):
    for subdir in tree.subdir:
        assert len(dirmeta) == subdir.selfoffset
        dirmeta += subdir.toBytes()

    for subfile in tree.subfile:
        assert len(filemeta) == subfile.selfoffset
        assert len(filedata) == subfile.dataoffset
        filemeta += subfile.toBytes()
        filedata += subfile.data
        subfile.data = None

    for subdir in tree.subdir:
        treeToData(subdir, dirmeta, filemeta, filedata)


def buildRomfs(path, target):
    tree = loadRomfsTree(path)
    dirhashtable = [0xFFFFFFFF] * getHashTableLength(tree.totaldir)
    filehashtable = [0xFFFFFFFF] * getHashTableLength(tree.totalfile)
    virtualroot = RomfsDir()
    virtualroot.subdir.append(tree)
    tree = virtualroot
    fillTree(tree, 0, 0, 0, dirhashtable, filehashtable)
    dirmeta = bytearray()
    filemeta = bytearray()
    filedata = bytearray()
    treeToData(tree, dirmeta, filemeta, filedata)

    dirhash = b''.join([struct.pack("<I", x) for x in dirhashtable])
    filehash = b''.join([struct.pack("<I", x) for x in filehashtable])
    with open(target, "wb") as f:
        offset = 0x28
        f.write(struct.pack("<I", 0x28))

        f.write(struct.pack("<I", offset))
        f.write(struct.pack("<I", len(dirhash)))
        offset += len(dirhash)

        f.write(struct.pack("<I", offset))
        f.write(struct.pack("<I", len(dirmeta)))
        offset += len(dirmeta)


        f.write(struct.pack("<I", offset))
        f.write(struct.pack("<I", len(filehash)))
        offset += len(filehash)

        f.write(struct.pack("<I", offset))
        f.write(struct.pack("<I", len(filemeta)))
        offset += len(filemeta)

        padding = 0
        if offset % 16 != 0:
            padding = 16 - offset % 16

        offset += padding
        f.write(struct.pack("<I", offset))

        f.write(dirhash)
        f.write(dirmeta)
        f.write(filehash)
        f.write(filemeta)
        f.write(b'\0' * padding)
        f.write(filedata)


def extractRomfs(f, output_dir):
    romfs = open(f, 'rb')
    offset = 0

    header_len, \
        dir_hash_off, dir_hash_len, dir_meta_off, dir_meta_len, \
        file_hash_off, file_hash_len, file_meta_off, file_meta_len, \
        file_data_off = struct.unpack('IIIIIIIIII', romfs.read(0x28))

    def valid(a):
        return a != 0xFFFFFFFF

    def extract_dir(dir_offset, parent_name):
        nonlocal romfs, output_dir, offset, dir_meta_off
        while valid(dir_offset):
            romfs.seek(offset + dir_meta_off + dir_offset, os.SEEK_SET)
            parent_offset, next_dir_offset, first_child_dir_offset, first_file_offset, \
                hash_pointer, name_len = struct.unpack('IIIIII', romfs.read(0x18))
            name = romfs.read(name_len).decode('utf-16le')
            dirpath = os.path.join(output_dir, parent_name, name)
            if not os.path.isdir(dirpath):
                os.mkdir(dirpath)
            if valid(first_file_offset):
                extract_file(first_file_offset, os.path.join(parent_name, name))
            if valid(first_child_dir_offset):
                extract_dir(first_child_dir_offset, os.path.join(parent_name, name))
            dir_offset = next_dir_offset

    def extract_file(file_offset, parent_name):
        nonlocal romfs, output_dir, offset, file_meta_off
        while valid(file_offset):
            romfs.seek(offset + file_meta_off + file_offset, os.SEEK_SET)
            parent_offset, next_file_offset, data_offset, data_len, \
                hash_pointer, name_len = struct.unpack('IIQQII', romfs.read(0x20))
            name = romfs.read(name_len).decode('utf-16le')
            romfs.seek(offset + file_data_off + data_offset)
            file = open(os.path.join(output_dir, parent_name, name), 'wb')
            file.write(romfs.read(data_len))
            file.close()
            file_offset = next_file_offset

    extract_dir(0, '')
