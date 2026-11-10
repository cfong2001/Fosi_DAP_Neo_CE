# Host build + test for the M3U parser/resolver core.
#   make test        - build and run the suite (also under ASan/UBSan)
#   make clean
CC      ?= cc
CFLAGS  ?= -std=c99 -Wall -Wextra -Werror -O1
SRC      = ../src/m3u.c test_m3u.c

test:
	$(CC) $(CFLAGS) -o test_m3u $(SRC)
	./test_m3u
	$(CC) $(CFLAGS) -DHOST_TEST -I../src -o host_bridge_test ../src/m3u.c ../src/m3u_bridge.c host_bridge_test.c
	./host_bridge_test
	$(CC) $(CFLAGS) -ffunction-sections -fdata-sections -Wl,--gc-sections -o test_bridge_names test_bridge_names.c
	./test_bridge_names
	$(CC) $(CFLAGS) -g -fsanitize=address,undefined -o test_m3u_asan $(SRC)
	./test_m3u_asan
	$(CC) $(CFLAGS) -g -fsanitize=address,undefined -ffunction-sections -fdata-sections -Wl,--gc-sections -o test_bridge_names_asan test_bridge_names.c
	./test_bridge_names_asan

clean:
	rm -f test_m3u test_m3u_asan host_bridge_test test_bridge_names test_bridge_names_asan

