# SPDX-License-Identifier: MIT-0
#
# This file is part of the package-notes package.

Name:           fakelib
Version:        0
Release:        %autorelease
Summary:        %{name}

License:        None

%define __dlopen_notes_requires_opts   --rpm-features=fakelib:gcrypt,fakelib:lz4
%define __dlopen_notes_recommends_opts --rpm-features=*:zstd
%define __dlopen_notes_suggests_opts   --rpm-features=fakelib:lzm[abc]

#undefine _dlopen_notes_generator

%description
%{summary}.

%prep

%build

%install
install -Dt %{buildroot}/usr/lib64/ /usr/lib64/libsystemd.so.0
ln -s libsystemd.so.0 %{buildroot}/usr/lib64/libsystemd.so
install -Dt %{buildroot}/usr/lib64/ /usr/lib64/libmvec.so.1

%files
/usr/lib64/libsystemd.so.0
/usr/lib64/libsystemd.so
/usr/lib64/libmvec.so.1

%changelog
%autochangelog
