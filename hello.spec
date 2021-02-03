%bcond_without notes

Name:		hello
Version:	0
Release:	1%{?dist}%{!?with_notes:.nonotes}
Summary:	Aloha!

License:	CC-0

BuildRequires:	gcc

Source0:        brp-insert-version-note

%if %{with notes}
%global __brp_insert_version_note %{SOURCE0} '%{name}-%{VERSION}-%{RELEASE}.%{_arch}'

%global __os_install_post \
  %__os_install_post \
  %__brp_insert_version_note \
  %nil
%endif

%description
Test with:
objdump -s -j .package.version %{_bindir}/hello
objdump -s -j .package.version %{_libdir}/libhello.so

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

%build
cd build
gcc -Wall -fPIC -o libhello.so -shared libhello.c
gcc -Wall -o hello hello.c libhello.so

%install
cd build

install -Dt %{buildroot}%{_libdir}/ libhello.so
install -Dt %{buildroot}%{_bindir}/ hello

%files
%{_bindir}/hello
%{_libdir}/libhello.so

%changelog
* Wed Feb  3 2021 Zbigniew Jędrzejewski-Szmek <zbyszek@in.waw.pl> - 0-1
- Test
