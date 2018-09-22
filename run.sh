#!/bin/sh

# Build 3dstool
git clone --recursive https://github.com/dnasdw/3dstool
mkdir 3dstool/build
cd 3dstool/build
cmake -DUSE_DEP=OFF ..
make
cd ../..
cp ignore_3dstool.txt 3dstool/bin/Release/

# Create the Shared Font
cd shared_font
./run.sh
cd ..

# Create the Bad Word List
cd bad_word_list
./run.sh
cd ..

cd country_list
./run.sh
cd ..

# TODO(B3N30): Create the other system archives

# Cleanup
rm -rf 3dstool
