ELF Package Notes Reference Implementation

## Description

This repository provides a script to generate an ELF note that can be
linked into compiled binaries (programs and shared libraries) to provide
metadata about the package for which the binary was compiled.

See [Package Metadata for Core Files](https://systemd.io/COREDUMP_PACKAGE_METADATA/)
for the overview and details.

We provide implementations in Python and POSIX shell, with compatible CLI
interfaces.

## Requirements

### generate-package-notes.py

* python3 (>= 3.5)
* python3-simplejson
* binutils (>= 2.38) [--readonly true]

### generate-package-notes.sh

* POSIX shell
* binutils (>= 2.38) [--readonly true]
