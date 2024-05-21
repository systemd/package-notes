#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0

"""\
Read .note.dlopen notes from ELF files and report the contents.
"""

import argparse
import enum
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

def listify(f):
    def wrap(*args, **kwargs):
        return list(f(*args, **kwargs))
    return functools.update_wrapper(wrap, f)

@listify
def read_dlopen_notes(filename):
    elffile = ELFFile(open(filename, 'rb'))

    for section in elffile.iter_sections():
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
                raise ValueError(f'{filename}: Invalid UTF-8 in .note.dlopen n_desc') from e

            try:
                j = json.loads(text)
            except json.JSONDecodeError as e:
                raise ValueError(f'{filename}: Invalid JSON in .note.dlopen note_desc') from e

            if not isinstance(j, list):
                print(f'{filename}: ignoring .note.dlopen n_desc with JSON that is not a list',
                      file=sys.stderr)
                continue

            yield from j

def dictify(f):
    def wrap(*args, **kwargs):
        return dict(f(*args, **kwargs))
    return functools.update_wrapper(wrap, f)

@dictify
def group_by_soname(notes):
    for note in notes:
        for element in note:
            priority = element.get('priority', 'recommended')
            for soname in element['soname']:
                yield soname, priority

class Priority(enum.Enum):
    suggested   = 1
    recommended = 2
    required    = 3

    def __lt__(self, other):
        return self.value < other.value

def group_by_feature(filenames, notes):
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
    for filename, note_group in zip(filenames, notes):
        for note in note_group:
            prio = Priority[note.get('priority', 'recommened')]
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
                    print(f"{filename}: feature {note['feature']!r} found with different description, ignoring",
                          file=sys.stderr)

                for soname in note['soname']:
                    highest = max(feature['sonames'].get(soname, Priority.suggested),
                                  prio)
                    feature['sonames'][soname] = highest

    return features

def make_parser():
    p = argparse.ArgumentParser(
        description=__doc__,
        allow_abbrev=False,
        add_help=False,
        epilog='If no option is specifed, --raw is the default.',
    )
    p.add_argument('-r', '--raw',
                   action='store_true',
                   help='Show the original JSON extracted from input files')
    p.add_argument('-s', '--sonames',
                   action='store_true',
                   help='List all sonames and their priorities, one soname per line')
    p.add_argument('-f', '--features',
                   nargs='?',
                   const=[],
                   type=lambda s: s.split(','),
                   action='extend',
                   metavar='FEATURE1,FEATURE2',
                   help='Describe features, can be specified multiple times')
    p.add_argument('filenames',
                   nargs='+',
                   metavar='filename',
                   help='Library file to extract notes from')
    p.add_argument('-h', '--help',
                   action='help',
                   help='Show this help message and exit')
    return p

def parse_args():
    args = make_parser().parse_args()

    if not args.raw and args.features is None and not args.sonames:
        # Make --raw the default if no action is specified.
        args.raw = True

    return args

if __name__ == '__main__':
    args = parse_args()

    notes = [read_dlopen_notes(filename) for filename in args.filenames]

    if args.raw:
        for filename, note in zip(args.filenames, notes):
            print(f'# {filename}')
            print_json(json.dumps(note, indent=2))

    if args.features is not None:
        features = group_by_feature(args.filenames, notes)

        toprint = {name:feature for name,feature in features.items()
                   if name in args.features or not args.features}
        if len(toprint) < len(args.features):
            sys.exit('Some features were not found')

        print('# grouped by feature')
        print_json(json.dumps(toprint,
                              indent=2,
                              default=lambda prio: prio.name))

    if args.sonames:
        sonames = group_by_soname(notes)
        for soname in sorted(sonames.keys()):
            print(f"{soname} {sonames[soname]}")
