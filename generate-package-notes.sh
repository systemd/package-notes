#!/bin/sh
# SPDX-License-Identifier: CC0-1.0

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

    printf "%s/* %s: '%s' */" "$prefix" "$label" "$text"
    for i in $(seq ${#text}); do
        if [ $(( i % 4)) -eq 1 ]; then
            printf '\n%s' "$prefix"
        else
            printf ' '
        fi
        byte=$(echo "${text}" | cut -c "${i}")
        printf 'BYTE(0x%02x)' "'${byte}"
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
    printf "        BYTE(0x46) BYTE(0x44) BYTE(0x4f) BYTE(0x00) /* Owner: 'FDO' */\n"

    write_string "$1" '        ' 'Value' "$value_len"

    printf '    }\n}\n'
    printf 'INSERT AFTER .note.gnu.build-id;\n'
}

# Not supported on every distro
if [ ! -r /usr/lib/system-release-cpe ]; then
    cpe="$(cat /usr/lib/system-release-cpe)"
    json_cpe=",\"osCpe\": \"${cpe}\""
fi

json="$(printf '{"type":"rpm","name":"%s","version":"%s","architecture":"%s"%s}' "$1" "$2" "$3" "$json_cpe")"
write_script "$json"
