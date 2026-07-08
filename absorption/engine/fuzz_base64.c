/* Base64 fuzzer for cdp_client.c base64_encode - standalone harness */
#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include "cdp_client.h"

extern void base64_encode(const uint8_t *in, size_t in_len, char *out, size_t out_size);

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
    char out[256];
    base64_encode((uint8_t*)buf, size, out, sizeof(out));
    free(buf);
    return 0;
}