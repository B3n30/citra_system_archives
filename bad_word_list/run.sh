#!/bin/sh

echo "Create bad word list romfs..."
./../common/romfs.py -c romfs BAD_WORD_LIST_DATA

echo "Create a header file to include in citra..."
echo -n "// Git Hash: " > bad_word_list.app.romfs.h
git rev-parse HEAD >> bad_word_list.app.romfs.h
echo "" >> bad_word_list.app.romfs.h
xxd -i BAD_WORD_LIST_DATA >> bad_word_list.app.romfs.h
mv BAD_WORD_LIST_DATA 00000000.app.romfs

echo "Done"
