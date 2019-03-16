#!/bin/sh

mkdir system_archives
mkdir system_archives/shared_font
mkdir system_archives/bad_word_list
mkdir system_archives/country_list
mkdir system_archives/mii

mv shared_font/shared_font.app.romfs.h system_archives/shared_font/
mv shared_font/00000000.app.romfs system_archives/shared_font/

mv bad_word_list/shared_font.app.romfs.h system_archives/bad_word_list/
mv bad_word_list/00000000.app.romfs system_archives/bad_word_list/

mv country_list/shared_font.app.romfs.h system_archives/country_list/
mv country_list/00000000.app.romfs system_archives/country_list/

mv mii/shared_font.app.romfs.h system_archives/mii/
mv mii/00000000.app.romfs system_archives/mii/

7z a "system_archives.7z" system_archives
