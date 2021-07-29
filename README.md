ELF Package Notes Reference Implementation

## Description

This repository provides a script to generate an ELF note that can be
linked into compiled binaries (programs and shared libraries) to provide
metadata about the package for which the binary was compiled.

See [Package Metadata for Core Files](https://systemd.io/COREDUMP_PACKAGE_METADATA/)
for the overview and details.

## Requirements

* python3 (>= 3.5)
* python3-simplejson
* binutils (>= 2.38)
