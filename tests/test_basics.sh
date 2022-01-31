#!/bin/bash
# SPDX-License-Identifier: CC0-1.0

set -e

testdir="$(dirname "$(realpath "${0}")")"

diff <("${testdir}/../generate-package-notes.sh" --type rpm --name package --version 1.2.3 --architecture noarch --osCpe CPE) "${testdir}/resources/fedora-package.ld"
diff <("${testdir}/../generate-package-notes.sh" --type deb --name A --package-version 0 --architecture x --cpe o) "${testdir}/resources/very-short.ld"
diff <("${testdir}/../generate-package-notes.sh" --type deb --name A --version 0 --architecture x --osCpe o --readonly false) "${testdir}/resources/very-short-rw.ld"
diff <("${testdir}/../generate-package-notes.sh" --type rpm --name rust-plist+enable_unstable_features_that_may_break_with_minor_version_bumps-devel --version 200:1.3.1~rc1.post2^final3 --architecture ppc64le --osCpe cpe:/o:fedoraproject:fedora:35 --debugInfoUrl https://somewhere.on.the.internet.there.is.a.server.which.is.never.wrong/query) "${testdir}/resources/fedora-long-name.ld"
diff <("${testdir}/../generate-package-notes.sh" --type rpm --cpe auto --root "${testdir}/resources/root-no-cpe/") "${testdir}/resources/fedora-cpe-os-release.ld"
diff <("${testdir}/../generate-package-notes.sh" --type rpm --cpe auto --root "${testdir}/resources/root/") "${testdir}/resources/fedora-cpe-system-release.ld"
