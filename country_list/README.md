# 3DS Country List Archive Tool

Requirement: Python 3

## archive converter tool `country-archive.py`
Usage:
```
country_archive.py [-x|-c] INPUT OUTPUT
```

 - `-x`: convert archive RomFS to JSON
 - `-c`: convert JSON to archive RomFS

Note: the RomFS format is the one used in citra, which only contains level 3 of the IVFC tree.

## archive generator tool
Usage:
```
run.sh
```
Generates an archive in C/C++ source code format using `country.json` in this directory
