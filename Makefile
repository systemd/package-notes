all:

install:
	install -m 755 -D dlopen-notes.py $(DESTDIR)/usr/bin/dlopen-notes
	install -m 644 -D man/dlopen-notes.1 $(DESTDIR)/usr/share/man/man1/dlopen-notes.1

check:
	make -C test check

clean:
	make -C test clean
