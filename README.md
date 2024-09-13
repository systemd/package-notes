ELF Package and Dlopen Notes Reference Implementation

## Description

This repository provides RPM and DEB packaging tools to generate an
`.note.package` ELF note that will be linked into compiled binaries (programs
and shared libraries) to provide metadata about the package for which the
binary was compiled.

See [Package Metadata for Core Files](https://systemd.io/ELF_PACKAGE_METADATA/)
for the overview and details.

When building binaries, the `--package-metadata` option provided by
`bfd`, `gold`, `mold`, and `lld` shall be used to inject the metadata
into the binary.

### Displaying package notes

Raw:
```console
$ objdump -j .note.package -s /usr/bin/ls

/usr/bin/ls:     file format elf64-x86-64

Contents of section .note.package:
 03cc 04000000 7c000000 7e1afeca 46444f00  ....|...~...FDO.
 03dc 7b227479 7065223a 2272706d 222c226e  {"type":"rpm","n
 03ec 616d6522 3a22636f 72657574 696c7322  ame":"coreutils"
 03fc 2c227665 7273696f 6e223a22 392e342d  ,"version":"9.4-
 040c 372e6663 3430222c 22617263 68697465  7.fc40","archite
 041c 63747572 65223a22 7838365f 3634222c  cture":"x86_64",
 042c 226f7343 7065223a 22637065 3a2f6f3a  "osCpe":"cpe:/o:
 043c 6665646f 72617072 6f6a6563 743a6665  fedoraproject:fe
 044c 646f7261 3a343022 7d000000           dora:40"}...
```

Pretty:
```console
$ systemd-analyze inspect-elf /usr/bin/ls
           path: /usr/bin/ls
        elfType: executable
elfArchitecture: AMD x86-64

           type: rpm
           name: coreutils
        version: 9.4-7.fc40
   architecture: x86_64
          osCpe: cpe:/o:fedoraproject:fedora:40
        buildId: 40e5a1570a9d97fc48f5c61cfb7690fec0f872b2
```

## `dlopen()` metadata

This package also provides scripts to extract and display
`.note.dlopen` ELF notes that are used to describe libraries loaded via `dlopen(3)`.

See [`dlopen()` Metadata for ELF Files](https://systemd.io/ELF_DLOPEN_METADATA/)
for the overview and details.

### Displaying `dlopen()` notes

Raw:
```console
$ objdump -j .note.dlopen -s /usr/lib64/systemd/libsystemd-shared-257.so

/usr/lib64/systemd/libsystemd-shared-257.so:     file format elf64-x86-64

Contents of section .note.dlopen:
 0334 04000000 8e000000 0a0c7c40 46444f00  ..........|@FDO.
 0344 5b7b2266 65617475 7265223a 22627066  [{"feature":"bpf
 0354 222c2264 65736372 69707469 6f6e223a  ","description":
 0364 22537570 706f7274 20666972 6577616c  "Support firewal
 0374 6c696e67 20616e64 2073616e 64626f78  ling and sandbox
 0384 696e6720 77697468 20425046 222c2270  ing with BPF","p
 0394 72696f72 69747922 3a227375 67676573  riority":"sugges
 03a4 74656422 2c22736f 6e616d65 223a5b22  ted","soname":["
 03b4 6c696262 70662e73 6f2e3122 2c226c69  libbpf.so.1","li
 03c4 62627066 2e736f2e 30225d7d 5d000000  bbpf.so.0"]}]...
 03d4 04000000 9e000000 0a0c7c40 46444f00  ..........|@FDO.
...
```

Pretty:
```console
$ dlopen-notes /usr/lib64/systemd/libsystemd-shared-257.so
# /usr/lib64/systemd/libsystemd-shared-257.so
[
  {
    "feature": "bpf",
    "description": "Support firewalling and sandboxing with BPF",
    "priority": "suggested",
    "soname": [
      "libbpf.so.1",
      "libbpf.so.0"
    ]
  },
...
```

## Requirements
* binutils (>= 2.39)
* mold (>= 1.3.0)
* lld (>= 15.0.0)
* python (>= 3.8)
