#!/usr/bin/perl

use strict;
use warnings;
use Debian::Debhelper::Dh_Lib;

insert_after("dh_shlibdeps", "dh_dlopenlibdeps");
