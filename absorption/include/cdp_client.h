/**
 * cdp_client.h — Chrome DevTools Protocol client (WebSocket over raw socket)
 */
#ifndef CDP_CLIENT_H
#define CDP_CLIENT_H

#include <stddef.h>
#include <stdbool.h>
#include <stdint.h>

typedef struct cdp_client cdp_client_t;

/* Lifecycle */
cdp_client_t *cdp_connect(const char *host, const char *port);  /* Connect to host:port */
void          cdp_destroy(cdp_client_t *cdp);

/* Operations */
void base64_encode(const uint8_t *in, size_t in_len, char *out, size_t out_size);

int  cdp_navigate(cdp_client_t *cdp, const char *url);
bool cdp_check_panel(cdp_client_t *cdp);
int  cdp_click_panel(cdp_client_t *cdp);
int  cdp_click_transcript_tab(cdp_client_t *cdp);
char *cdp_extract_transcript(cdp_client_t *cdp);  /* Caller must free */

/* Evaluate JS expression, returns malloc'd result or NULL */
char *cdp_eval(cdp_client_t *cdp, const char *expression);

#endif /* CDP_CLIENT_H */
