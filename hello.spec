# SPDX-License-Identifier: CC0-1.0

%bcond_without notes

Name:           hello
Version:        0
Release:        1%{?dist}%{!?with_notes:.nonotes}
Summary:        Aloha!

License:        CC0

BuildRequires:  binutils
BuildRequires:  gcc
BuildRequires:  rpmdevtools
BuildRequires:  python3
BuildRequires:  python3-simplejson

Source0:        generate-package-notes.py

%description
Test with:
objdump -s -j .note.package %{_bindir}/hello
objdump -s -j .note.package %{_libdir}/libhello.so

%prep
%setup -cT
set -eo pipefail

cat <<EOF >libhello.c
const char* greeting(void) {
    return "Hello";
}
EOF
cat <<EOF >hello.c
#include <stdio.h>
extern char* greeting(void);
int main() {
    puts(greeting());
    return 0;
}
EOF

%build
set -eo pipefail

ld_version="$(ld --version | sed -r -n '1 {s/.*version (.*)/\1/p}')"
set +e
rpmdev-vercmp "$ld_version" "2.38" >/dev/null
if [ $? == 12 ]; then
  readonly="--readonly=no"
fi
set -e

%if %{with notes}
python3 %{SOURCE0} $readonly --rpm '%{name}-%{VERSION}-%{RELEASE}.%{_arch}' | \
        tee notes.ld
%endif

LDFLAGS="%{build_ldflags} %{?with_notes:-Wl,-dT,$PWD/notes.ld}"
CFLAGS="%{build_cflags}"

gcc -Wall -fPIC -o libhello.so -shared libhello.c $CFLAGS $LDFLAGS
gcc -Wall -o hello hello.c libhello.so $CFLAGS $LDFLAGS

%install
set -eo pipefail

install -Dt %{buildroot}%{_libdir}/ libhello.so
install -Dt %{buildroot}%{_bindir}/ hello

%check
set -eo pipefail

%if %{with notes}
objdump -s -j .note.package ./hello
objdump -s -j .note.package ./libhello.so
%endif

%files
%{_bindir}/hello
%{_libdir}/libhello.so

%changelog
* Wed Feb  3 2021 Zbigniew Jędrzejewski-Szmek <zbyszek@in.waw.pl> - 0-1
- Test
