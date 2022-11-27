# SPDX-License-Identifier: CC0-1.0
# Include from debian/rules to use with dh_package_notes.
# See dh_package_notes(1) for details
include /usr/share/dpkg/vendor.mk
ifeq (, $(filter nocheck, $(DEBUGINFOD_URLS)))
ifeq ($(DEB_VENDOR),Ubuntu)
export DEBUGINFOD_URLS=https://debuginfod.ubuntu.com
else
export DEBUGINFOD_URLS=https://debuginfod.debian.net
endif
endif
export DEB_SOURCE_PACKAGE_VERSION=$(shell dpkg-parsechangelog -S Version)
export DEB_SOURCE_PACKAGE_NAME=$(shell dpkg-parsechangelog -S Source)
export DEB_LDFLAGS_MAINT_APPEND+= -specs=/usr/share/debhelper/dh_package_notes/debian-package-notes.specs
export DEB_VENDOR

