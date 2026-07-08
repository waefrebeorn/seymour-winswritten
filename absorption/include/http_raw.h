/**
 * http_raw.h — Raw socket HTTP/1.1 client (no libcurl dependency)
 */
#ifndef HTTP_RAW_H
#define HTTP_RAW_H

#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>

typedef struct {
    int sockfd;
    char host[256];
    uint16_t port;
    char last_response[8192];
    int  last_status;
} http_conn_t;

/* Connection */
int  http_connect(http_conn_t *conn, const char *host, uint16_t port);
void http_close(http_conn_t *conn);

/* HTTP requests */
int  http_get(http_conn_t *conn, const char *path);
int  http_get_json(http_conn_t *conn, const char *path, char **out_body, size_t *out_len);

/* JSON helpers */
char *json_find_key(const char *body, const char *key, size_t *value_len);
int   json_find_int(const char *body, const char *key);

/* PUT request for CDP /json/new */
int http_put_json(http_conn_t *conn, const char *path, char **out_body, size_t *out_len);

#endif /* HTTP_RAW_H */
