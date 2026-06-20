# SPDX-License-Identifier: CC0-1.0

from _notes import ELFFileReader, group_alternatives, generate_rpm, rpm_dependency, Priority

def test_sonames():
    expected = {
        ('libfido2.so.1',): Priority.required,
        ('liblz4.so.1',): Priority.recommended,
        ('libpcre2-8.so.0', 'libpcre2-8.so.1'): Priority.suggested,
        ('libtss2-esys.so.0',): Priority.recommended,
        ('libtss2-mu.so.0',): Priority.recommended,
    }
    notes = ELFFileReader('notes')
    assert group_alternatives([notes]) == expected

def test_requires():
    notes = ELFFileReader('notes')

    expected = {
        32: [
            'Suggests: (libpcre2-8.so.0 or libpcre2-8.so.1)',
            'Suggests: libtss2-mu.so.0',
            'Suggests: libtss2-esys.so.0',
        ],
        64: [
            'Suggests: (libpcre2-8.so.0()(64bit) or libpcre2-8.so.1()(64bit))',
            'Suggests: libtss2-mu.so.0()(64bit)',
            'Suggests: libtss2-esys.so.0()(64bit)',
        ],
    }

    lines = generate_rpm([notes], 'Suggests', ('pcre2', 'tpm'))
    expect = expected[notes.elffile.elfclass]
    assert sorted(lines) == sorted(expect)

def test_rpm_dependency():
    # One soname stays plain; multiple become an rpm boolean "or" dependency.
    assert rpm_dependency(['libfoo.so.1'], '') == 'libfoo.so.1'
    assert rpm_dependency(['libfoo.so.1'], '()(64bit)') == 'libfoo.so.1()(64bit)'
    assert rpm_dependency(['libfoo.so.2', 'libfoo.so.1'], '') == '(libfoo.so.2 or libfoo.so.1)'
    assert rpm_dependency(['libfoo.so.2', 'libfoo.so.1'], '()(64bit)') == \
        '(libfoo.so.2()(64bit) or libfoo.so.1()(64bit))'

class FakeReader:
    def __init__(self, notes):
        self._notes = notes

    def notes(self):
        return self._notes

def test_sonames_highest_priority_stable():
    a = FakeReader([{'soname': ['libcrypto.so.3'], 'priority': 'required'}])
    b = FakeReader([{'soname': ['libcrypto.so.3'], 'priority': 'recommended'}])
    c = FakeReader([{'soname': ['libcrypto.so.3'], 'priority': 'suggested'}])

    expected = {('libcrypto.so.3',): Priority.required}
    assert group_alternatives([a, b, c]) == expected
    assert group_alternatives([c, b, a]) == expected
    assert group_alternatives([b, a, c]) == expected

def test_alternatives_grouped():
    # Sonames in one note are alternatives and stay grouped, preferred first.
    a = FakeReader([{'soname': ['libcrypto.so.4', 'libcrypto.so.3'], 'priority': 'required'}])
    expected = {('libcrypto.so.4', 'libcrypto.so.3'): Priority.required}
    assert group_alternatives([a]) == expected

def test_alternatives_distinct_from_separate_notes():
    # Separate notes are distinct dependencies, not alternatives.
    grouped = FakeReader([{'soname': ['liba.so.1', 'libb.so.1'], 'priority': 'required'}])
    separate = FakeReader([{'soname': ['liba.so.1'], 'priority': 'required'},
                           {'soname': ['libb.so.1'], 'priority': 'required'}])

    assert group_alternatives([grouped]) == {('liba.so.1', 'libb.so.1'): Priority.required}
    assert group_alternatives([separate]) == {('liba.so.1',): Priority.required,
                                              ('libb.so.1',): Priority.required}
