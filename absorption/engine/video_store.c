/**
 * video_store.c — Save transcripts to disk
 *
 * C11, fast I/O with large buffers.
 */

#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <dirent.h>
#include <unistd.h>
#include <errno.h>

#include "video_store.h"

#define DATA_DIR      "./data/transcripts"
#define FAILED_DIR    "./data/failed"
#define MAX_PATH_LEN  512

static bool g_initialized = false;

void video_store_init(void) {
    if (g_initialized) return;
    
    /* Create directories */
    (void)mkdir(DATA_DIR, 0755);
    (void)mkdir(FAILED_DIR, 0755);
    
    g_initialized = true;
}

int video_store_save(const char *video_id, const char *data, size_t len) {
    if (!g_initialized) video_store_init();
    
    char path[MAX_PATH_LEN];
    int path_len = snprintf(path, sizeof(path), "%s/%s.txt", DATA_DIR, video_id);
    if (path_len < 0 || (size_t)path_len >= sizeof(path)) return -1;
    
    /* Use fopen with large buffer for speed */
    FILE *fp = fopen(path, "w");
    if (!fp) return -1;
    
    /* Set a large buffer (256KB) for fewer syscalls */
    setvbuf(fp, NULL, _IOFBF, 256 * 1024);
    
    /* Write in single call */
    size_t written = fwrite(data, 1, len, fp);
    
    /* Also write video_id as last line for metadata */
    fprintf(fp, "\n\n<!-- VIDEO_ID:%s -->\n", video_id);
    
    fclose(fp);
    
    return (written == len) ? 0 : -1;
}

bool video_store_has(const char *video_id) {
    char path[MAX_PATH_LEN];
    int path_len = snprintf(path, sizeof(path), "%s/%s.txt", DATA_DIR, video_id);
    if (path_len < 0 || (size_t)path_len >= sizeof(path)) return false;
    
    return (access(path, F_OK) == 0);
}

int video_store_count(void) {
    if (!g_initialized) video_store_init();
    
    DIR *dir = opendir(DATA_DIR);
    if (!dir) return 0;
    
    int count = 0;
    struct dirent *entry;
    while ((entry = readdir(dir)) != NULL) {
        if (entry->d_name[0] == '.') continue;
        if (strstr(entry->d_name, ".txt")) count++;
    }
    closedir(dir);
    
    return count;
}
