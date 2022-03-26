#!/bin/sh
# SPDX-License-Identifier: CC0-1.0
#
# Generates a linker script to insert a .note.package section with a
# JSON payload. The contents are derived from the specified options and the
# os-release file. Use the output with -Wl,-dT,/path/to/output in $LDFLAGS.
#
# $ ./generate-package-notes.sh --type rpm --name systemd --version 248~rc2-1.fc34 --architecture x86_64 --osCpe 'cpe:/o:fedoraproject:fedora:33'
# SECTIONS
# {
#     .note.package (READONLY) : ALIGN(4) {
#         BYTE(0x04) BYTE(0x00) BYTE(0x00) BYTE(0x00) /* Length of Owner including NUL */
#         BYTE(0x7c) BYTE(0x00) BYTE(0x00) BYTE(0x00) /* Length of Value including NUL */
#         BYTE(0x7e) BYTE(0x1a) BYTE(0xfe) BYTE(0xca) /* Note ID */
#         BYTE(0x46) BYTE(0x44) BYTE(0x4f) BYTE(0x00) /* Owner: 'FDO\x00' */
#         BYTE(0x7b) BYTE(0x22) BYTE(0x74) BYTE(0x79) /* Value: '{"type":"rpm","name":"systemd","version":"248~rc2-1.fc34","architecture":"x86_64","osCpe":"cpe:/o:fedoraproject:fedora:33"}\x00' */
#         BYTE(0x70) BYTE(0x65) BYTE(0x22) BYTE(0x3a)
#         BYTE(0x22) BYTE(0x72) BYTE(0x70) BYTE(0x6d)
#         BYTE(0x22) BYTE(0x2c) BYTE(0x22) BYTE(0x6e)
#         BYTE(0x61) BYTE(0x6d) BYTE(0x65) BYTE(0x22)
#         BYTE(0x3a) BYTE(0x22) BYTE(0x73) BYTE(0x79)
#         BYTE(0x73) BYTE(0x74) BYTE(0x65) BYTE(0x6d)
#         BYTE(0x64) BYTE(0x22) BYTE(0x2c) BYTE(0x22)
#         BYTE(0x76) BYTE(0x65) BYTE(0x72) BYTE(0x73)
#         BYTE(0x69) BYTE(0x6f) BYTE(0x6e) BYTE(0x22)
#         BYTE(0x3a) BYTE(0x22) BYTE(0x32) BYTE(0x34)
#         BYTE(0x38) BYTE(0x7e) BYTE(0x72) BYTE(0x63)
#         BYTE(0x32) BYTE(0x2d) BYTE(0x31) BYTE(0x2e)
#         BYTE(0x66) BYTE(0x63) BYTE(0x33) BYTE(0x34)
#         BYTE(0x22) BYTE(0x2c) BYTE(0x22) BYTE(0x61)
#         BYTE(0x72) BYTE(0x63) BYTE(0x68) BYTE(0x69)
#         BYTE(0x74) BYTE(0x65) BYTE(0x63) BYTE(0x74)
#         BYTE(0x75) BYTE(0x72) BYTE(0x65) BYTE(0x22)
#         BYTE(0x3a) BYTE(0x22) BYTE(0x78) BYTE(0x38)
#         BYTE(0x36) BYTE(0x5f) BYTE(0x36) BYTE(0x34)
#         BYTE(0x22) BYTE(0x2c) BYTE(0x22) BYTE(0x6f)
#         BYTE(0x73) BYTE(0x43) BYTE(0x70) BYTE(0x65)
#         BYTE(0x22) BYTE(0x3a) BYTE(0x22) BYTE(0x63)
#         BYTE(0x70) BYTE(0x65) BYTE(0x3a) BYTE(0x2f)
#         BYTE(0x6f) BYTE(0x3a) BYTE(0x66) BYTE(0x65)
#         BYTE(0x64) BYTE(0x6f) BYTE(0x72) BYTE(0x61)
#         BYTE(0x70) BYTE(0x72) BYTE(0x6f) BYTE(0x6a)
#         BYTE(0x65) BYTE(0x63) BYTE(0x74) BYTE(0x3a)
#         BYTE(0x66) BYTE(0x65) BYTE(0x64) BYTE(0x6f)
#         BYTE(0x72) BYTE(0x61) BYTE(0x3a) BYTE(0x33)
#         BYTE(0x33) BYTE(0x22) BYTE(0x7d) BYTE(0x00)
#     }
# }
# INSERT AFTER .note.gnu.build-id;
# /* HINT: add -Wl,-dT,/path/to/this/file to $LDFLAGS */
#
# See https://systemd.io/COREDUMP_PACKAGE_METADATA/ for details.


json=
readonly="(READONLY) "
root=

help() {
    echo "Usage: $0 [OPTION]..."
    echo "Generate a package notes linker script from specified metadata."
    echo
    echo "  -h, --help                      display this help and exit"
    echo "      --readonly BOOL             whether to add the READONLY attribute to script (default: true)"
    echo "      --root PATH                 when a file (eg: os-release) is parsed, open it relatively to this hierarchy (default: not set)"
    echo "      --cpe VALUE                 NIST CPE identifier of the vendor operating system, or 'auto' to parse from system-release-cpe or os-release"
    echo "      --package-type TYPE         set the package type (e.g. 'rpm' or 'deb')"
    echo "      --package-name NAME         set the package name"
    echo "      --package-version VERSION   set the package version"
    echo "      --package-architecture ARCH set the package architecture"
    echo "      --NAME VALUE                set an arbitrary name/value pair"
}

invalid_argument() {
    printf 'ERROR: "%s" requires a non-empty option argument.\n' "${1}" >&2
    exit 1
}

append_parameter() {
    if [ -z "${2}" ]; then
        invalid_argument "${1}"
    fi

    # Posix-compatible substring check
    case "$json" in
        *"\"${1}\":"*) echo "Duplicated argument: --${1}"; exit 1 ;;
    esac

    if [ -z "${json}" ]; then
        json="{\"${1}\":\"${2}\""
    else
        json="${json},\"${1}\":\"${2}\""
    fi
}

# Support the same fixed parameters as the python script
parse_options() {
    cpe=

    while :; do
        case $1 in
            -h|-\?|--help)
                help
                exit
                ;;
            --readonly)
                if [ -z "${2}" ]; then
                    invalid_argument "${1}"
                fi
                case $2 in
                    no|NO|No|false|FALSE|False|0)
                        readonly=""
                        ;;
                esac
                shift
                ;;
            --root)
                if [ -z "${2}" ] || [ ! -d "${2}" ]; then
                    invalid_argument "${1}"
                fi
                root="${2}"
                shift
                ;;
            --package-type)
                append_parameter "type" "${2}"
                shift
                ;;
            --package-name)
                append_parameter "name" "${2}"
                shift
                ;;
            --package-version)
                append_parameter "version" "${2}"
                shift
                ;;
            --package-architecture)
                append_parameter "architecture" "${2}"
                shift
                ;;
            --cpe)
                if [ -z "${2}" ]; then
                    invalid_argument "${1}"
                fi
                cpe="${2}"
                shift
                ;;
            --debug-info-url)
                append_parameter "debugInfoUrl" "${2}"
                shift
                ;;
            --*)
                # Allow passing arbitrary name/value pairs
                append_parameter "$(echo "${1}" | cut -c 3-)" "${2}"
                shift
                ;;
            -*)
                printf 'WARNING: Unknown option (ignored): %s\n' "${1}" >&2
                ;;
            *)
                break
        esac

        shift
    done

    # Parse at the end, so that --root can be used in any position
    if [ "${cpe}" = "auto" ]; then
        if [ -r "${root}/usr/lib/system-release-cpe" ]; then
            cpe="$(cat "${root}/usr/lib/system-release-cpe")"
        elif [ -r "${root}/etc/os-release" ]; then
            # shellcheck disable=SC1090 disable=SC1091
            cpe="$(. "${root}/etc/os-release" && echo "${CPE_NAME}")"
        elif [ -r "${root}/usr/lib/os-release" ]; then
            # shellcheck disable=SC1090 disable=SC1091
            cpe="$(. "${root}/usr/lib/os-release" && echo "${CPE_NAME}")"
        fi
        if [ -z "${cpe}" ]; then
            printf 'ERROR: --cpe auto but cannot read %s/usr/lib/system-release-cpe or parse CPE_NAME from %s/etc/os-release or %s/usr/lib/os-release.\n' "${root}" "${root}" "${root}" >&2
            exit 1
        fi
    fi
    if [ -n "${cpe}" ]; then
        append_parameter "osCpe" "${cpe}"
    fi

    # Terminate the JSON object
    if [ -n "${json}" ]; then
        json="${json}}"
    fi

    return "$#"
}

pad_comment() {
    for _ in $(seq "$1"); do
        printf '\\x00'
    done
}

pad_string() {
    for i in $(seq "$1"); do
        if [ $(( ( $2 + i - 1) % 4 )) -eq 0 ]; then
            printf '\n%sBYTE(0x00)' "${3}"
        else
            printf ' BYTE(0x00)'
        fi
    done
}

write_string() {
    text="$1"
    prefix="$2"
    label="$3"
    total="$4"

    # We always have at least the terminating NULL
    if [ $(( total % 4)) -eq 0 ]; then
        padding_nulls=1
    else
        padding_nulls="$(( 1 + 4 - (total % 4) ))"
    fi

    for i in $(seq ${#text}); do
        if [ $(( i % 4)) -eq 1 ]; then
            printf '\n%s' "$prefix"
        else
            printf ' '
        fi
        byte=$(echo "${text}" | cut -c "${i}")
        printf 'BYTE(0x%02x)' "'${byte}"

        # Print the json object as a comment after the first 4 bytes
        # to match the output of the older script, including padding NUL.
        if [ "${i}" -eq 4 ]; then
            printf " /* %s: '%s" "$label" "$text"
            pad_comment "${padding_nulls}"
            printf "' */"
        fi
    done

    pad_string "${padding_nulls}" "${#text}" "$prefix"
    printf '\n'
}

write_script() {
    # NULL terminator is included in the size, but not padding
    value_len=$(( ${#1} + 1 ))

    if [ "${value_len}" -gt 65536 ]; then
        printf 'ERROR: "%s" is too long.\n' "${1}" >&2
        exit 1
    fi

    printf 'SECTIONS\n{\n'
    printf '    .note.package %s: ALIGN(4) {\n' "${readonly}"
    # Note that for the binary fields we use the native 4 bytes type, to avoid
    # endianness issues.
    printf '        LONG(0x0004)                                /* Length of Owner including NUL */\n'
    printf '        LONG(0x%04x)                                /* Length of Value including NUL */\n' \
        ${value_len}
    printf '        LONG(0xcafe1a7e)                            /* Note ID */\n'

    printf "        BYTE(0x46) BYTE(0x44) BYTE(0x4f) BYTE(0x00) /* Owner: 'FDO\\\\x00' */" # newline will be added by write_string

    write_string "$1" '        ' 'Value' "$value_len"

    printf '    }\n}\n'
    printf 'INSERT AFTER .note.gnu.build-id;\n'
    # shellcheck disable=SC2016
    printf '/* HINT: add -Wl,-dT,/path/to/this/file to $LDFLAGS */\n'
}

if ! parse_options "$@" && [ "$#" -gt 0 ]; then
    # Not supported on every distro
    if [ -r "${root}/usr/lib/system-release-cpe" ]; then
        cpe="$(cat "${root}/usr/lib/system-release-cpe")"
        json_cpe=",\"osCpe\":\"${cpe}\""
    fi

    # old-style invocation with positional parameters for backward compatibility
    json="$(printf '{"type":"rpm","name":"%s","version":"%s","architecture":"%s"%s}' "$1" "$2" "$3" "$json_cpe")"
elif [ -z "${json}" ]; then
    help
    exit 1
fi

write_script "$json"
