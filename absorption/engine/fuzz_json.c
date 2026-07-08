/* JSON fuzzer for json_find_key - standalone harness */
#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include "http_raw.h"

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
    size_t vlen;
    char *result = json_find_key(buf, "value", &vlen);
    free(result);
    free(buf);
    return 0;
}