/**
 * absorber_main.c — C11 YouTube CDP Transcript Engine
 * 
 * Connects to Chrome via CDP, navigates to YouTube videos,
 * extracts "In this video" engagement panel transcripts.
 * 
 * Compile: gcc -std=gnu11 -O3 -march=native -I../include -o absorption_c11 \
 *          engine/absorber_main.c engine/cdp_client.c engine/http_raw.c engine/video_store.c \
 *          -lpthread
 * 
 * Usage: cat video_ids.txt | ./absorption_c11
 * Output: One JSON line per video to stdout.
 */

#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdatomic.h>
#include <stdalign.h>
#include <threads.h>
#include <time.h>
#include <unistd.h>
#include <errno.h>
#include <signal.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <fcntl.h>
#include <poll.h>

#include "cdp_client.h"
#include "http_raw.h"
#include "video_store.h"

/* ── C11 static assertions ── */
_Static_assert(sizeof(int) >= 4, "int must be at least 32-bit");
_Static_assert(sizeof(size_t) >= 8, "size_t must be at least 64-bit");
_Static_assert(alignof(max_align_t) >= 16, "max_align_t must be >= 16 for SIMD");

/* ── Configuration ── */
#define MAX_VIDEO_ID_LEN    32
#define MAX_URL_LEN         256
#define MAX_TRANSCRIPT_LEN   (2 * 1024 * 1024)  /* 2MB max transcript */
#define CDP_TIMEOUT_MS       30000
#define PAGE_LOAD_MS         15000
#define TRANSCRIPT_WAIT_MS   8000
#define BATCH_SIZE           20
#define MAX_CDP_PORT_LEN     16

/* ── Thread-local error buffer ── */
_Thread_local char tls_error_buf[256] = {0};

/* ── Atomic stop flag ── */
static atomic_bool g_stop = false;

/* ── Signal handler ── */
static _Noreturn void handle_signal(int sig) {
    (void)sig;
    atomic_store(&g_stop, true);
    /* Write minimal response to stderr for clean shutdown */
    const char msg = '\0';
    ssize_t wr = write(STDERR_FILENO, &msg, 1);
    (void)wr;
    _exit(0);
}

/* ── Result codes ── */
typedef enum : int {
    RESULT_OK = 0,
    RESULT_NO_PANEL,
    RESULT_EMPTY,
    RESULT_WHISPER_NEEDED,
    RESULT_CDP_ERROR,
    RESULT_HTTP_ERROR,
    RESULT_TIMEOUT,
    RESULT_UNKNOWN
} ResultCode;

/* ── Result record ── */
typedef struct {
    char video_id[MAX_VIDEO_ID_LEN];
    ResultCode code;
    uint32_t transcript_len;
    uint32_t duration_ms;
} __attribute__((aligned(64))) ResultRecord;

/* ── Timing helper ── */
static inline uint64_t time_ms(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000 + (uint64_t)ts.tv_nsec / 1000000;
}

/* ── Output result as JSON line ── */
static void output_result(const ResultRecord *r, const char *transcript) {
    /* Use fputs for buffered I/O — faster than printf for large strings */
    fputc('{', stdout);
    fputs("\"video_id\":\"", stdout);
    fputs(r->video_id, stdout);
    fputs("\",\"status\":", stdout);
    
    switch (r->code) {
        case RESULT_OK:              fputs("\"ok\"", stdout); break;
        case RESULT_NO_PANEL:        fputs("\"no_panel\"", stdout); break;
        case RESULT_EMPTY:           fputs("\"empty\"", stdout); break;
        case RESULT_WHISPER_NEEDED:  fputs("\"whisper\"", stdout); break;
        case RESULT_CDP_ERROR:       fputs("\"cdp_error\"", stdout); break;
        case RESULT_HTTP_ERROR:      fputs("\"http_error\"", stdout); break;
        case RESULT_TIMEOUT:         fputs("\"timeout\"", stdout); break;
        default:                     fputs("\"unknown\"", stdout); break;
    }
    
    fputs(",\"duration_ms\":", stdout);
    {
        char buf[32];
        int len = snprintf(buf, sizeof(buf), "%u", r->duration_ms);
        fwrite(buf, 1, (size_t)len, stdout);
    }
    
    if (r->code == RESULT_OK && transcript) {
        fputs(",\"transcript\":\"", stdout);
        /* Escape JSON strings inline */
        for (const char *p = transcript; *p; p++) {
            switch (*p) {
                case '"':  fputs("\\\"", stdout); break;
                case '\\': fputs("\\\\", stdout); break;
                case '\n': fputs("\\n", stdout); break;
                case '\r': fputs("\\r", stdout); break;
                case '\t': fputs("\\t", stdout); break;
                default:   fputc(*p, stdout); break;
            }
        }
        fputc('"', stdout);
    }
    
    fputs("}\n", stdout);
}

/* ── Discover Chrome CDP port ── */
static int discover_cdp_port(char *port_buf, size_t port_buf_size) {
    /* Use hardcoded port 9222 for Windows Chrome via port forwarding */
    strncpy(port_buf, "9222", port_buf_size - 1);
    port_buf[port_buf_size - 1] = '\0';
    return 0;
}

/* ── Discover Chrome CDP host ── */
static int discover_cdp_host(char *host_buf, size_t host_buf_size) {
    /* Use localhost since chromium runs in WSL */
    strncpy(host_buf, "127.0.0.1", host_buf_size - 1);
    host_buf[host_buf_size - 1] = '\0';
    return 0;
}

/* ── Process single video ── */
static ResultRecord process_video(const char *video_id) {
    ResultRecord rec = {0};
    memcpy(rec.video_id, video_id, MAX_VIDEO_ID_LEN - 1);
    rec.video_id[MAX_VIDEO_ID_LEN - 1] = '\0';
    
    uint64_t t0 = time_ms();
    
    /* Check stop flag */
    if (atomic_load(&g_stop)) {
        rec.code = RESULT_TIMEOUT;
        rec.duration_ms = (uint32_t)(time_ms() - t0);
        return rec;
    }
    
    /* Discover CDP port */
    char cdp_port[MAX_CDP_PORT_LEN] = {0};
    if (discover_cdp_port(cdp_port, sizeof(cdp_port)) != 0) {
        rec.code = RESULT_CDP_ERROR;
        rec.duration_ms = (uint32_t)(time_ms() - t0);
        return rec;
    }

    /* Discover CDP host */
    char cdp_host[64] = {0};
    if (discover_cdp_host(cdp_host, sizeof(cdp_host)) != 0) {
        rec.code = RESULT_CDP_ERROR;
        rec.duration_ms = (uint32_t)(time_ms() - t0);
        return rec;
    }

    /* Build CDP connection */
    cdp_client_t *cdp = cdp_connect(cdp_host, cdp_port);
    if (!cdp) {
        rec.code = RESULT_CDP_ERROR;
        rec.duration_ms = (uint32_t)(time_ms() - t0);
        return rec;
    }
    
    /* Navigate to video */
    char url[MAX_URL_LEN];
    int url_len = snprintf(url, sizeof(url), 
                          "https://www.youtube.com/watch?v=%s", video_id);
    if (url_len < 0 || (size_t)url_len >= sizeof(url)) {
        cdp_destroy(cdp);
        rec.code = RESULT_UNKNOWN;
        rec.duration_ms = (uint32_t)(time_ms() - t0);
        return rec;
    }
    
    if (cdp_navigate(cdp, url) != 0) {
        cdp_destroy(cdp);
        rec.code = RESULT_CDP_ERROR;
        rec.duration_ms = (uint32_t)(time_ms() - t0);
        return rec;
    }
    
    /* Wait for page load */
    usleep((useconds_t)PAGE_LOAD_MS * 1000);

    /* Check for "In this video" panel */
    bool has_panel = false;
    for (int attempt = 0; attempt < 3 && !atomic_load(&g_stop); attempt++) {
        has_panel = cdp_check_panel(cdp);
        fprintf(stderr, "[absorber] Panel check attempt %d: %s\n", attempt + 1, has_panel ? "FOUND" : "NOT FOUND");
        if (has_panel) break;
        usleep(5000 * 1000); /* 5s retry wait */
    }

    if (!has_panel) {
        cdp_destroy(cdp);
        rec.code = RESULT_NO_PANEL;
        rec.duration_ms = (uint32_t)(time_ms() - t0);
        return rec;
    }
    
    /* Click "In this video" */
    fprintf(stderr, "[absorber] Clicking panel...\n");
    cdp_click_panel(cdp);
    usleep(5000 * 1000); /* 5s wait for expansion */
    
    /* Click "Transcript" tab */
    fprintf(stderr, "[absorber] Clicking transcript tab...\n");
    cdp_click_transcript_tab(cdp);
    usleep(8000 * 1000); /* 8s wait for transcript */
    
    /* Extract transcript text */
    char *transcript = cdp_extract_transcript(cdp);
    cdp_destroy(cdp);
    
    if (!transcript) {
        rec.code = RESULT_EMPTY;
        rec.duration_ms = (uint32_t)(time_ms() - t0);
        return rec;
    }
    
    size_t tlen = strlen(transcript);
    if (tlen < 100) {
        free(transcript);
        rec.code = RESULT_WHISPER_NEEDED;
        rec.duration_ms = (uint32_t)(time_ms() - t0);
        return rec;
    }
    
    /* Output result BEFORE freeing transcript */
    rec.code = RESULT_OK;
    rec.transcript_len = (uint32_t)tlen;
    rec.duration_ms = (uint32_t)(time_ms() - t0);
    output_result(&rec, transcript);
    
    /* Save transcript to file */
    video_store_save(video_id, transcript, tlen);
    free(transcript);
    
    return rec;
}

/* ── Main ── */
int main(void) {
    /* Set up signal handlers */
    struct sigaction sa = {0};
    sa.sa_handler = handle_signal;
    sigemptyset(&sa.sa_mask);
    sigaction(SIGINT, &sa, NULL);
    sigaction(SIGTERM, &sa, NULL);
    
    /* Disable SIGPIPE */
    signal(SIGPIPE, SIG_IGN);
    
    /* Set line buffering for stdout */
    setvbuf(stdout, NULL, _IOLBF, 0);
    
    /* Initialize video store */
    video_store_init();
    
    /* Read video IDs from stdin */
    char line[MAX_VIDEO_ID_LEN + 2];
    int count = 0;
    
    while (fgets(line, sizeof(line), stdin)) {
        if (atomic_load(&g_stop)) break;
        
        /* Strip newline */
        size_t len = strlen(line);
        while (len > 0 && (line[len-1] == '\n' || line[len-1] == '\r'))
            line[--len] = '\0';
        
        if (len == 0) continue;
        if (len >= MAX_VIDEO_ID_LEN) continue;
        
        /* Process */
        ResultRecord rec = process_video(line);
        
        /* Output result */
        if (rec.code != RESULT_OK) {
            output_result(&rec, NULL);
        }
        
        count++;
        if (count % BATCH_SIZE == 0) {
            fflush(stdout);
        }
    }
    
    fflush(stdout);
    fprintf(stderr, "[absorber] processed %d videos\n", count);
    return 0;
}