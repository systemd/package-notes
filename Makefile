all:

install:
	install -m 755 -D dlopen-notes.py $(DESTDIR)/usr/bin/dlopen-notes

check:
	make -C test check

clean:
	make -C test clean
