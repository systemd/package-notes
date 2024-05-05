notes: notes.c
	$(CC) -o $@ $+ $(CFLAGS) $(LDFLAGS) $(LDLIBS)

check: notes
	python3 -m pytest test.py

clean:
	rm -f notes
	rm -rf __pycache__/
