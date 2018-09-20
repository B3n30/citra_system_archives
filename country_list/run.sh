#!/bin/sh

./country-archive.py -c country.json COUNTRY_LIST_DATA

echo -n "// Git Hash: " > country_list.app.romfs.h
git rev-parse HEAD >> country_list.app.romfs.h
echo "" >> country_list.app.romfs.h
xxd -i COUNTRY_LIST_DATA >> country_list.app.romfs.h
mv COUNTRY_LIST_DATA 00000000.app.romfs
