#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0

"""\
Read .note.dlopen notes from ELF files and report the contents.
"""

import argparse
import enum
import fnmatch
import functools
import json
import sys
from elftools.elf.elffile import ELFFile
from elftools.elf.sections import NoteSection

try:
    import rich
    print_json = rich.print_json
except ImportError:
    print_json = print

def dictify(f):
    def wrap(*args, **kwargs):
        return dict(f(*args, **kwargs))
    return functools.update_wrapper(wrap, f)

def listify(f):
    def wrap(*args, **kwargs):
        return list(f(*args, **kwargs))
    return functools.update_wrapper(wrap, f)

class ELFFileReader:
    def __init__(self, filename):
        self.filename = filename
        self.elffile = ELFFile(open(filename, 'rb'))

    @functools.cache
    @listify
    def notes(self):
        for section in self.elffile.iter_sections():
            if not isinstance(section, NoteSection) or section.name != '.note.dlopen':
                continue

            for note in section.iter_notes():
                if note['n_type'] != 0x407c0c0a or note['n_name'] != 'FDO':
                    continue
                note_desc = note['n_desc']

                try:
                    # On older Python versions (e.g.: Ubuntu 22.04) we get a string, on
                    # newer versions a bytestring
                    if not isinstance(note_desc, str):
                        text = note_desc.decode('utf-8').rstrip('\0')
                    else:
                        text = note_desc.rstrip('\0')
                except UnicodeDecodeError as e:
                    raise ValueError(f'{self.filename}: Invalid UTF-8 in .note.dlopen n_desc') from e

                try:
                    j = json.loads(text)
                except json.JSONDecodeError as e:
                    raise ValueError(f'{self.filename}: Invalid JSON in .note.dlopen note_desc') from e

                if not isinstance(j, list):
                    print(f'{self.filename}: ignoring .note.dlopen n_desc with JSON that is not a list',
                          file=sys.stderr)
                    continue

                yield from j

@dictify
def group_by_soname(elffiles):
    for elffile in elffiles:
        for element in elffile.notes():
            priority = element.get('priority', 'recommended')
            for soname in element['soname']:
                yield soname, priority

class Priority(enum.Enum):
    suggested   = 1
    recommended = 2
    required    = 3

    def __lt__(self, other):
        return self.value < other.value

    def rpm_name(self):
        if self == self.__class__.suggested:
            return 'Suggests'
        if self == self.__class__.recommended:
            return 'Recommends'
        if self == self.__class__.required:
            return 'Requires'
        raise ValueError


def group_by_feature(elffiles):
    features = {}

    # We expect each note to be in the format:
    # [
    #   {
    #     "feature": "...",
    #     "description": "...",
    #     "priority": "required"|"recommended"|"suggested",
    #     "soname": ["..."],
    #   }
    # ]
    for elffiles in elffiles:
        for note in elffiles.notes():
            prio = Priority[note.get('priority', 'recommended')]
            feature_name = note['feature']

            try:
                feature = features[feature_name]
            except KeyError:
                # Create new
                feature = features[feature_name] = {
                    'description': note.get('description', ''),
                    'sonames': { soname:prio for soname in note['soname'] },
                }
            else:
                # Merge
                if feature['description'] != note.get('description', ''):
                    print(f"{note.filename}: feature {note['feature']!r} found with different description, ignoring",
                          file=sys.stderr)

                for soname in note['soname']:
                    highest = max(feature['sonames'].get(soname, Priority.suggested),
                                  prio)
                    feature['sonames'][soname] = highest

    return features

def filter_features(features, filter):
    if filter is None:
        return None
    ans = { name:feature for name,feature in features.items()
            if name in filter or not filter }
    if missing := set(filter) - set(ans):
        sys.exit('Some features not found:', ', '.join(missing))
    return ans

@listify
def generate_rpm(elffiles, stanza, filter):
    # Produces output like:
    # Requires: libqrencode.so.4()(64bit)
    # Requires: libzstd.so.1()(64bit)
    for elffile in elffiles:
        suffix = '()(64bit)' if elffile.elffile.elfclass == 64 else ''
        for note in elffile.notes():
            if note['feature'] in filter or not filter:
                soname = next(iter(note['soname']))  # we take the first — most recommended — soname
                yield f"{stanza}: {soname}{suffix}"

def rpm_fileattr_generator(args):
    if args.rpm_features is not None:
        if not any(fnmatch.fnmatch(args.subpackage, pattern[0])
                   for pattern in args.rpm_features):
            # Current subpackage is not listed, nothing to do.
            # Consume all input as required by the protocol.
            sys.stdin.read()
            return

    for file in sys.stdin:
        file = file.strip()
        if not file:
            continue  # ignore empty lines

        elffile = ELFFileReader(file)
        suffix = '()(64bit)' if elffile.elffile.elfclass == 64 else ''

        first = True

        for note in elffile.notes():
            # Feature name is optional. Allow this to be matched
            # by the empty string ('') or a wildcard glob ('*').
            feature = note.get('feature', '')

            if args.rpm_features is not None:
                for package_pattern,feature_pattern in args.rpm_features:
                    if (fnmatch.fnmatch(args.subpackage, package_pattern) and
                        fnmatch.fnmatch(feature, feature_pattern)):
                        break
                else:
                    # not matched
                    continue
            else:
                # if no mapping, print all features at the suggested level
                level = Priority[note.get('priority', 'recommended')].rpm_name()
                if level != args.rpm_fileattr:
                    continue

            if first:
                print(f';{file}')
                first = False

            soname = next(iter(note['soname']))  # we take the first — most recommended — soname
            print(f'{soname}{suffix}')


def make_parser():
    p = argparse.ArgumentParser(
        description=__doc__,
        allow_abbrev=False,
        add_help=False,
        epilog='If no option is specifed, --raw is the default.',
    )
    p.add_argument(
        '-r', '--raw',
        action='store_true',
        help='Show the original JSON extracted from input files',
    )
    p.add_argument(
        '-s', '--sonames',
        action='store_true',
        help='List all sonames and their priorities, one soname per line',
    )
    p.add_argument(
        '-f', '--features',
        nargs='?',
        const=[],
        type=lambda s: s.split(','),
        action='extend',
        metavar='FEATURE1,FEATURE2',
        help='Describe features, can be specified multiple times',
    )
    p.add_argument(
        '--rpm-requires',
        nargs='?',
        const=[],
        type=lambda s: s.split(','),
        action='extend',
        metavar='FEATURE1,FEATURE2',
        help='Generate rpm Requires for listed features',
    )
    p.add_argument(
        '--rpm-recommends',
        nargs='?',
        const=[],
        type=lambda s: s.split(','),
        action='extend',
        metavar='FEATURE1,FEATURE2',
        help='Generate rpm Recommends for listed features',
    )
    p.add_argument(
        '--rpm-fileattr',
        metavar='TYPE',
        help='Run as rpm fileattr generator for TYPE dependencies',
    )
    p.add_argument(
        '--subpackage',
        metavar='NAME',
        default='',
        help='Current subpackage NAME',
    )
    p.add_argument(
        '--rpm-features',
        metavar='SUBPACKAGE:FEATURE,SUBPACKAGE:FEATURE',
        type=lambda s: [x.split(':', maxsplit=1) for x in s.split(',')],
        action='extend',
        help='Specify subpackage:feature mapping',
    )
    p.add_argument(
        'filenames',
        nargs='*',
        metavar='FILENAME',
        help='Library file to extract notes from',
    )
    p.add_argument(
        '-h', '--help',
        action='help',
        help='Show this help message and exit',
    )
    return p

def parse_args():
    args = make_parser().parse_args()

    if (not args.raw
        and not args.sonames
        and args.features is None
        and args.rpm_requires is None
        and args.rpm_recommends is None
        and args.rpm_fileattr is None):
        # Make --raw the default if no action is specified.
        args.raw = True

    if args.rpm_fileattr is not None:
        if (args.filenames
            or args.raw
            or args.features is not None
            or args.rpm_requires
            or args.rpm_recommends):
            raise ValueError('--rpm-generate cannot be combined with most options')

    if args.rpm_fileattr is None and not args.filenames:
        raise ValueError('At least one positional FILENAME parameter is required')

    return args

if __name__ == '__main__':
    args = parse_args()

    if args.rpm_fileattr is not None:
        sys.exit(rpm_fileattr_generator(args))

    elffiles = [ELFFileReader(filename) for filename in args.filenames]
    features = group_by_feature(elffiles)

    if args.raw:
        for elffile in elffiles:
            print(f'# {elffile.filename}')
            print_json(json.dumps(elffile.notes(), indent=2))

    if features_to_print := filter_features(features, args.features):
        print('# grouped by feature')
        print_json(json.dumps(features_to_print,
                              indent=2,
                              default=lambda prio: prio.name))

    if args.rpm_requires is not None:
        lines = generate_rpm(elffiles, 'Requires', args.rpm_requires)
        print('\n'.join(lines))

    if args.rpm_recommends is not None:
        lines = generate_rpm(elffiles, 'Recommends', args.rpm_recommends)
        print('\n'.join(lines))

    if args.sonames:
        sonames = group_by_soname(elffiles)
        for soname in sorted(sonames.keys()):
            print(f"{soname} {sonames[soname]}")
