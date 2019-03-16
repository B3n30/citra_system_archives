#!/bin/sh

echo "Create the images..."
./create_png.py

echo "Copy reserved unicode chars..."
cp reserved_unicode_chars/* .

echo "Create the bcfnt file..."
./bcfnt.py -cf code.bcfnt

echo "Convert the bcfnt file into a romfs..."
mkdir romfs
./../common/lz_compress.py code.bcfnt romfs/cbf_std.bcfnt.lz
./../common/romfs.py -c romfs SHARED_FONT_DATA

echo "Create a header file to include in citra..."
echo -n "// Git Hash: " > shared_font.app.romfs.h
git rev-parse HEAD >> shared_font.app.romfs.h
echo "" >> shared_font.app.romfs.h
xxd -i SHARED_FONT_DATA >> shared_font.app.romfs.h
mv SHARED_FONT_DATA 00000000.app.romfs

echo "Cleanups..."
rm -rf romfs
rm code.bcfnt
rm code_sheet*

echo "Done"
