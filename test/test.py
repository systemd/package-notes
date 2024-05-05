# SPDX-License-Identifier: CC0-1.0

from _notes import read_dlopen_notes, group_by_soname

def test_notes():
    expected = {
        'libfido2.so.1': 'required',
        'liblz4.so.1': 'recommended',
        'libpcre2-8.so.0': 'suggested',
        'libpcre2-8.so.1': 'suggested',
        'libtss2-esys.so.0': 'recommended',
        'libtss2-mu.so.0': 'recommended',
    }
    notes = [read_dlopen_notes('notes')]
    assert group_by_soname(notes) == expected
