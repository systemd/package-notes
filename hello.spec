%bcond_without notes

Name:           hello
Version:        0
Release:        1%{?dist}%{!?with_notes:.nonotes}
Summary:        Aloha!

License:        CC0

BuildRequires:  binutils
BuildRequires:  gcc
BuildRequires:  python3

Source0:        generate-package-notes.py

%description
Test with:
objdump -s -j .note.package %{_bindir}/hello
objdump -s -j .note.package %{_libdir}/libhello.so

%prep
rm -rf build && mkdir build && cd build

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

%if %{with notes}
python3 %{SOURCE0} --rpm '%{name}-%{VERSION}-%{RELEASE}.%{_arch}' | \
        tee notes.ld
%endif

%build
cd build

LDFLAGS="%{build_ldflags} %{?with_notes:-Wl,-T,$PWD/notes.ld}"
CFLAGS="%{build_cflags}"

gcc -Wall -fPIC -o libhello.so -shared libhello.c $CFLAGS $LDFLAGS
gcc -Wall -o hello hello.c libhello.so $CFLAGS $LDFLAGS

%install
cd build

install -Dt %{buildroot}%{_libdir}/ libhello.so
install -Dt %{buildroot}%{_bindir}/ hello

%check
cd build

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
