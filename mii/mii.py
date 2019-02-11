#!/usr/bin/env python3

# Copyright 2019 Weiyi Wang
# Licensed under GPLv2 or any later version
# Refer to the license.txt file included.

from PIL import Image
import os
import sys
import struct
import tempfile
import shutil
sys.path.append('../')
from common import romfs

def pow(i):
    o = 1
    while o < i:
        o *= 2
    return o

def ispow2(i):
    return i != 0 and ((i & (i - 1)) == 0)

def Decode4(p):
    return (p * 0x11, p * 0x11, p * 0x11, 0xFF)

def Decode8(p):
    return ((p >> 4) * 0x11, (p >> 4) * 0x11, (p >> 4) * 0x11, (p & 0xf) * 0x11)

def Decode16(p):
    r = (p >> 12) & 0xf
    g = (p >> 8) & 0xf
    b = (p >> 4) & 0xf
    a = p & 0xf
    return (r * 0x11, g * 0x11, b * 0x11, a*0x11)

def Encode4(p):
    return p[0] >> 4

def Encode8(p):
    return (p[0] >> 4 << 4) + (p[3] >> 4)

def Encode16(p):
    return (p[0] >> 4 << 12) + (p[1] >> 4 << 8) + (p[2] >> 4 << 4) + (p[3] >> 4)

bpp = {
0:4,
2:4,
4:8,
10:16
}

decoder = {
0:Decode4,
2:Decode4,
4:Decode8,
10:Decode16
}

encoder = {
0:Encode4,
2:Encode4,
4:Encode8,
10:Encode16
}

item_counts = [
    0x0004,
    0x0108,
    0x000C,
    0x0108,
    0x0001,
    0x0108,
    0x000C,
    0x0012,
    0x0012,
    0x0084,
    0x003E,
    0x0018,
    0x0003,
    0x000C,
    0x000C,
    0x0009,
    0x0002,
    0x0025,
    0x0006,
    0x0012
]

def GetAddress(w, x, y):
    cx = x // 8
    cy = y // 8
    fx = x % 8
    fy = y % 8
    line = cy * w * 8
    tile = line + cx * 64
    xlut = [0x00, 0x01, 0x04, 0x05, 0x10, 0x11, 0x14, 0x15]
    ylut = [0x00, 0x02, 0x08, 0x0a, 0x20, 0x22, 0x28, 0x2a]
    return tile + xlut[fx] + ylut[fy]

def Build(in_path, out_path):
    root = in_path
    f = open(out_path, "wb")
    f.write(struct.pack("<HH", 20, 0x0509))

    # skip section offset table
    f.write(b'\0' * 20 * 4)

    section_offsets = []

    for section in range(20):
        section_offset = f.tell()
        section_offsets.append(f.tell())

        f.write(struct.pack("<H", item_counts[section]))
        f.write(struct.pack("<H", 0)) # skip max buffer
        f.write(b'\0' * (item_counts[section] + 1) * 4) # skip offset table
        item_base = f.tell()
        item_offsets = []
        max_buf = 0
        for item in range(item_counts[section]):
            item_offset = f.tell()
            item_offsets.append(item_offset - item_base)
            if section >= 9:
                image_path = os.path.join(root, "%d"%section, "%d.png"%item)
                extra_path = os.path.join(root, "%d"%section, "%d_extra.txt"%item)

                if not os.path.exists(image_path):
                    continue
                
                extra = open(extra_path, "rt")
                dic = {}
                for line_ in extra:
                    line = line_.rstrip('\n')
                    if len(line) == 0: continue
                    s = line.split("=")
                    dic[s[0]] = int(s[1])
                extra.close()

                format = dic["format"]
                width = dic["width"]
                height = dic["height"]

                f.write(struct.pack("<H", width))
                f.write(struct.pack("<H", height))
                f.write(struct.pack("<B", 1))
                f.write(struct.pack("<B", format))
                f.write(struct.pack("<B", dic["wrap_u"]))
                f.write(struct.pack("<B", dic["wrap_v"]))

                image = Image.open(image_path)
                w, h = image.size
                if not ispow2(w) or not ispow2(h):
                    raise Exception("Image size is not power of 2")
                if width > w or width <= w / 2 or height > h or height <= h / 2:
                    raise Exception("Image internal size doesn't match")
                image.convert(mode="RGBA")

                data = [0] * (w * h * bpp[format] // 8)
                for x in range(w):
                    for y in range(h):
                        v = image.getpixel((x,y))
                        a = GetAddress(w, x, y)
                        vv = encoder[format](v)
                        if bpp[format] == 4:
                            value = data[a // 2]
                            if a % 2 == 0:
                                data[a // 2] = (value & 0xF0) + vv
                            else:
                                data[a // 2] = (value & 0xF) + (vv << 4)
                        elif bpp[format] == 8:
                            data[a] = vv
                        elif bpp[format] == 16:
                            data[a * 2] = vv & 0xFF
                            data[a * 2 + 1] = vv >> 8
                max_buf = max(max_buf, len(data) + 8)
                for b in data:
                    f.write(struct.pack("<B", b))
            else: # section < 9
                begin = f.tell()
                obj_path = os.path.join(root, "%d"%section, "%d.obj"%item)
                extra_path = os.path.join(root, "%d"%section, "%d_extra.txt"%item)
                if not os.path.exists(obj_path):
                    continue
                if section == 2 or section == 5:
                    extra = open(extra_path, "rt")
                    dic = {}
                    for line_ in extra:
                        line = line_.rstrip('\n')
                        if len(line) == 0: continue
                        s = line.split("=")
                        k = s[1].split(",")
                        dic[s[0]] = (float(k[0]), float(k[1]), float(k[2]))
                    extra.close()
                    if section == 2:
                        f.write(struct.pack("<fff", dic["hair"][0], dic["hair"][1], dic["hair"][2]))
                        f.write(struct.pack("<fff", dic["nose"][0], dic["nose"][1], dic["nose"][2]))
                        f.write(struct.pack("<fff", dic["beard"][0], dic["beard"][1], dic["beard"][2]))
                    else:
                        f.write(struct.pack("<fff", dic["hat_a_angle"][0], dic["hat_a_angle"][1], dic["hat_a_angle"][2]))
                        f.write(struct.pack("<fff", dic["hat_a_position"][0], dic["hat_a_position"][1], dic["hat_a_position"][2]))
                        f.write(struct.pack("<fff", dic["hat_b_angle"][0], dic["hat_b_angle"][1], dic["hat_b_angle"][2]))
                        f.write(struct.pack("<fff", dic["hat_b_position"][0], dic["hat_b_position"][1], dic["hat_b_position"][2]))
                        f.write(struct.pack("<fff", dic["hat_c_angle"][0], dic["hat_c_angle"][1], dic["hat_c_angle"][2]))
                        f.write(struct.pack("<fff", dic["hat_c_position"][0], dic["hat_c_position"][1], dic["hat_c_position"][2]))
                obj = open(obj_path, "rt")
                vertex = []
                normal = []
                tex = []
                index = []
                for line_ in obj:
                    line = line_.rstrip('\n')
                    if len(line) == 0: continue
                    s = line.split(" ")
                    if s[0] == "v":
                        vertex.append((float(s[1]), float(s[2]), float(s[3])))
                    elif s[0] == "vt":
                        tex.append((float(s[1]), float(s[2])))
                    elif s[0] == "vn":
                        normal.append((float(s[1]), float(s[2]), float(s[3])))
                    elif s[0] == "f":
                        a = s[1].split("/")
                        b = s[2].split("/")
                        c = s[3].split("/")
                        index.append(int(a[0]))
                        index.append(int(b[0]))
                        index.append(int(c[0]))
                obj.close()
                f.write(struct.pack("<H", len(vertex)))
                f.write(struct.pack("<H", len(normal)))
                f.write(struct.pack("<H", len(tex)))
                f.write(struct.pack("<H", 1 if len(index) else 0))

                def R256(v): return int(round(v * 256.0))
                def R8192(v): return int(round(v * 8192.0))

                for v in range(len(vertex)):
                    f.write(struct.pack("<hhh", R256(vertex[v][0]), R256(vertex[v][1]), R256(vertex[v][2])))
                    if len(normal) > 1:
                        f.write(struct.pack("<hhh", R256(normal[v][0]), R256(normal[v][1]), R256(normal[v][2])))
                    if len(tex) > 1:
                        f.write(struct.pack("<hh", R8192(tex[v][0]), R8192(tex[v][1])))
                if len(normal) == 1:
                    f.write(struct.pack("<hhh", R256(normal[0][0]), R256(normal[0][1]), R256(normal[0][2])))
                if len(tex) == 1:
                    f.write(struct.pack("<hh", R8192(tex[0][0]), R8192(tex[0][1])))
                if len(index) != 0:
                    f.write(struct.pack("<HH", 4, len(index)))
                    for i in index:
                        f.write(struct.pack("B", i - 1))
                if section == 6:
                    extra = open(extra_path, "rt")
                    for line_ in extra:
                        line = line_.rstrip('\n')
                        if len(line) == 0: continue
                        s = line.split(",")
                        x = s[0].split("-")
                        y = s[1].split("-")
                        f.write(struct.pack("<B", (int(x[0]) << 4) + int(x[1])))
                        f.write(struct.pack("<B", (int(y[0]) << 4) + int(y[1])))
                r = f.tell() % 4
                if r != 0:
                    f.write(b'\0' * (4 - r))

                max_buf = max(max_buf, f.tell() - begin)

        redirect = open(os.path.join(root, "%d"%section, "redirect.txt"), "rt")
        for line_ in redirect:
            line = line_.rstrip('\n')
            if len(line) == 0: continue
            s = line.split("->")
            item_offsets[int(s[0])] |= (int(s[1]) + 1) << 22

        cur = f.tell()
        item_offsets.append(cur - item_base)
        f.seek(section_offset + 2)
        f.write(struct.pack("<H", max_buf))
        for o in item_offsets:
            f.write(struct.pack("<I", o))
        f.seek(cur)

    f.seek(4)
    for o in section_offsets:
        f.write(struct.pack("<I", o))
    f.close()

def Extract(in_path, out_path):
    root = out_path

    try:
        os.mkdir(root)
    except OSError:
        pass

    f = open(in_path, "rb")

    l0size, _ = struct.unpack("<HH", f.read(4))

    l0offsets = [struct.unpack("<I", f.read(4))[0] for _ in range(l0size)]

    section = 0
    for l0offset in l0offsets:
        #print("### Section ", section)

        try:
            os.mkdir(os.path.join(root, "%d"%section))
        except OSError:
            pass

        redirects = open(os.path.join(root, "%d"%section, "redirect.txt"), "wt")

        if f.tell() != l0offset:
            raise Exception("Gap found")
        #f.seek(l0offset, 0)

        l1size, bufsize = struct.unpack("<HH", f.read(4))
        l1offsets = [struct.unpack("<I", f.read(4))[0] for _ in range(l1size + 1)]
        max_size = 0
        for i in range(l1size):
            offset = l1offsets[i] & 0x3ffFFf
            size = (l1offsets[i + 1] & 0x3ffFFf) - offset
            redirect = l1offsets[i] >> 22

            max_size = max(max_size, size)
            
            if size == 0:
                if redirect != 0:
                    redirects.write("%d->%d\n" % (i, redirect - 1))
                    #print("[%03d] redirected to %03d"%(i, redirect - 1))
                else:
                    pass##print("[%03d] is empty"%(i))
                continue

            if redirect != 0:
                raise "redirect found but not empty"

            if section >= 9:
                width, height, mipmap, format, wrap_u, wrap_v = struct.unpack("<HHBBBB", f.read(8))
                if mipmap != 1:
                    raise Exception("wrong mipmap")
                #print("[%03d] image %dx%d format%d wrap%dx%d size=%d"%(i, width, height, format, wrap_u, wrap_v, size - 8))

                out = open(os.path.join(root, "%d"%section, "%d_extra.txt"%i), "wt")
                out.write("width=%d\n"%width)
                out.write("height=%d\n"%height)
                out.write("format=%d\n"%format)
                out.write("wrap_u=%d\n"%wrap_u)
                out.write("wrap_v=%d\n"%wrap_v)
                out.close()

                data = f.read(size - 8)

                wp = pow(width)
                hp = pow(height)

                if wp * hp * bpp[format] != (size - 8) * 8:
                    raise Exception("Wrong texture size")

                im = Image.new("RGBA", (wp, hp))
                for x in range(wp):
                    for y in range(hp):
                        addr = GetAddress(wp, x, y)
                        if bpp[format] == 4:
                            value = int(data[addr // 2])
                            if addr % 2 == 0:
                                value &= 0xF
                            else:
                                value >>= 4
                        elif bpp[format] == 8:
                            value = int(data[addr])
                        elif bpp[format] == 16:
                            value = int(data[addr * 2]) + (int(data[addr * 2 + 1]) << 8)
                        
                        color = decoder[format](value)
                        im.putpixel((x, y), color)

                im.save(os.path.join(root, "%d"%section, "%d.png"%i))
            else:
                if section == 2:
                    out = open(os.path.join(root, "%d"%section, "%d_extra.txt"%i), "wt")
                    hp = struct.unpack("<fff", f.read(12))
                    size -= 12
                    out.write("hair=%.8f,%.8f,%.8f\n"%(hp[0], hp[1], hp[2]))
                    hp = struct.unpack("<fff", f.read(12))
                    size -= 12
                    out.write("nose=%.8f,%.8f,%.8f\n"%(hp[0], hp[1], hp[2]))
                    hp = struct.unpack("<fff", f.read(12))
                    size -= 12
                    out.write("beard=%.8f,%.8f,%.8f\n"%(hp[0], hp[1], hp[2]))
                elif section == 5:
                    out = open(os.path.join(root, "%d"%section, "%d_extra.txt"%i), "wt")
                    hp = struct.unpack("<fff", f.read(12))
                    size -= 12
                    out.write("hat_a_angle=%.8f,%.8f,%.8f\n"%(hp[0], hp[1], hp[2]))
                    hp = struct.unpack("<fff", f.read(12))
                    size -= 12
                    out.write("hat_a_position=%.8f,%.8f,%.8f\n"%(hp[0], hp[1], hp[2]))
                    hp = struct.unpack("<fff", f.read(12))
                    size -= 12
                    out.write("hat_b_angle=%.8f,%.8f,%.8f\n"%(hp[0], hp[1], hp[2]))
                    hp = struct.unpack("<fff", f.read(12))
                    size -= 12
                    out.write("hat_b_position=%.8f,%.8f,%.8f\n"%(hp[0], hp[1], hp[2]))
                    hp = struct.unpack("<fff", f.read(12))
                    size -= 12
                    out.write("hat_c_angle=%.8f,%.8f,%.8f\n"%(hp[0], hp[1], hp[2]))
                    hp = struct.unpack("<fff", f.read(12))
                    size -= 12
                    out.write("hat_c_position=%.8f,%.8f,%.8f\n"%(hp[0], hp[1], hp[2]))
                    out.close()

                vertex_count, normal_count, texcoord_count, index_count = struct.unpack("<HHHH", f.read(8))
                size -= 8
                if normal_count != vertex_count and normal_count != 0 and normal_count != 1:
                    raise Exception("Wrong normal count")
                if texcoord_count != vertex_count and texcoord_count != 0 and texcoord_count != 1:
                    raise Exception("Wrong texcoord count")

                vertex_list = []
                normal_list = []
                texcoord_list = []

                for _ in range(vertex_count):
                    x, y, z = struct.unpack("<hhh", f.read(6))
                    size -= 6
                    vertex_list.append((x, y, z))
                    if normal_count == vertex_count:
                        nx, ny, nz = struct.unpack("<hhh", f.read(6))
                        size -= 6
                        normal_list.append((nx, ny, nz))
                    if texcoord_count == vertex_count:
                        tx, ty = struct.unpack("<hh", f.read(4))
                        size -= 4
                        texcoord_list.append((tx, ty))
                if normal_count == 1:
                    nx, ny, nz = struct.unpack("<hhh", f.read(6))
                    size -= 6
                    normal_list.append((nx, ny, nz))
                if texcoord_count == 1:
                    tx, ty = struct.unpack("<hh", f.read(4))
                    size -= 4
                    texcoord_list.append((tx, ty))
                if index_count != 0:
                    if index_count != 1:
                        raise Exception("Wrong index count")
                    magic, = struct.unpack("<H", f.read(2))
                    size -= 2
                    if magic != 4:
                        raise Exception("Wrong index list magic")
                    
                    index_count, = struct.unpack("<H", f.read(2))
                    size -= 2
                    index_list = [struct.unpack("<B", f.read(1))[0] for _ in range(index_count)]
                    size -= index_count
                    
                    if section == 6:
                        out = open(os.path.join(root, "%d"%section, "%d_extra.txt"%i), "wt")
                        extra_count = index_count // 3

                        for u in range(extra_count):
                            xx, yy = struct.unpack("<BB", f.read(2))
                            size -= 2;
                            out.write("%d-%d,%d-%d\n" % (xx >> 4, xx & 0xF, yy >> 4, yy & 0xF))

                        out.close()
                        

                if size >= 4 or size < 0:
                    raise Exception("Wrong size")

                if size != 0:
                    _ = f.read(size)

                out = open(os.path.join(root, "%d"%section, "%d.obj"%i), "wt")
                for vertex in vertex_list:
                    out.write("v %f %f %f\n"%(vertex[0] / 256.0, vertex[1] / 256.0, vertex[2] / 256.0))
                for texcoord in texcoord_list:
                    out.write("vt %f %f\n"%(texcoord[0] / 8192.0, texcoord[1] / 8192.0))
                for normal in normal_list:
                    out.write("vn %f %f %f\n"%(normal[0] / 256.0, normal[1] / 256.0, normal[2] / 256.0))

                for ii in range(index_count):
                    if ii % 3 == 0:
                        out.write("\nf")
                    vi = index_list[ii] + 1
                    ti = vi if texcoord_count == vertex_count else 1
                    ni = vi if normal_count == vertex_count else 1
                    if texcoord_count == 0:
                        if normal_count == 0:
                            out.write(" %d"%vi)
                        else:
                            out.write(" %d//%d"%(vi, ni))
                    else:
                        if normal_count == 0:
                            out.write(" %d/%d"%(vi, ti))
                        else:
                            out.write(" %d/%d/%d"%(vi, ti, ni))
                out.close()
       
        if max_size != bufsize:
            raise Exception("wrong bufsize")

        redirects.close()
        section += 1

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
        Extract(os.path.join(d, "CFL_Res.dat"), outPath)
        shutil.rmtree(d)
    elif sys.argv[1] == "-c":
        d = tempfile.mkdtemp()
        Build(inPath, os.path.join(d, "CFL_Res.dat"))
        romfs.buildRomfs(d, outPath)
        shutil.rmtree(d)
    else:
        printHelp()

if __name__ == "__main__":
    main()
