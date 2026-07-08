/**
 * whisper_fallback.c — C11 tiny.en transcription for video audio
 *
 * Uses whisper.cpp (built as library) or faster_whisper Python fallback.
 * For videos without "In this video" panels.
 *
 * Compile: gcc -std=gnu11 -O3 -march=native -I../include -o whisper_fallback \
 *          engine/whisper_fallback.c -lwhisper -lpthread -lm
 *
 * Usage: ./whisper_fallback <audio.wav>
 */

#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdatomic.h>
#include <time.h>
#include <unistd.h>

/* whisper.cpp API (if available) */
#ifdef USE_WHISPER_CPP
#include <whisper.h>
#endif

/* Timing helper */
static inline uint64_t time_ms(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000 + (uint64_t)ts.tv_nsec / 1000000;
}

/* Result */
typedef struct {
    char *transcript;
    size_t len;
    uint64_t duration_ms;
    int rc; /* 0=ok, non-zero=error */
} WhisperResult;

#ifdef USE_WHISPER_CPP
/* ── whisper.cpp native path (fastest CPU) ── */
static WhisperResult transcribe_native(const char *audio_path) {
    WhisperResult result = {0};
    uint64_t t0 = time_ms();
    
    struct whisper_context *ctx = whisper_init_from_file("models/ggml-tiny.en.bin");
    if (!ctx) {
        fprintf(stderr, "[whisper] Failed to load model\n");
        result.rc = -1;
        result.duration_ms = time_ms() - t0;
        return result;
    }
    
    struct whisper_full_params params = whisper_full_default_params(
        WHISPER_SAMPLING_GREEDY);
    params.print_progress = false;
    params.print_special   = false;
    params.print_realtime  = false;
    params.language        = "en";
    
    if (whisper_full(ctx, params, audio_path) != 0) {
        fprintf(stderr, "[whisper] Transcription failed\n");
        whisper_free(ctx);
        result.rc = -2;
        result.duration_ms = time_ms() - t0;
        return result;
    }
    
    /* Collect text */
    int n_segments = whisper_full_n_segments(ctx);
    size_t total = 0;
    for (int i = 0; i < n_segments; i++) {
        const char *text = whisper_full_get_segment_text(ctx, i);
        total += strlen(text);
    }
    
    result.transcript = malloc(total + 1);
    if (!result.transcript) {
        whisper_free(ctx);
        result.rc = -3;
        result.duration_ms = time_ms() - t0;
        return result;
    }
    
    result.transcript[0] = '\0';
    for (int i = 0; i < n_segments; i++) {
        strcat(result.transcript, whisper_full_get_segment_text(ctx, i));
    }
    result.len = strlen(result.transcript);
    
    whisper_free(ctx);
    result.duration_ms = time_ms() - t0;
    return result;
}
#endif

/* ── Python fallback (faster_whisper) ── */
static WhisperResult transcribe_python(const char *audio_path) {
    WhisperResult result = {0};
    uint64_t t0 = time_ms();
    
    char cmd[1024];
    int len = snprintf(cmd, sizeof(cmd),
        "python3 -c \""
        "import sys; "
        "from faster_whisper import WhisperModel; "
        "m = WhisperModel('tiny.en', device='cpu', compute_type='int8'); "
        "segs, _ = m.transcribe('%s', beam_size=5, vad_filter=True); "
        "print(''.join(s.text for s in segs))"
        "\" 2>/dev/null",
        audio_path);
    
    if (len < 0 || (size_t)len >= sizeof(cmd)) {
        result.rc = -1;
        result.duration_ms = time_ms() - t0;
        return result;
    }
    
    FILE *fp = popen(cmd, "r");
    if (!fp) {
        result.rc = -2;
        result.duration_ms = time_ms() - t0;
        return result;
    }
    
    size_t capacity = 1024 * 1024; /* 1MB initial */
    result.transcript = malloc(capacity);
    if (!result.transcript) {
        pclose(fp);
        result.rc = -3;
        result.duration_ms = time_ms() - t0;
        return result;
    }
    
    size_t total = 0;
    size_t n;
    while ((n = fread(result.transcript + total, 1, capacity - total - 1, fp)) > 0) {
        total += n;
        if (total >= capacity - 1) {
            capacity *= 2;
            char *new_buf = realloc(result.transcript, capacity);
            if (!new_buf) break;
            result.transcript = new_buf;
        }
    }
    result.transcript[total] = '\0';
    result.len = total;
    
    int status = pclose(fp);
    result.rc = (status == 0) ? 0 : -4;
    result.duration_ms = time_ms() - t0;
    
    return result;
}

/* ── Main ── */
int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <audio.wav>\n", argv[0]);
        return 1;
    }
    
    WhisperResult result;
    
#ifdef USE_WHISPER_CPP
    fprintf(stderr, "[whisper] Using native whisper.cpp\n");
    result = transcribe_native(argv[1]);
#else
    fprintf(stderr, "[whisper] Using faster_whisper fallback\n");
    result = transcribe_python(argv[1]);
#endif
    
    if (result.rc != 0) {
        fprintf(stderr, "[whisper] Error: rc=%d\n", result.rc);
        return result.rc;
    }
    
    /* Output JSON */
    fprintf(stdout, "{\"transcript\":\"");
    for (const char *p = result.transcript; *p; p++) {
        switch (*p) {
            case '"':  fputs("\\\"", stdout); break;
            case '\\': fputs("\\\\", stdout); break;
            case '\n': fputs("\\n", stdout); break;
            case '\r': fputs("\\r", stdout); break;
            case '\t': fputs("\\t", stdout); break;
            default:   fputc(*p, stdout); break;
        }
    }
    fprintf(stdout, "\"}\n");
    
    fprintf(stderr, "[whisper] %zu chars in %llums\n",
            result.len, (unsigned long long)result.duration_ms);
    
    free(result.transcript);
    return 0;
}
