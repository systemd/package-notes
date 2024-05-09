/* SPDX-License-Identifier: CC0-1.0 */

#include <stdint.h>

#define XCONCATENATE(x, y) x ## y
#define CONCATENATE(x, y) XCONCATENATE(x, y)
#define UNIQ_T(x, uniq) CONCATENATE(__unique_prefix_, CONCATENATE(x, uniq))
#define UNIQ __COUNTER__

#define ELF_NOTE_DLOPEN_VENDOR "FDO"
#define ELF_NOTE_DLOPEN_TYPE 0x407c0c0a

#define _ELF_NOTE_DLOPEN(module, variable_name)                         \
        __attribute__((used, section(".note.dlopen"))) _Alignas(sizeof(uint32_t)) static const struct { \
                struct {                                                \
                        uint32_t n_namesz, n_descsz, n_type;            \
                } nhdr;                                                 \
                char name[sizeof(ELF_NOTE_DLOPEN_VENDOR)];              \
                _Alignas(sizeof(uint32_t)) char dlopen_module[sizeof(module)]; \
        } variable_name = {                                             \
                .nhdr = {                                               \
                        .n_namesz = sizeof(ELF_NOTE_DLOPEN_VENDOR),     \
                        .n_descsz = sizeof(module),                     \
                        .n_type   = ELF_NOTE_DLOPEN_TYPE,               \
                },                                                      \
                .name = ELF_NOTE_DLOPEN_VENDOR,                         \
                .dlopen_module = module,                                \
        }

#define _SONAME_ARRAY1(a) "[\""a"\"]"
#define _SONAME_ARRAY2(a, b) "[\""a"\",\""b"\"]"
#define _SONAME_ARRAY3(a, b, c) "[\""a"\",\""b"\",\""c"\"]"
#define _SONAME_ARRAY4(a, b, c, d) "[\""a"\",\""b"\",\""c"\"",\""d"\"]"
#define _SONAME_ARRAY5(a, b, c, d, e) "[\""a"\",\""b"\",\""c"\"",\""d"\",\""e"\"]"
#define _SONAME_ARRAY_GET(_1,_2,_3,_4,_5,NAME,...) NAME
#define _SONAME_ARRAY(...) _SONAME_ARRAY_GET(__VA_ARGS__, _SONAME_ARRAY5, _SONAME_ARRAY4, _SONAME_ARRAY3, _SONAME_ARRAY2, _SONAME_ARRAY1)(__VA_ARGS__)

#define ELF_NOTE_DLOPEN(feature, description, priority, ...) \
        _ELF_NOTE_DLOPEN("[{\"feature\":\"" feature "\",\"description\":\"" description "\",\"priority\":\"" priority "\",\"soname\":" _SONAME_ARRAY(__VA_ARGS__) "}]", UNIQ_T(s, UNIQ))

#define ELF_NOTE_DLOPEN_DUAL(feature0, priority0, module0, feature1, priority1, module1) \
        _ELF_NOTE_DLOPEN("[{\"feature\":\"" feature0 "\",\"priority\":\"" priority0 "\",\"soname\":[\"" module0 "\"]}, {\"feature\":\"" feature1 "\",\"priority\":\"" priority1 "\",\"soname\":[\"" module1 "\"]}]", UNIQ_T(s, UNIQ))

int main(int argc, char **argv) {
        ELF_NOTE_DLOPEN("fido2", "Support fido2 for encryption and authentication.", "required", "libfido2.so.1");
        ELF_NOTE_DLOPEN("pcre2", "Support pcre2 for regex", "suggested", "libpcre2-8.so.0","libpcre2-8.so.1");
        ELF_NOTE_DLOPEN("lz4", "Support lz4 decompression in journal and coredump files", "recommended", "liblz4.so.1");
        ELF_NOTE_DLOPEN_DUAL("tpm", "recommended", "libtss2-mu.so.0", "tpm", "recommended", "libtss2-esys.so.0");
        return 0;
}
