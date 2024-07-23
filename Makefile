all:

man: dlopen-notes.1

dlopen-notes.1: dlopen-notes.py docs/dlopen-description.man Makefile
	argparse-manpage 	\
		--output=docs/$@ 	\
		--pyfile=$< 	\
		--function=make_parser \
		--project-name=package-notes \
		--include=docs/dlopen-description.man

install:
	install -m 755 -D dlopen-notes.py $(DESTDIR)/usr/bin/dlopen-notes
	install -m 644 -D docs/dlopen-notes.1 $(DESTDIR)/usr/share/man/man1/dlopen-notes.1

check:
	make -C test check

clean:
	make -C test clean
