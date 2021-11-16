#!/usr/bin/perl
# SPDX-License-Identifier: CC0-1.0

use warnings;
use strict;
use Debian::Debhelper::Dh_Lib;

insert_before('dh_auto_configure', 'dh_package_notes');

1
