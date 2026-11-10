# Host build + test for the M3U parser/resolver core.
#   make test        - build and run the suite (also under ASan/UBSan)
#   make clean
CC      ?= cc
CFLAGS  ?= -std=c99 -Wall -Wextra -Werror -O1
SRC      = ../src/m3u.c test_m3u.c

test:
	$(CC) $(CFLAGS) -o test_m3u $(SRC)
	./test_m3u
	$(CC) $(CFLAGS) -g -fsanitize=address,undefined -o test_m3u_asan $(SRC)
	./test_m3u_asan

clean:
	rm -f test_m3u test_m3u_asan
