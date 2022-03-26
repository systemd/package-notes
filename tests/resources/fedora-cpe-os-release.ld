SECTIONS
{
    .note.package (READONLY) : ALIGN(4) {
        LONG(0x0004)                                /* Length of Owner including NUL */
        LONG(0x0038)                                /* Length of Value including NUL */
        LONG(0xcafe1a7e)                            /* Note ID */
        BYTE(0x46) BYTE(0x44) BYTE(0x4f) BYTE(0x00) /* Owner: 'FDO\x00' */
        BYTE(0x7b) BYTE(0x22) BYTE(0x74) BYTE(0x79) /* Value: '{"type":"rpm","osCpe":"cpe:/o:fedoraproject:fedora:34"}\x00' */
        BYTE(0x70) BYTE(0x65) BYTE(0x22) BYTE(0x3a)
        BYTE(0x22) BYTE(0x72) BYTE(0x70) BYTE(0x6d)
        BYTE(0x22) BYTE(0x2c) BYTE(0x22) BYTE(0x6f)
        BYTE(0x73) BYTE(0x43) BYTE(0x70) BYTE(0x65)
        BYTE(0x22) BYTE(0x3a) BYTE(0x22) BYTE(0x63)
        BYTE(0x70) BYTE(0x65) BYTE(0x3a) BYTE(0x2f)
        BYTE(0x6f) BYTE(0x3a) BYTE(0x66) BYTE(0x65)
        BYTE(0x64) BYTE(0x6f) BYTE(0x72) BYTE(0x61)
        BYTE(0x70) BYTE(0x72) BYTE(0x6f) BYTE(0x6a)
        BYTE(0x65) BYTE(0x63) BYTE(0x74) BYTE(0x3a)
        BYTE(0x66) BYTE(0x65) BYTE(0x64) BYTE(0x6f)
        BYTE(0x72) BYTE(0x61) BYTE(0x3a) BYTE(0x33)
        BYTE(0x34) BYTE(0x22) BYTE(0x7d) BYTE(0x00)
    }
}
INSERT AFTER .note.gnu.build-id;
/* HINT: add -Wl,-dT,/path/to/this/file to $LDFLAGS */
