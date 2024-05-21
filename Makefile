all:

dlopen-notes.1: dlopen-notes.py docs/dlopen-description.man Makefile
	argparse-manpage 	\
		--output=$@ 	\
		--pyfile=$< 	\
		--function=make_parser \
		--project-name=package-notes \
		--include=docs/dlopen-description.man

install:
	install -m 755 -D dlopen-notes.py $(DESTDIR)/usr/bin/dlopen-notes

check:
	make -C test check

clean:
	make -C test clean
