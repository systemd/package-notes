#!/bin/sh
# SPDX-License-Identifier: CC0-1.0

json=

help() {
    echo "Usage: $0 [OPTION]..."
    echo "Generate a package notes linker script from specified metadata."
    echo
    echo "  -h, --help                      display this help and exit"
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
    while :; do
        case $1 in
            -h|-\?|--help)
                help
                exit
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
                append_parameter "osCpe" "${2}"
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

    # Terminate the JSON object
    if [ -n "${json}" ]; then
        json="${json}}"
    fi

    return "$#"
}

pad_comment() {
    for _ in $(seq "$1"); do
        printf '\x00'
    done
}

pad_string() {
    for _ in $(seq "$1"); do
        printf ' BYTE(0x00)'
    done
}

write_string() {
    text="$1"
    prefix="$2"
    label="$3"
    total="$4"

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
            pad_comment $(( total - ${#text} ))
            printf "' */"
        fi
    done

    pad_string $(( total - ${#text} ))
    printf '\n'
}

write_script() {
    value_len=$(( (${#1} + 3) / 4 * 4 ))

    printf 'SECTIONS\n{\n'
    printf '    .note.package (READONLY) : ALIGN(4) {\n'
    printf '        BYTE(0x04) BYTE(0x00) BYTE(0x00) BYTE(0x00) /* Length of Owner including NUL */\n'
    printf '        BYTE(0x%02x) BYTE(0x%02x) BYTE(0x00) BYTE(0x00) /* Length of Value including NUL */\n' \
           $((value_len % 256)) $((value_len / 256))

    printf '        BYTE(0x7e) BYTE(0x1a) BYTE(0xfe) BYTE(0xca) /* Note ID */\n'
    printf "        BYTE(0x46) BYTE(0x44) BYTE(0x4f) BYTE(0x00) /* Owner: 'FDO\x00' */" # newline will be added by write_string

    write_string "$1" '        ' 'Value' "$value_len"

    printf '    }\n}\n'
    printf 'INSERT AFTER .note.gnu.build-id;\n'
    # shellcheck disable=SC2016
    printf '/* HINT: add -Wl,-dT,/path/to/this/file to $LDFLAGS */\n'
}

if ! parse_options "$@" && [ "$#" -gt 0 ]; then
    # Not supported on every distro
    if [ -r /usr/lib/system-release-cpe ]; then
        cpe="$(cat /usr/lib/system-release-cpe)"
        json_cpe=",\"osCpe\":\"${cpe}\""
    fi

    # old-style invocation with positional parameters for backward compatibility
    json="$(printf '{"type":"rpm","name":"%s","version":"%s","architecture":"%s"%s}' "$1" "$2" "$3" "$json_cpe")"
elif [ -z "${json}" ]; then
    help
    exit 1
fi

write_script "$json"
