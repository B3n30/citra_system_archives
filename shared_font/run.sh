#!/bin/sh

git clone --recursive https://github.com/dnasdw/3dstool
mkdir 3dstool/build
cd 3dstool/build
cmake ..
make
cd ../..
cp ignore_3dstool.txt 3dstool/bin/Release/
python create_png.py
python bcfnt.py -cf code.bcfnt
mkdir romfs
./3dstool/bin/Release/3dstool -zvf code.bcfnt --compress-type lzex --compress-out romfs/cbf_std.bcfnt.lz
./3dstool/bin/Release/3dstool -cvtf romfs romfs.bin --romfs-dir romfs
dd bs=4096 skip=1 if=romfs.bin of=00000000.app.romfs
rm -rf 3dstool
rm -rf romfs
rm code.bcfnt
rm code_sheet*
rm romfs.bin
