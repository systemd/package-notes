# SPDX-License-Identifier: CC0-1.0

from _notes import ELFFileReader, group_by_soname, generate_rpm

def test_sonames():
    expected = {
        'libfido2.so.1': 'required',
        'liblz4.so.1': 'recommended',
        'libpcre2-8.so.0': 'suggested',
        'libpcre2-8.so.1': 'suggested',
        'libtss2-esys.so.0': 'recommended',
        'libtss2-mu.so.0': 'recommended',
    }
    notes = ELFFileReader('notes')
    assert group_by_soname([notes]) == expected

def test_requires():
    notes = ELFFileReader('notes')

    expected = {
        32: [
            'Suggests: libpcre2-8.so.0',
            'Suggests: libtss2-mu.so.0',
            'Suggests: libtss2-esys.so.0',
        ],
        64: [
            'Suggests: libpcre2-8.so.0()(64bit)',
            'Suggests: libtss2-mu.so.0()(64bit)',
            'Suggests: libtss2-esys.so.0()(64bit)',
        ],
    }

    lines = generate_rpm([notes], 'Suggests', ('pcre2', 'tpm'))
    expect = expected[notes.elffile.elfclass]
    assert lines == expect
