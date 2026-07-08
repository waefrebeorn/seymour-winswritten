/**
 * cdp_client.c — Chrome DevTools Protocol client
 * 
 * C11 implementation. Raw socket + WebSocket framing.
 * No libcurl, no openssl. Just POSIX.
 */

#ifndef _GNU_SOURCE
#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#endif
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include <unistd.h>
#include <errno.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <fcntl.h>
#include <poll.h>
#include <time.h>
#include <ctype.h>

#include "cdp_client.h"
#include "http_raw.h"

/* ── WebSocket constants ── */
#define WS_KEY_LEN     24
#define WS_HANDSHAKE_BUF 4096
#define WS_FRAME_BUF   (16 * 1024 * 1024)  /* 16MB for large transcripts */
#define WS_TIMEOUT_MS  30000

/* ── Fuzzing exports ── */
#ifdef FUZZING
#define FUZZ_EXPORT
#else
#define FUZZ_EXPORT static
#endif

/* ── CDP Client struct ── */
struct cdp_client {
    int sockfd;
    char host[256];
    uint16_t port;
    char ws_path[512];
    uint64_t msg_id;
    char recv_buf[WS_FRAME_BUF];
    char send_buf[WS_FRAME_BUF];
};

/* ── Helper: base64 encode (for WS key) ── */
static const char b64_table[] = 
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

void base64_encode(const uint8_t *in, size_t in_len, char *out, size_t out_size) {
    size_t j = 0;
    for (size_t i = 0; i < in_len; i += 3) {
        uint32_t octet_a = in[i];
        uint32_t octet_b = (i + 1 < in_len) ? in[i + 1] : 0;
        uint32_t octet_c = (i + 2 < in_len) ? in[i + 2] : 0;
        uint32_t triple = (octet_a << 16) | (octet_b << 8) | octet_c;
        
        if (j + 4 >= out_size) break;
        out[j++] = b64_table[(triple >> 18) & 0x3F];
        out[j++] = b64_table[(triple >> 12) & 0x3F];
        out[j++] = (i + 1 < in_len) ? b64_table[(triple >> 6) & 0x3F] : '=';
        out[j++] = (i + 2 < in_len) ? b64_table[triple & 0x3F] : '=';
    }
    out[j] = '\0';
}

/* ── Generate random WS key ── */
static void generate_ws_key(char *key, size_t len) {
    uint8_t rand_bytes[16];
    FILE *urandom = fopen("/dev/urandom", "r");
    if (urandom) {
        size_t n = fread(rand_bytes, 1, 16, urandom);
        fclose(urandom);
        if (n < 16) {
            /* Fallback to less random */
            srand((unsigned)time(NULL) ^ (unsigned)getpid());
            for (int i = 0; i < 16; i++) rand_bytes[i] = (uint8_t)(rand() & 0xFF);
        }
    }
    base64_encode(rand_bytes, 16, key, len);
}

/* ── WebSocket frame send ── */
static int ws_send(cdp_client_t *cdp, const char *data) {
    size_t len = strlen(data);
    uint8_t header[14];
    size_t header_len = 0;

    /* FIN=1, opcode=text(0x1) */
    header[0] = 0x81;

    /* Generate mask key */
    uint8_t mask[4];
    srand((unsigned)time(NULL) ^ (unsigned)getpid());
    for (int i = 0; i < 4; i++) mask[i] = (uint8_t)(rand() & 0xFF);

    if (len < 126) {
        header[1] = (uint8_t)(len | 0x80); /* MASK=1 */
        header[2] = mask[0];
        header[3] = mask[1];
        header[4] = mask[2];
        header[5] = mask[3];
        header_len = 6;
    } else if (len < 65536) {
        header[1] = (uint8_t)(126 | 0x80);
        header[2] = (uint8_t)(len >> 8);
        header[3] = (uint8_t)(len & 0xFF);
        header[4] = mask[0];
        header[5] = mask[1];
        header[6] = mask[2];
        header[7] = mask[3];
        header_len = 8;
    } else {
        header[1] = (uint8_t)(127 | 0x80);
        for (int i = 0; i < 8; i++)
            header[2 + i] = (uint8_t)(len >> (56 - 8 * i));
        header[10] = mask[0];
        header[11] = mask[1];
        header[12] = mask[2];
        header[13] = mask[3];
        header_len = 14;
    }

    /* Send header + mask */
    ssize_t sent = send(cdp->sockfd, header, header_len, MSG_NOSIGNAL);
    if (sent != (ssize_t)header_len) return -1;

    /* Mask and send data */
    for (size_t i = 0; i < len; i++) {
        uint8_t byte = ((uint8_t)data[i]) ^ mask[i % 4];
        sent = send(cdp->sockfd, &byte, 1, MSG_NOSIGNAL);
        if (sent != 1) return -1;
    }

    return 0;
}

/* ── WebSocket frame receive ── */
static int ws_recv(cdp_client_t *cdp, char *out, size_t out_max, int timeout_ms) {
    struct pollfd pfd = { .fd = cdp->sockfd, .events = POLLIN };
    int rc = poll(&pfd, 1, timeout_ms);
    if (rc <= 0) return -1;
    
    /* Read frame header (at least 2 bytes) */
    ssize_t n = recv(cdp->sockfd, cdp->recv_buf, 2, 0);
    if (n != 2) return -1;
    
    uint8_t opcode = cdp->recv_buf[0] & 0x0F;
    bool masked = cdp->recv_buf[1] & 0x80;
    uint64_t payload_len = cdp->recv_buf[1] & 0x7F;
    
    if (payload_len == 126) {
        uint8_t len_buf[2];
        n = recv(cdp->sockfd, len_buf, 2, MSG_WAITALL);
        if (n != 2) return -1;
        payload_len = ((uint64_t)len_buf[0] << 8) | len_buf[1];
    } else if (payload_len == 127) {
        uint8_t len_buf[8];
        n = recv(cdp->sockfd, len_buf, 8, MSG_WAITALL);
        if (n != 8) return -1;
        payload_len = 0;
        for (int i = 0; i < 8; i++)
            payload_len = (payload_len << 8) | len_buf[i];
    }
    
    if (masked) {
        uint8_t mask[4];
        n = recv(cdp->sockfd, mask, 4, MSG_WAITALL);
        if (n != 4) return -1;
    }
    
    if (payload_len > out_max - 1) {
        /* Too large — read and discard */
        uint64_t remaining = payload_len;
        while (remaining > 0) {
            size_t chunk = (remaining < WS_FRAME_BUF) ? (size_t)remaining : WS_FRAME_BUF;
            n = recv(cdp->sockfd, cdp->recv_buf, chunk, 0);
            if (n <= 0) return -1;
            remaining -= (uint64_t)n;
        }
        return -2; /* RESULT_TOO_LARGE */
    }
    
    /* Read payload */
    uint64_t received = 0;
    while (received < payload_len) {
        n = recv(cdp->sockfd, out + received, 
                 (size_t)(payload_len - received), 0);
        if (n <= 0) return -1;
        received += (uint64_t)n;
    }
    
    out[received] = '\0';
    
    /* Handle close frame */
    if (opcode == 0x8) return -3; /* RESULT_CLOSED */
    
    return (int)received;
}

/* ── Send CDP command ── */
static int cdp_send(cdp_client_t *cdp, const char *method, const char *params) {
    char *msg = malloc(WS_FRAME_BUF);
    if (!msg) return -1;
    int len = snprintf(msg, WS_FRAME_BUF,
        "{\"id\":%lu,\"method\":\"%s\",\"params\":%s}",
        (unsigned long)++cdp->msg_id, method,
        params ? params : "{}");

    if (len < 0 || (size_t)len >= WS_FRAME_BUF) {
        free(msg);
        return -1;
    }
    int result = ws_send(cdp, msg);
    free(msg);
    return result;
}

/* ── Receive CDP response ── */
static int cdp_recv(cdp_client_t *cdp, char *out, size_t out_max) {
    return ws_recv(cdp, out, out_max, WS_TIMEOUT_MS);
}

/* ── Public: Connect ── */
cdp_client_t *cdp_connect(const char *host, const char *port) {
    cdp_client_t *cdp = calloc(1, sizeof(cdp_client_t));
    if (!cdp) return NULL;

    strncpy(cdp->host, host, sizeof(cdp->host) - 1);
    cdp->port = (uint16_t)atoi(port);
    cdp->sockfd = -1;

    /* HTTP GET /json to find a page target */
    http_conn_t http;
    if (http_connect(&http, host, cdp->port) != 0) {
        free(cdp);
        return NULL;
    }
    
    /* Try to get /json/list first */
    char *body = NULL;
    size_t body_len = 0;
    int status = http_get_json(&http, "/json/list", &body, &body_len);
    http_close(&http);
    
    char ws_url[512] = {0};
    
    if (status == 200 && body) {
        /* Look for a page type with webSocketDebuggerUrl */
        const char *p = body;
        while ((p = strstr(p, "\"type\"")) != NULL) {
            /* Check if this is a page type - could be "type":"page" or "type": "page" */
            const char *colon = p + strlen("\"type\"");
            while (*colon == ' ' || *colon == '\t') colon++;
            if (*colon != ':') { p++; continue; }
            colon++;
            while (*colon == ' ' || *colon == '\t') colon++;
            if (*colon != '\"') { p++; continue; }
            colon++;
            if (strncmp(colon, "page\"", 5) == 0) {
                /* Find webSocketDebuggerUrl after this */
                const char *ws = strstr(p, "\"webSocketDebuggerUrl\":\"");
                if (ws) {
                    ws += strlen("\"webSocketDebuggerUrl\":\"");
                    const char *end = strchr(ws, '\"');
                    if (end && (size_t)(end - ws) < sizeof(ws_url)) {
                        memcpy(ws_url, ws, (size_t)(end - ws));
                        ws_url[end - ws] = '\0';
                    }
                    break;
                }
            }
            p++;
        }
        free(body);
    }
    
    if (ws_url[0] == '\0') {
        /* No page found — create one with PUT */
        http_conn_t http2;
        if (http_connect(&http2, cdp->host, cdp->port) != 0) {
            free(cdp);
            return NULL;
        }
        char *new_body = NULL;
        size_t new_len = 0;
        int status = http_put_json(&http2, "/json/new?about:blank", &new_body, &new_len);
        http_close(&http2);
        
        if (status == 200 && new_body) {
            size_t vlen;
            char *ws = json_find_key(new_body, "webSocketDebuggerUrl", &vlen);
            if (ws) {
                strncpy(ws_url, ws, sizeof(ws_url) - 1);
                free(ws);
            }
            free(new_body);
        }
    }
    
    if (ws_url[0] == '\0') {
        fprintf(stderr, "[cdp] No WebSocket URL found\n");
        free(cdp);
        return NULL;
    }
    
    /* Parse ws_url: ws://<host>:<port><path> */
    const char *host_start = strstr(ws_url, "://");
    if (!host_start) { free(cdp); return NULL; }
    host_start += 3;

    const char *port_start = strchr(host_start, ':');
    if (!port_start) { free(cdp); return NULL; }
    port_start++;

    const char *path_start = strchr(port_start, '/');
    if (path_start) {
        strncpy(cdp->ws_path, path_start, sizeof(cdp->ws_path) - 1);
    }

    /* Extract host from WS URL */
    char ws_host[256] = {0};
    size_t host_len = (size_t)(port_start - host_start - 1);
    if (host_len >= sizeof(ws_host)) host_len = sizeof(ws_host) - 1;
    memcpy(ws_host, host_start, host_len);

    /* Extract port from WS URL */
    char ws_port[8] = {0};
    size_t port_len = path_start ? (size_t)(path_start - port_start) : strlen(port_start);
    if (port_len >= sizeof(ws_port)) port_len = sizeof(ws_port) - 1;
    memcpy(ws_port, port_start, port_len);

    /* Connect TCP */
    struct addrinfo hints = {0}, *res = NULL;
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;

    int rc = getaddrinfo(ws_host, ws_port, &hints, &res);
    if (rc != 0) { free(cdp); return NULL; }
    
    cdp->sockfd = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
    if (cdp->sockfd < 0) { freeaddrinfo(res); free(cdp); return NULL; }
    
    int flag = 1;
    setsockopt(cdp->sockfd, IPPROTO_TCP, TCP_NODELAY, &flag, sizeof(flag));
    
    struct timeval tv = { .tv_sec = 5, .tv_usec = 0 };
    setsockopt(cdp->sockfd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
    setsockopt(cdp->sockfd, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(tv));
    
    rc = connect(cdp->sockfd, res->ai_addr, res->ai_addrlen);
    freeaddrinfo(res);
    
    if (rc != 0) {
        close(cdp->sockfd);
        free(cdp);
        return NULL;
    }
    
    /* WebSocket handshake */
    char ws_key[WS_KEY_LEN + 1];
    generate_ws_key(ws_key, sizeof(ws_key));

    char *handshake = malloc(WS_HANDSHAKE_BUF);
    if (!handshake) {
        close(cdp->sockfd);
        free(cdp);
        return NULL;
    }
    int hlen = snprintf(handshake, WS_HANDSHAKE_BUF,
        "GET %s HTTP/1.1\r\n"
        "Host: %s:%s\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        "Sec-WebSocket-Key: %s\r\n"
        "Sec-WebSocket-Version: 13\r\n"
        "\r\n",
        cdp->ws_path, ws_host, ws_port, ws_key);

    ssize_t sent = send(cdp->sockfd, handshake, (size_t)hlen, MSG_NOSIGNAL);
    free(handshake);
    if (sent != hlen) {
        close(cdp->sockfd);
        free(cdp);
        return NULL;
    }
    
    /* Read handshake response */
    ssize_t received = recv(cdp->sockfd, cdp->recv_buf, 
                            WS_FRAME_BUF - 1, 0);
    if (received <= 0) {
        close(cdp->sockfd);
        free(cdp);
        return NULL;
    }
    cdp->recv_buf[received] = '\0';
    
    if (!strstr(cdp->recv_buf, "101 Switching Protocols") && !strstr(cdp->recv_buf, "101 WebSocket Protocol Handshake")) {
        fprintf(stderr, "[cdp] WS handshake failed: %.200s\n", cdp->recv_buf);
        close(cdp->sockfd);
        free(cdp);
        return NULL;
    }
    
    return cdp;
}

/* ── Public: Destroy ── */
void cdp_destroy(cdp_client_t *cdp) {
    if (!cdp) return;
    if (cdp->sockfd >= 0) {
        /* Send WS close frame */
        uint8_t close_frame[2] = {0x88, 0x80};
        send(cdp->sockfd, close_frame, 2, MSG_NOSIGNAL);
        close(cdp->sockfd);
    }
    free(cdp);
}

/* ── Public: Navigate ── */
int cdp_navigate(cdp_client_t *cdp, const char *url) {
    char params[512];
    snprintf(params, sizeof(params), "{\"url\":\"%s\"}", url);
    return cdp_send(cdp, "Page.navigate", params);
}

/* ── Public: Evaluate JS ── */
char *cdp_eval(cdp_client_t *cdp, const char *expression) {
    /* Escape the JS expression for JSON */
    char *escaped = malloc(WS_FRAME_BUF);
    if (!escaped) return NULL;
    
    char *dst = escaped;
    for (const char *src = expression; *src && (dst - escaped) < WS_FRAME_BUF - 1; src++) {
        switch (*src) {
            case '"': *dst++ = '\\'; *dst++ = '"'; break;
            case '\\': *dst++ = '\\'; *dst++ = '\\'; break;
            case '\n': *dst++ = '\\'; *dst++ = 'n'; break;
            case '\r': *dst++ = '\\'; *dst++ = 'r'; break;
            case '\t': *dst++ = '\\'; *dst++ = 't'; break;
            default: *dst++ = *src; break;
        }
    }
    *dst = '\0';
    
    fprintf(stderr, "[cdp] Escaped JS: %.200s\n", escaped);
    
    char *params = malloc(WS_FRAME_BUF);
    if (!params) { free(escaped); return NULL; }
    int len = snprintf(params, WS_FRAME_BUF,
        "{\"expression\":\"%s\",\"returnByValue\":true}", escaped);
    free(escaped);
    
    if (len < 0 || (size_t)len >= WS_FRAME_BUF) {
        free(params);
        return NULL;
    }

    if (cdp_send(cdp, "Runtime.evaluate", params) != 0) {
        free(params);
        return NULL;
    }
    free(params);

    char *resp = malloc(WS_FRAME_BUF);
    if (!resp) return NULL;
    int n = cdp_recv(cdp, resp, WS_FRAME_BUF);
    if (n <= 0) {
        free(resp);
        return NULL;
    }

    fprintf(stderr, "[cdp] Raw response: %.500s\n", resp);

    /* Extract result value - handle both type:value and direct value */
    size_t vlen;
    char *result = json_find_key(resp, "value", &vlen);
    if (!result) {
        free(resp);
        return NULL;
    }
    
    fprintf(stderr, "[cdp] Found value field: %s\n", result);
    
    /* Check if value is an object with type/value */
    size_t tlen;
    char *type = json_find_key(result, "type", &tlen);
    char *value = json_find_key(result, "value", &vlen);
    
    if (type && value && strcmp(type, "string") == 0) {
        /* It's a string value object */
        free(type);
        free(result);
        free(resp);
        return value; /* caller frees */
    }
    
    if (type) free(type);
    /* Return the raw value if it's already a string */
    free(resp);
    return result; /* caller frees */
}

/* ── Public: Check panel ── */
bool cdp_check_panel(cdp_client_t *cdp) {
    const char *js = 
        "(function() {"
        "  var h = document.querySelectorAll('[class*=\"panel-title-header\"], "
        "    [class*=\"header-text\"]');"
        "  for (var i = 0; i < h.length; i++) {"
        "    if ((h[i].textContent || '').trim() === 'In this video') return true;"
        "  }"
        "  return false;"
        "})()";
    
    char *result = cdp_eval(cdp, js);
    if (!result) return false;
    
    fprintf(stderr, "[cdp] Panel check result: '%s'\n", result);
    
    bool ok = (strcmp(result, "true") == 0);
    free(result);
    return ok;
}

/* ── Public: Click panel ── */
int cdp_click_panel(cdp_client_t *cdp) {
    const char *js = 
        "(function() {"
        "  var h = document.querySelectorAll('[class*=\"panel-title-header\"], "
        "    [class*=\"header-text\"]');"
        "  for (var i = 0; i < h.length; i++) {"
        "    if ((h[i].textContent || '').trim() === 'In this video') {"
        "      h[i].click(); return true;"
        "    }"
        "  }"
        "  return false;"
        "})()";
    
    char *result = cdp_eval(cdp, js);
    if (!result) return -1;
    
    fprintf(stderr, "[cdp] Click panel result: '%s'\n", result);
    
    int ok = (strcmp(result, "true") == 0);
    free(result);
    return ok ? 0 : -1;
}

/* ── Public: Click transcript tab ── */
int cdp_click_transcript_tab(cdp_client_t *cdp) {
    const char *js = 
        "(function() {"
        "  var tabs = document.querySelectorAll('[role=\"tab\"]');"
        "  for (var t = 0; t < tabs.length; t++) {"
        "    if ((tabs[t].textContent || '').trim() === 'Transcript') {"
        "      tabs[t].click(); return true;"
        "    }"
        "  }"
        "  return false;"
        "})()";
    
    char *result = cdp_eval(cdp, js);
    if (!result) return -1;
    
    fprintf(stderr, "[cdp] Click transcript result: '%s'\n", result);
    
    int ok = (strcmp(result, "true") == 0);
    free(result);
    return ok ? 0 : -1;
}

/* ── Public: Extract transcript ── */
char *cdp_extract_transcript(cdp_client_t *cdp) {
    const char *js = 
        "(function() {"
        "  var panels = document.querySelectorAll('[class*=\"style-scope ytd-engagement-panel-section-list-renderer\"]');"
        "  var results = [];"
        "  for (var i = 0; i < panels.length; i++) {"
        "    var text = panels[i].textContent || '';"
        "    if (text.length > 50) {"
        "      results.push({index: i, length: text.length, preview: text.substring(0, 200)});"
        "    }"
        "    if (/\\d+:\\d+/.test(text) && text.length > 1000) return text;"
        "  }"
        "  return JSON.stringify(results);"
        "})()";
    
    char *result = cdp_eval(cdp, js);
    if (!result) return NULL;
    
    fprintf(stderr, "[cdp] Transcript debug: %s\n", result);
    
    /* Now try to get the actual transcript */
    const char *js2 = 
        "(function() {"
        "  var panels = document.querySelectorAll('[class*=\"style-scope ytd-engagement-panel-section-list-renderer\"]');"
        "  for (var i = 0; i < panels.length; i++) {"
        "    var text = panels[i].textContent || '';"
        "    if (/\\d+:\\d+/.test(text) && text.length > 1000) return text;"
        "  }"
        "  return '';"
        "})()";
    
    char *result2 = cdp_eval(cdp, js2);
    free(result);
    return result2;
}
