#!/bin/sh

git clone --recursive https://github.com/dnasdw/3dstool
mkdir 3dstool/build
cd 3dstool/build
cmake -DUSE_DEP=OFF ..
make
cd ../..
cp ignore_3dstool.txt 3dstool/bin/Release/

# Create the images
python create_png.py

# Create the bcfnt file
python bcfnt.py -cf code.bcfnt

# Copy reserved unicode chars
cp reserved_unicode_chars/* .

# Convert the bcfnt file into a romfs
mkdir romfs
./3dstool/bin/Release/3dstool -zvf code.bcfnt --compress-type lzex --compress-out romfs/cbf_std.bcfnt.lz
./3dstool/bin/Release/3dstool -cvtf romfs romfs.bin --romfs-dir romfs
dd bs=4096 skip=1 if=romfs.bin of=SHARED_FONT_DATA

# Create a header file to include in citra
echo -n "// Git Hash: " > shared_font.app.romfs.h
git git rev-parse HEAD >> shared_font.app.romfs.h
echo "" >> shared_font.app.romfs.h
xxd -i SHARED_FONT_DATA >> shared_font.app.romfs.h
mv SHARED_FONT_DATA 00000000.app.romfs

# Cleanups
rm -rf 3dstool
rm -rf romfs
rm code.bcfnt
rm code_sheet*
rm romfs.bin
