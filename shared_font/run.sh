#!/bin/sh

# Create the images
python create_png.py

# Copy reserved unicode chars
cp reserved_unicode_chars/* .

# Create the bcfnt file
python bcfnt.py -cf code.bcfnt

# Convert the bcfnt file into a romfs
mkdir romfs
./../common/lz_compress.py code.bcfnt romfs/cbf_std.bcfnt.lz
./../common/romfs.py -c romfs SHARED_FONT_DATA

# Create a header file to include in citra
echo -n "// Git Hash: " > shared_font.app.romfs.h
git rev-parse HEAD >> shared_font.app.romfs.h
echo "" >> shared_font.app.romfs.h
xxd -i SHARED_FONT_DATA >> shared_font.app.romfs.h
mv SHARED_FONT_DATA 00000000.app.romfs

# Cleanups
rm -rf romfs
rm code.bcfnt
rm code_sheet*
