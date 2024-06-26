ELF Package and Dlopen Notes Reference Implementation

## Description

This repository provides RPM and DEB packaging tools to generate an
`.note.package` ELF note that will be linked into compiled binaries (programs
and shared libraries) to provide metadata about the package for which the
binary was compiled.

See [Package Metadata for Core Files](https://systemd.io/ELF_PACKAGE_METADATA/)
for the overview and details.

The new `--package-metadata` option provided by `bfd`, `gold`, `mold`, and `lld` is used.

It also provides scripts to extract and display `.note.dlopen` ELF notes
that are used to describe libraries loaded via `dlopen(3)`.

See [`dlopen()` Metadata for ELF Files](https://systemd.io/ELF_DLOPEN_METADATA/)
for the overview and details.

## Requirements
* binutils (>= 2.39)
* mold (>= 1.3.0)
* lld (>= 15.0.0)
