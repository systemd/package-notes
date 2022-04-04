#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0

"""
Generates a linker script to insert a .note.package section with a
JSON payload. The contents are derived from the specified options and the
os-release file. Use the output with -Wl,-dT,/path/to/output in $LDFLAGS.

$ ./generate-package-notes.py --package-type rpm --package-name systemd --package-version 248~rc2-1.fc34 --package-architecture x86_64 --cpe 'cpe:/o:fedoraproject:fedora:33'
SECTIONS
{
    .note.package (READONLY) : ALIGN(4) {
        BYTE(0x04) BYTE(0x00) BYTE(0x00) BYTE(0x00) /* Length of Owner including NUL */
        BYTE(0x7c) BYTE(0x00) BYTE(0x00) BYTE(0x00) /* Length of Value including NUL */
        BYTE(0x7e) BYTE(0x1a) BYTE(0xfe) BYTE(0xca) /* Note ID */
        BYTE(0x46) BYTE(0x44) BYTE(0x4f) BYTE(0x00) /* Owner: 'FDO\x00' */
        BYTE(0x7b) BYTE(0x22) BYTE(0x74) BYTE(0x79) /* Value: '{"type":"rpm","name":"systemd","version":"248~rc2-1.fc34","architecture":"x86_64","osCpe":"cpe:/o:fedoraproject:fedora:33"}\x00' */
        BYTE(0x70) BYTE(0x65) BYTE(0x22) BYTE(0x3a)
        BYTE(0x22) BYTE(0x72) BYTE(0x70) BYTE(0x6d)
        BYTE(0x22) BYTE(0x2c) BYTE(0x22) BYTE(0x6e)
        BYTE(0x61) BYTE(0x6d) BYTE(0x65) BYTE(0x22)
        BYTE(0x3a) BYTE(0x22) BYTE(0x73) BYTE(0x79)
        BYTE(0x73) BYTE(0x74) BYTE(0x65) BYTE(0x6d)
        BYTE(0x64) BYTE(0x22) BYTE(0x2c) BYTE(0x22)
        BYTE(0x76) BYTE(0x65) BYTE(0x72) BYTE(0x73)
        BYTE(0x69) BYTE(0x6f) BYTE(0x6e) BYTE(0x22)
        BYTE(0x3a) BYTE(0x22) BYTE(0x32) BYTE(0x34)
        BYTE(0x38) BYTE(0x7e) BYTE(0x72) BYTE(0x63)
        BYTE(0x32) BYTE(0x2d) BYTE(0x31) BYTE(0x2e)
        BYTE(0x66) BYTE(0x63) BYTE(0x33) BYTE(0x34)
        BYTE(0x22) BYTE(0x2c) BYTE(0x22) BYTE(0x61)
        BYTE(0x72) BYTE(0x63) BYTE(0x68) BYTE(0x69)
        BYTE(0x74) BYTE(0x65) BYTE(0x63) BYTE(0x74)
        BYTE(0x75) BYTE(0x72) BYTE(0x65) BYTE(0x22)
        BYTE(0x3a) BYTE(0x22) BYTE(0x78) BYTE(0x38)
        BYTE(0x36) BYTE(0x5f) BYTE(0x36) BYTE(0x34)
        BYTE(0x22) BYTE(0x2c) BYTE(0x22) BYTE(0x6f)
        BYTE(0x73) BYTE(0x43) BYTE(0x70) BYTE(0x65)
        BYTE(0x22) BYTE(0x3a) BYTE(0x22) BYTE(0x63)
        BYTE(0x70) BYTE(0x65) BYTE(0x3a) BYTE(0x2f)
        BYTE(0x6f) BYTE(0x3a) BYTE(0x66) BYTE(0x65)
        BYTE(0x64) BYTE(0x6f) BYTE(0x72) BYTE(0x61)
        BYTE(0x70) BYTE(0x72) BYTE(0x6f) BYTE(0x6a)
        BYTE(0x65) BYTE(0x63) BYTE(0x74) BYTE(0x3a)
        BYTE(0x66) BYTE(0x65) BYTE(0x64) BYTE(0x6f)
        BYTE(0x72) BYTE(0x61) BYTE(0x3a) BYTE(0x33)
        BYTE(0x33) BYTE(0x22) BYTE(0x7d) BYTE(0x00)
    }
}
INSERT AFTER .note.gnu.build-id;
/* HINT: add -Wl,-dT,/path/to/this/file to $LDFLAGS */

See https://systemd.io/COREDUMP_PACKAGE_METADATA/ for details.
"""

__version__ = '0.8'

import argparse
import itertools
import os
import re
from pathlib import Path

import simplejson as json

DOC_PARAGRAPHS = ['\n'.join(group)
                  for (key, group) in itertools.groupby(__doc__.splitlines(), bool)
                  if key]

def read_os_release(field, root=Path('/')):
    try:
        f = open(root / 'etc/os-release')
    except FileNotFoundError:
        f = open(root / 'usr/lib/os-release')

    prefix = '{}='.format(field)
    for line in f:
        if line.startswith(prefix):
            break
    else:
        return None

    value = line.rstrip()
    value = value[value.startswith(prefix) and len(prefix):]
    if value[0] in '"\'' and value[0] == value[-1]:
        value = value[1:-1]

    return value

def str_to_bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in {'yes', 'true', '1'}:
        return True
    if v.lower() in {'no', 'false', '0'}:
        return False
    raise argparse.ArgumentTypeError('"yes"/"true"/"1"/"no"/"false"/"0" expected')

def parse_args():
    p = argparse.ArgumentParser(description=DOC_PARAGRAPHS[0],
                                epilog=DOC_PARAGRAPHS[-1],
                                allow_abbrev=False)
    p.add_argument('--package-type', metavar='TYPE',
                   default='package',
                   help='Specify the package type, e.g. "rpm" or "deb"')
    p.add_argument('--package-name', metavar='NAME',
                   help='The name of the package (e.g. "foo" or "libbar")')
    p.add_argument('--package-version', metavar='VERSION',
                   help='The full version of the package (e.g. 1.5-1.fc35.s390x)')
    p.add_argument('--package-architecture', metavar='ARCH',
                   help='The code architecture of the binaries (e.g. arm64 or s390x)')
    p.add_argument('--cpe',
                   help='NIST CPE identifier of the vendor operating system, or \'auto\' to parse from system-release-cpe or os-release')
    p.add_argument('--rpm', metavar='NEVRA',
                   help='Extract type,name,version,architecture from a full rpm name')
    p.add_argument('--debug-info-url', metavar='URL',
                   help='URL of the debuginfod server where sources can be queried')
    p.add_argument('--readonly', metavar='BOOL',
                   type=str_to_bool, default=True,
                   help='Make the notes section read-only (requires binutils 2.38)')
    p.add_argument('--root', metavar='PATH', type=Path, default="/",
                   help='When a file (eg: /usr/lib/os-release) is parsed, open it relatively from this hierarchy')
    p.add_argument('--version', action='version', version=f'%(prog)s {__version__}')

    opts = p.parse_args()

    return opts

def encode_bytes(arr):
    return ' '.join('BYTE(0x{:02x})'.format(n) for n in arr)

def encode_bytes_lines(arr, prefix='', label='string'):
    assert len(arr) % 4 == 0
    s = bytes(arr).decode()
    yield prefix + encode_bytes(arr[:4]) + ' /* {}: {!r} */'.format(label, s)
    for offset in range(4, len(arr), 4):
        yield prefix + encode_bytes(arr[offset:offset+4])

def encode_length(s, prefix='', label='string'):
    n = (len(s) + 1) * 4 // 4
    return f'{prefix}LONG(0x{n:04x})                                /* Length of {label} including NUL */'

def encode_note_id(id, prefix=''):
    return f'{prefix}LONG(0x{id:04x})                            /* Note ID */'

def pad_string(s):
    return [0] * ((len(s) + 4) // 4 * 4 - len(s))

def encode_string(s, prefix='', label='string'):
    arr = list(s.encode()) + pad_string(s)
    yield from encode_bytes_lines(arr, prefix=prefix, label=label)

def encode_note(note_name, note_id, owner, value, readonly=True, prefix=''):
    l1 = encode_length(owner, prefix=prefix + '    ', label='Owner')
    l2 = encode_length(value, prefix=prefix + '    ', label='Value')
    l3 = encode_note_id(note_id, prefix=prefix + '    ')
    l4 = encode_string(owner, prefix=prefix + '    ', label='Owner')
    l5 = encode_string(value, prefix=prefix + '    ', label='Value')
    readonly = '(READONLY) ' if readonly else ''

    return [prefix + '.note.{} {}: ALIGN(4) {{'.format(note_name, readonly),
            l1, l2, l3, *l4, *l5,
            prefix + '}']

NOTE_ID= 0xcafe1a7e

def json_serialize(s):
    # Avoid taking space in the ELF header if there's no value to store
    return json.dumps({k: v for k, v in s.items() if v is not None},
                      ensure_ascii=False,
                      separators=(',', ':'))

def gather_data(opts):
    if opts.cpe == 'auto':
        try:
            with open(Path(opts.root, 'usr/lib/system-release-cpe'), 'r') as f:
                opts.cpe = f.read()
        except FileNotFoundError:
            opts.cpe = read_os_release('CPE_NAME', root=opts.root)
            if opts.cpe is None or opts.cpe == "":
                raise ValueError(f"Could not read {opts.root}usr/lib/system-release-cpe or CPE_NAME from {opts.root}usr/lib/os-release")

    if opts.rpm:
        split = re.match(r'(.*?)-([0-9].*)\.(.*)', opts.rpm)
        if not split:
            raise ValueError('{!r} does not seem to be a valid package name'.format(opts.rpm))
        opts.package_type = 'rpm'
        opts.package_name = split.group(1)
        opts.package_version = split.group(2)
        opts.package_architecture = split.group(3)

    data = {
        'type':         opts.package_type,
        'name':         opts.package_name,
        'version':      opts.package_version,
        'architecture': opts.package_architecture,
    }
    if opts.cpe:
        data['osCpe'] = opts.cpe
    else:
        data['os'] = read_os_release('ID', root=opts.root)
        data['osVersion'] = read_os_release('VERSION_ID', root=opts.root)
    if opts.debug_info_url:
        data['debugInfoUrl'] = opts.debug_info_url
    return data

def generate_section(data, readonly=True):
    json = json_serialize(data)

    section = encode_note('package', NOTE_ID, 'FDO', json, readonly=readonly, prefix='    ')
    return ['SECTIONS', '{',
            *section,
            '}',
            'INSERT AFTER .note.gnu.build-id;',
            '/* HINT: add -Wl,-dT,/path/to/this/file to $LDFLAGS */']

if __name__ == '__main__':
    opts = parse_args()
    data = gather_data(opts)
    lines = generate_section(data, readonly=opts.readonly)

    print('\n'.join(lines))
