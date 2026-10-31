# Native decoder smoke build (Linux/macOS) and in-memory ABI test.
# On Windows/MSYS2 use build_windows.sh.
CC ?= cc
CFLAGS ?= -O2 -Wall -Wextra -std=c11

all: libd64resource.so
libd64resource.so: d64resource.c d64resource.h
	$(CC) $(CFLAGS) -fPIC -shared -o $@ d64resource.c -lz
clean:
	rm -f libd64resource.so
