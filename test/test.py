# SPDX-License-Identifier: CC0-1.0

from _notes import ELFFileReader, group_by_soname, generate_rpm, Priority

def test_sonames():
    expected = {
        'libfido2.so.1': Priority.required,
        'liblz4.so.1': Priority.recommended,
        'libpcre2-8.so.0': Priority.suggested,
        'libpcre2-8.so.1': Priority.suggested,
        'libtss2-esys.so.0': Priority.recommended,
        'libtss2-mu.so.0': Priority.recommended,
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
    assert sorted(lines) == sorted(expect)

class FakeReader:
    def __init__(self, notes):
        self._notes = notes

    def notes(self):
        return self._notes

def test_sonames_highest_priority_stable():
    a = FakeReader([{'soname': ['libcrypto.so.3'], 'priority': 'required'}])
    b = FakeReader([{'soname': ['libcrypto.so.3'], 'priority': 'recommended'}])
    c = FakeReader([{'soname': ['libcrypto.so.3'], 'priority': 'suggested'}])

    expected = {'libcrypto.so.3': Priority.required}
    assert group_by_soname([a, b, c]) == expected
    assert group_by_soname([c, b, a]) == expected
    assert group_by_soname([b, a, c]) == expected
