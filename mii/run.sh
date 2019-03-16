#!/bin/sh

echo "Create mii resource romfs..."
./mii.py -c custom MII_DATA

echo "Create a header file to include in citra..."
echo -n "// Git Hash: " > mii.app.romfs.h
git rev-parse HEAD >> mii.app.romfs.h
echo "" >> mii.app.romfs.h
xxd -i MII_DATA >> mii.app.romfs.h
mv MII_DATA 00000000.app.romfs

echo "Done"
