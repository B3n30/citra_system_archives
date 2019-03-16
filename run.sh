#!/bin/sh

echo "Create the Shared Font..."
cd shared_font
./run.sh
cd ..

echo "Create the Bad Word List..."
cd bad_word_list
./run.sh
cd ..

echo "Create the country list..."
cd country_list
./run.sh
cd ..

echo "Create the mii database..."
cd mii
./run.sh
cd ..

echo "All done"
