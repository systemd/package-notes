#!/usr/bin/env python3

"""
$ ./generate-package-notes.py --package-type rpm --package-name systemd --package-version 248~rc2-1.fc34 --vendor-type https://fedoraproject.org/ --vendor-name Fedora --vendor-version 34
SECTIONS
{
    .note.package ALIGN(8): {
        BYTE(0x04) BYTE(0x00) BYTE(0x00) BYTE(0x00) /* Length of Owner including NUL */
        BYTE(0x17) BYTE(0x00) BYTE(0x00) BYTE(0x00) /* Length of Value including NUL */
        BYTE(0x00) BYTE(0x33) BYTE(0xdd) BYTE(0x7a) /* Note ID */
        BYTE(0x72) BYTE(0x70) BYTE(0x6d) BYTE(0x00) /* Owner: 'rpm\x00' */
        BYTE(0x73) BYTE(0x79) BYTE(0x73) BYTE(0x74) /* Value: 'systemd\x00248~rc2-1.fc34\x00\x00' */
        BYTE(0x65) BYTE(0x6d) BYTE(0x64) BYTE(0x00)
        BYTE(0x32) BYTE(0x34) BYTE(0x38) BYTE(0x7e)
        BYTE(0x72) BYTE(0x63) BYTE(0x32) BYTE(0x2d)
        BYTE(0x31) BYTE(0x2e) BYTE(0x66) BYTE(0x63)
        BYTE(0x33) BYTE(0x34) BYTE(0x00) BYTE(0x00)
    }
    .note.package.vendor ALIGN(8): {
        BYTE(0x1b) BYTE(0x00) BYTE(0x00) BYTE(0x00) /* Length of Owner including NUL */
        BYTE(0x0a) BYTE(0x00) BYTE(0x00) BYTE(0x00) /* Length of Value including NUL */
        BYTE(0x00) BYTE(0x33) BYTE(0xdd) BYTE(0x7a) /* Note ID */
        BYTE(0x68) BYTE(0x74) BYTE(0x74) BYTE(0x70) /* Owner: 'https://fedoraproject.org/\x00\x00' */
        BYTE(0x73) BYTE(0x3a) BYTE(0x2f) BYTE(0x2f)
        BYTE(0x66) BYTE(0x65) BYTE(0x64) BYTE(0x6f)
        BYTE(0x72) BYTE(0x61) BYTE(0x70) BYTE(0x72)
        BYTE(0x6f) BYTE(0x6a) BYTE(0x65) BYTE(0x63)
        BYTE(0x74) BYTE(0x2e) BYTE(0x6f) BYTE(0x72)
        BYTE(0x67) BYTE(0x2f) BYTE(0x00) BYTE(0x00)
        BYTE(0x46) BYTE(0x65) BYTE(0x64) BYTE(0x6f) /* Value: 'Fedora\x0034\x00\x00\x00' */
        BYTE(0x72) BYTE(0x61) BYTE(0x00) BYTE(0x33)
        BYTE(0x34) BYTE(0x00) BYTE(0x00) BYTE(0x00)
    }
}
INSERT AFTER .note.gnu.build-id;
"""

import argparse

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--package-type', default='package')
    p.add_argument('--package-name')
    p.add_argument('--package-version')
    p.add_argument('--vendor-type', default='vendor')
    p.add_argument('--vendor-name')
    p.add_argument('--vendor-version')

    return p.parse_args()

def encode_bytes(arr):
    return ' '.join(f'BYTE(0x{n:02x})' for n in arr)

def encode_bytes_lines(arr, prefix='', label='string'):
    assert len(arr) % 4 == 0
    s = bytes(arr).decode()
    yield prefix + encode_bytes(arr[:4]) + f' /* {label}: {s!r} */'
    for offset in range(4, len(arr), 4):
        yield prefix + encode_bytes(arr[offset:offset+4])

def encode_length(s, prefix='', label='string'):
    n = (len(s) + 1) * 4 // 4
    n1 = n % 0xFF
    n2 = n // 0xFF
    assert n2 < 0xFF
    return prefix + encode_bytes([n1, n2, 0, 0]) + f' /* Length of {label} including NUL */'

def encode_note_id(arr, prefix=''):
    assert len(arr) == 4
    return prefix + encode_bytes(arr) + f' /* Note ID */'

def pad_string(s):
    return [0] * ((len(s) + 4) // 4 * 4 - len(s))

def encode_string(s, prefix='', label='string'):
    arr = list(s.encode()) + pad_string(s)
    yield from encode_bytes_lines(arr, prefix=prefix, label=label)

def encode_note(note_name, note_id, owner, value, prefix=''):
    l1 = encode_length(owner, prefix=prefix + '    ', label='Owner')
    l2 = encode_length(value, prefix=prefix + '    ', label='Value')
    l3 = encode_note_id(note_id, prefix=prefix + '    ')
    l4 = encode_string(owner, prefix=prefix + '    ', label='Owner')
    l5 = encode_string(value, prefix=prefix + '    ', label='Value')
    return [prefix + f'.note.{note_name} ALIGN(8): {{',
            l1, l2, l3, *l4, *l5,
            prefix + '}']

NOTE_ID = [0x00, 0x33, 0xDD, 0x7A]

def generate_sections(opts):
    s1 = encode_note('package',        NOTE_ID, opts.package_type,
                     f'{opts.package_name}\0{opts.package_version}', prefix='    ')
    s2 = encode_note('package.vendor', NOTE_ID, opts.vendor_type,
                     f'{opts.vendor_name}\0{opts.vendor_version}', prefix='    ')
    return ['SECTIONS', '{',
            *s1,
            *s2,
            '}', 'INSERT AFTER .note.gnu.build-id;']

if __name__ == '__main__':
    opts = parse_args()
    lines = generate_sections(opts)

    print('\n'.join(lines))
