/**
 * http_raw.c — Raw socket HTTP/1.1 client (no libcurl dependency)
 *
 * C11, no external deps. Uses POSIX sockets directly.
 * Optimized for speed: minimal copies, buffered reads.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
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

#include "http_raw.h"

/* ── Constants ── */
#define RECV_BUF_SIZE  (64 * 1024)
#define CONNECT_TIMEOUT_MS 5000
#define RECV_TIMEOUT_MS   10000

/* ── Fuzzing exports ── */
#ifdef FUZZING
#define FUZZ_EXPORT
#else
#define FUZZ_EXPORT static
#endif

/* ── Internal state ── */
static char g_recv_buf[RECV_BUF_SIZE];

/* ── Set socket non-blocking ── */
static int set_nonblocking(int fd) {
    int flags = fcntl(fd, F_GETFL, 0);
    if (flags == -1) return -1;
    return fcntl(fd, F_SETFL, flags | O_NONBLOCK);
}

/* ── Set TCP NODELAY for low latency ── */
static void set_tcp_nodelay(int fd) {
    int flag = 1;
    setsockopt(fd, IPPROTO_TCP, TCP_NODELAY, &flag, sizeof(flag));
}

/* ── Connect with timeout ── */
int http_connect(http_conn_t *conn, const char *host, uint16_t port) {
    memset(conn, 0, sizeof(*conn));
    
    strncpy(conn->host, host, sizeof(conn->host) - 1);
    conn->host[sizeof(conn->host) - 1] = '\0';
    conn->port = port;
    
    struct addrinfo hints = {0}, *res = NULL;
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;
    
    char port_str[8];
    snprintf(port_str, sizeof(port_str), "%u", port);
    
    int rc = getaddrinfo(host, port_str, &hints, &res);
    if (rc != 0) return -1;
    
    conn->sockfd = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
    if (conn->sockfd < 0) { freeaddrinfo(res); return -1; }
    
    set_tcp_nodelay(conn->sockfd);
    set_nonblocking(conn->sockfd);
    
    rc = connect(conn->sockfd, res->ai_addr, res->ai_addrlen);
    freeaddrinfo(res);
    
    if (rc != 0 && errno != EINPROGRESS) {
        close(conn->sockfd);
        conn->sockfd = -1;
        return -1;
    }
    
    if (rc != 0) {
        struct pollfd pfd = { .fd = conn->sockfd, .events = POLLOUT };
        int poll_rc = poll(&pfd, 1, CONNECT_TIMEOUT_MS);
        if (poll_rc <= 0 || !(pfd.revents & POLLOUT)) {
            close(conn->sockfd);
            conn->sockfd = -1;
            return -1;
        }
        int sockerr = 0;
        socklen_t len = sizeof(sockerr);
        getsockopt(conn->sockfd, SOL_SOCKET, SO_ERROR, &sockerr, &len);
        if (sockerr != 0) {
            close(conn->sockfd);
            conn->sockfd = -1;
            return -1;
        }
    }
    
    int flags = fcntl(conn->sockfd, F_GETFL, 0);
    fcntl(conn->sockfd, F_SETFL, flags & ~O_NONBLOCK);
    
    struct timeval tv = {
        .tv_sec = RECV_TIMEOUT_MS / 1000,
        .tv_usec = (RECV_TIMEOUT_MS % 1000) * 1000
    };
    setsockopt(conn->sockfd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
    
    return 0;
}

void http_close(http_conn_t *conn) {
    if (conn && conn->sockfd >= 0) {
        close(conn->sockfd);
        conn->sockfd = -1;
    }
}

int http_get(http_conn_t *conn, const char *path) {
    char req[4096];
    int req_len = snprintf(req, sizeof(req),
        "GET %s HTTP/1.1\r\n"
        "Host: %s:%u\r\n"
        "Connection: close\r\n"
        "Accept: application/json\r\n"
        "User-Agent: SeymourAbsorber/1.0\r\n"
        "\r\n",
        path, conn->host, conn->port);
    
    if (req_len < 0 || (size_t)req_len >= sizeof(req)) return -1;
    
    ssize_t sent = send(conn->sockfd, req, (size_t)req_len, MSG_NOSIGNAL);
    if (sent != req_len) return -1;
    
    ssize_t total = 0;
    ssize_t n;
    while ((n = recv(conn->sockfd, g_recv_buf + total,
                     RECV_BUF_SIZE - total - 1, 0)) > 0) {
        total += n;
        if (total >= RECV_BUF_SIZE - 1) break;
    }
    
    if (total <= 0) return -1;
    g_recv_buf[total] = '\0';
    
    memcpy(conn->last_response, g_recv_buf, sizeof(conn->last_response) - 1);
    conn->last_response[sizeof(conn->last_response) - 1] = '\0';
    
    char *space = strchr(g_recv_buf, ' ');
    if (space) conn->last_status = atoi(space + 1);
    
    return conn->last_status;
}

int http_get_json(http_conn_t *conn, const char *path, char **out_body, size_t *out_len) {
    int status = http_get(conn, path);
    if (status != 200) return status;
    
    char *body = strstr(conn->last_response, "\r\n\r\n");
    if (!body) return -1;
    body += 4;
    
    size_t body_len = strlen(body);
    *out_body = malloc(body_len + 1);
    if (!*out_body) return -1;
    memcpy(*out_body, body, body_len + 1);
    *out_len = body_len;
    return status;
}

/* ── Simple JSON key finder ── */
char *json_find_key(const char *body, const char *key, size_t *value_len) {
    if (!body || !key) return NULL;
    
    char search[256];
    int slen = snprintf(search, sizeof(search), "\"%s\"", key);
    if (slen < 0) return NULL;
    
    const char *p = body;
    while ((p = strstr(p, search)) != NULL) {
        p += slen;
        while (*p == ' ' || *p == '\t') p++;
        if (*p != ':') continue;
        p++;
        while (*p == ' ' || *p == '\t') p++;
        
        if (*p == '"') {
            p++;
            const char *end = strchr(p, '"');
            if (!end) return NULL;
            *value_len = (size_t)(end - p);
            char *result = malloc(*value_len + 1);
            if (!result) return NULL;
            memcpy(result, p, *value_len);
            result[*value_len] = '\0';
            return result;
        } else {
            const char *end = p;
            while (*end && *end != ',' && *end != '}' && *end != '\n') end++;
            *value_len = (size_t)(end - p);
            char *result = malloc(*value_len + 1);
            if (!result) return NULL;
            memcpy(result, p, *value_len);
            result[*value_len] = '\0';
            return result;
        }
    }
    return NULL;
}

int json_find_int(const char *body, const char *key) {
    size_t vlen;
    char *val = json_find_key(body, key, &vlen);
    if (!val) return -1;
    int result = atoi(val);
    free(val);
    return result;
}

/* ── PUT request for CDP /json/new ── */
int http_put_json(http_conn_t *conn, const char *path, char **out_body, size_t *out_len) {
    char req[4096];
    int req_len = snprintf(req, sizeof(req),
        "PUT %s HTTP/1.1\r\n"
        "Host: %s:%u\r\n"
        "Connection: close\r\n"
        "Accept: application/json\r\n"
        "User-Agent: SeymourAbsorber/1.0\r\n"
        "\r\n",
        path, conn->host, conn->port);

    if (req_len < 0 || (size_t)req_len >= sizeof(req)) return -1;

    ssize_t sent = send(conn->sockfd, req, (size_t)req_len, MSG_NOSIGNAL);
    if (sent != req_len) return -1;

    ssize_t total = 0;
    ssize_t n;
    while ((n = recv(conn->sockfd, g_recv_buf + total,
                     RECV_BUF_SIZE - total - 1, 0)) > 0) {
        total += n;
        if (total >= RECV_BUF_SIZE - 1) break;
    }

    if (total <= 0) return -1;
    g_recv_buf[total] = '\0';

    memcpy(conn->last_response, g_recv_buf, sizeof(conn->last_response) - 1);
    conn->last_response[sizeof(conn->last_response) - 1] = '\0';

    char *space = strchr(g_recv_buf, ' ');
    if (space) conn->last_status = atoi(space + 1);

    if (conn->last_status != 200) return conn->last_status;

    char *body = strstr(conn->last_response, "\r\n\r\n");
    if (!body) return -1;
    body += 4;

    size_t body_len = strlen(body);
    *out_body = malloc(body_len + 1);
    if (!*out_body) return -1;
    memcpy(*out_body, body, body_len + 1);
    *out_len = body_len;
    return 200;
}
