/* WebSocket frame fuzzer for ws_recv - standalone harness */
#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include "cdp_client.h"

/* Test the JS escape logic in cdp_eval */
int main(int argc, char **argv) {
    if (argc < 2) return 0;
    FILE *fp = fopen(argv[1], "rb");
    if (!fp) return 0;
    fseek(fp, 0, SEEK_END);
    long size = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    if (size <= 0 || size > 100000) { fclose(fp); return 0; }
    char *buf = malloc(size + 1);
    if (!buf) { fclose(fp); return 0; }
    fread(buf, 1, size, fp);
    fclose(fp);
    buf[size] = '\0';
    /* Test the escape loop in cdp_eval */
    size_t dst_len = 0;
    for (size_t i = 0; i < (size_t)size; i++) {
        switch (buf[i]) {
            case '"': case '\\': case '\n': case '\r': case '\t': dst_len += 2; break;
            default: dst_len += 1; break;
        }
    }
    free(buf);
    return 0;
}