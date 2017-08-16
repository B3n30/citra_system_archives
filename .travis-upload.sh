#!/bin/sh

mkdir system_archives
mkdir system_archives/shared_font

mv shared_font/shared_font.app.romfs.h artifacts/shared_font/
mv shared_font/00000000.app.romfs artifacts/shared_font/

7z a "system_archives.7z" system_archives
