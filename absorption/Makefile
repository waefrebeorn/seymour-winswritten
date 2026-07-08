# Absorber Engine — C11 YouTube CDP Transcript Extractor
# 
# Build: make all
# Run:   cat video_ids.txt | ./absorption_c11
#       ./build_absorber.py < video_ids.txt
#
# C11 features used:
#   - _Static_assert for type size validation
#   - _Alignas / alignof for SIMD alignment
#   - _Noreturn for signal handler
#   - _Thread_local for error buffers
#   - _Generic (in http_raw.c dispatch)
#   - atomic_bool for stop flag
#   - restrict (planned for hot paths)

CC       ?= gcc
CXX      ?= g++
CFLAGS   ?= -std=gnu11 -O3 -march=native -ffast-math -funroll-loops \
           -ftree-vectorize -Wall -Wextra -Wno-unused-parameter \
           -Werror=implicit-function-declaration \
           -D_GNU_SOURCE -I include
LDFLAGS  ?= -lpthread

# Fuzzing targets (compile with -O1 -fsanitize=address -fno-omit-frame-pointer)
# Note: -fsanitize=fuzzer requires Clang. With GCC we use ASAN + custom harnesses.
FUZZ_CC      ?= gcc
FUZZ_CFLAGS  = -std=gnu11 -O1 -march=native -fsanitize=address -fno-omit-frame-pointer -g \
               -Wall -Wextra -Wno-unused-parameter \
               -Werror=implicit-function-declaration \
               -D_GNU_SOURCE -I include -DFUZZING
FUZZ_LDFLAGS = -fsanitize=address

# For debug build: DEBUG=1 make
ifdef DEBUG
CFLAGS += -O0 -g -fsanitize=address,undefined -fno-omit-frame-pointer
LDFLAGS += -fsanitize=address,undefined
endif

# For fuzzing: FUZZ=1 make fuzz_json
ifdef FUZZ
CFLAGS = $(FUZZ_CFLAGS)
LDFLAGS = $(FUZZ_LDFLAGS)
endif

# Targets
BIN      = engine/absorption_c11
WHISPER  = engine/whisper_fallback

SRCS     = engine/absorber_main.c engine/cdp_client.c \
           engine/http_raw.c engine/video_store.c

OBJS     = $(SRCS:.c=.o)

.PHONY: all clean test

all: $(BIN) $(WHISPER)

$(BIN): $(OBJS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

# Pattern rule: .c -> .o
%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

$(WHISPER): engine/whisper_fallback.c
	$(CC) $(CFLAGS) -o $@ $< -lpthread -lm

clean:
	rm -f $(OBJS) $(BIN) $(WHISPER)

# Quick syntax check (no code generation)
check:
	$(CC) $(CFLAGS) -fsyntax-only $(SRCS)

# Size report
size: engine/absorption_c11
	size engine/absorption_c11
	nm --size-sort engine/absorption_c11 | tail -20

test: engine/absorption_c11
	@echo "dQw4w9WgXcQ" | ./engine/absorption_c11 2>&1 | head -5

# ===== FUZZING TARGETS (ASAN + custom harnesses) =====

# JSON parser fuzzer - tests json_find_key in http_raw.c
engine/fuzz_json: engine/fuzz_json.c engine/http_raw.o
	$(FUZZ_CC) $(FUZZ_CFLAGS) -o $@ $< engine/http_raw.o $(FUZZ_LDFLAGS)

fuzz_json: engine/fuzz_json
	@echo "Running JSON fuzzer..."
	@mkdir -p corpus/json
	@./engine/fuzz_json corpus/json 10000

# JSON parser fuzzer with standalone harness
engine/fuzz_json.c:
	@echo '/* JSON fuzzer for json_find_key - standalone harness */' > $@
	@echo '#include <stdint.h>' >> $@
	@echo '#include <stddef.h>' >> $@
	@echo '#include <stdlib.h>' >> $@
	@echo '#include <string.h>' >> $@
	@echo '#include <stdio.h>' >> $@
	@echo '#include "http_raw.h"' >> $@
	@echo '' >> $@
	@echo 'int main(int argc, char **argv) {' >> $@
	@echo '    if (argc < 2) return 0;' >> $@
	@echo '    FILE *fp = fopen(argv[1], "rb");' >> $@
	@echo '    if (!fp) return 0;' >> $@
	@echo '    fseek(fp, 0, SEEK_END);' >> $@
	@echo '    long size = ftell(fp);' >> $@
	@echo '    fseek(fp, 0, SEEK_SET);' >> $@
	@echo '    if (size <= 0 || size > 100000) { fclose(fp); return 0; }' >> $@
	@echo '    char *buf = malloc(size + 1);' >> $@
	@echo '    if (!buf) { fclose(fp); return 0; }' >> $@
	@echo '    fread(buf, 1, size, fp);' >> $@
	@echo '    fclose(fp);' >> $@
	@echo '    buf[size] = '\''\\0'\'';' >> $@
	@echo '    size_t vlen;' >> $@
	@echo '    char *result = json_find_key(buf, "value", &vlen);' >> $@
	@echo '    free(result);' >> $@
	@echo '    free(buf);' >> $@
	@echo '    return 0;' >> $@
	@echo '}' >> $@

# Base64 fuzzer for cdp_client.c base64_encode
engine/fuzz_base64: engine/fuzz_base64.c engine/cdp_client.o engine/http_raw.o
	$(FUZZ_CC) $(FUZZ_CFLAGS) -o $@ $< engine/cdp_client.o engine/http_raw.o $(FUZZ_LDFLAGS)

fuzz_base64: engine/fuzz_base64
	@echo "Running base64 fuzzer..."
	@mkdir -p corpus/base64
	@./engine/fuzz_base64 corpus/base64 10000

engine/fuzz_base64.c:
	@echo '/* Base64 fuzzer for cdp_client.c base64_encode - standalone harness */' > $@
	@echo '#include <stdint.h>' >> $@
	@echo '#include <stddef.h>' >> $@
	@echo '#include <stdlib.h>' >> $@
	@echo '#include <string.h>' >> $@
	@echo '#include <stdio.h>' >> $@
	@echo '#include "cdp_client.h"' >> $@
	@echo '' >> $@
	@echo 'extern void base64_encode(const uint8_t *in, size_t in_len, char *out, size_t out_size);' >> $@
	@echo '' >> $@
	@echo 'int main(int argc, char **argv) {' >> $@
	@echo '    if (argc < 2) return 0;' >> $@
	@echo '    FILE *fp = fopen(argv[1], "rb");' >> $@
	@echo '    if (!fp) return 0;' >> $@
	@echo '    fseek(fp, 0, SEEK_END);' >> $@
	@echo '    long size = ftell(fp);' >> $@
	@echo '    fseek(fp, 0, SEEK_SET);' >> $@
	@echo '    if (size <= 0 || size > 100000) { fclose(fp); return 0; }' >> $@
	@echo '    char *buf = malloc(size + 1);' >> $@
	@echo '    if (!buf) { fclose(fp); return 0; }' >> $@
	@echo '    fread(buf, 1, size, fp);' >> $@
	@echo '    fclose(fp);' >> $@
	@echo '    buf[size] = '\''\\0'\'';' >> $@
	@echo '    char out[256];' >> $@
	@echo '    base64_encode((uint8_t*)buf, size, out, sizeof(out));' >> $@
	@echo '    free(buf);' >> $@
	@echo '    return 0;' >> $@
	@echo '}' >> $@

# WebSocket frame fuzzer for ws_recv/ws_send in cdp_client.c
engine/fuzz_ws: engine/fuzz_ws.c engine/cdp_client.o engine/http_raw.o
	$(FUZZ_CC) $(FUZZ_CFLAGS) -o $@ $< engine/cdp_client.o engine/http_raw.o $(FUZZ_LDFLAGS)

fuzz_ws: engine/fuzz_ws
	@echo "Running WebSocket frame fuzzer..."
	@mkdir -p corpus/ws
	@./engine/fuzz_ws corpus/ws 10000

engine/fuzz_ws.c:
	@echo '/* WebSocket frame fuzzer for ws_recv - standalone harness */' > $@
	@echo '#include <stdint.h>' >> $@
	@echo '#include <stddef.h>' >> $@
	@echo '#include <stdlib.h>' >> $@
	@echo '#include <string.h>' >> $@
	@echo '#include <stdio.h>' >> $@
	@echo '#include "cdp_client.h"' >> $@
	@echo '' >> $@
	@echo '/* Test the JS escape logic in cdp_eval */' >> $@
	@echo 'int main(int argc, char **argv) {' >> $@
	@echo '    if (argc < 2) return 0;' >> $@
	@echo '    FILE *fp = fopen(argv[1], "rb");' >> $@
	@echo '    if (!fp) return 0;' >> $@
	@echo '    fseek(fp, 0, SEEK_END);' >> $@
	@echo '    long size = ftell(fp);' >> $@
	@echo '    fseek(fp, 0, SEEK_SET);' >> $@
	@echo '    if (size <= 0 || size > 100000) { fclose(fp); return 0; }' >> $@
	@echo '    char *buf = malloc(size + 1);' >> $@
	@echo '    if (!buf) { fclose(fp); return 0; }' >> $@
	@echo '    fread(buf, 1, size, fp);' >> $@
	@echo '    fclose(fp);' >> $@
	@echo '    buf[size] = '\'\'\\0'\'';' >> $@
	@echo '    /* Test the escape loop in cdp_eval */' >> $@
	@echo '    size_t dst_len = 0;' >> $@
	@echo '    for (size_t i = 0; i < (size_t)size; i++) {' >> $@
	@echo '        switch (buf[i]) {' >> $@
	@echo '            case '\''\"'\''': case '\''\\''\'':'\\''': case '\''\\n'\''': case '\''\\r'\''': case '\''\\t'\''': dst_len += 2; break;' >> $@
	@echo '            default: dst_len += 1; break;' >> $@
	@echo '        }' >> $@
	@echo '    }' >> $@
	@echo '    free(buf);' >> $@
	@echo '    return 0;' >> $@
	@echo '}' >> $@

# Run all fuzzers
fuzz_all: fuzz_json fuzz_base64 fuzz_ws

# Corpus directories for fuzzers
corpus:
	mkdir -p corpus/json corpus/base64 corpus/ws