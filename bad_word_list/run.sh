#!/bin/sh

./../3dstool/bin/Release/3dstool -cvtf romfs romfs.bin --romfs-dir romfs/
dd bs=4096 skip=1 if=romfs.bin of=TEMP_BAD_WORD_LIST_DATA
head -c 1508 TEMP_BAD_WORD_LIST_DATA > BAD_WORD_LIST_DATA

# Create a header file to include in citra
echo -n "// Git Hash: " > bad_word_list.app.romfs.h
git rev-parse HEAD >> bad_word_list.app.romfs.h
echo "" >> bad_word_list.app.romfs.h
xxd -i BAD_WORD_LIST_DATA >> bad_word_list.app.romfs.h
mv BAD_WORD_LIST_DATA 00000000.app.romfs

#Cleanup
rm romfs.bin
rm TEMP_BAD_WORD_LIST_DATA
