# SPDX-License-Identifier: CC0-1.0
# Include from debian/rules to use with dh_package_notes.
# See dh_package_notes(1) for details
export DEB_LDFLAGS_MAINT_APPEND+= -Wl,-dT,$(CURDIR)/debian/.debhelper/notes.ld
