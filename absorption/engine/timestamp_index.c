/**
 * timestamp_index.c — C11 Timestamp Parser + Selective Clipper
 * 
 * Parses transcripts with [MM:SS] or inline timestamps,
 * builds a searchable index, and produces clipped transcripts
 * containing only relevant segments.
 * 
 * Compile: gcc -std=gnu11 -O3 -march=native -I../include -o timestamp_index \
 *          engine/timestamp_index.c engine/transcript_parser.c engine/clip_maker.c \
 *          -lpthread
 * 
 * Usage: ./timestamp_index <transcript_dir> <output_dir>
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
#include <stdalign.h>
#include <time.h>
#include <unistd.h>
#include <errno.h>
#include <dirent.h>
#include <sys/stat.h>

#include "transcript_parser.h"
#include "clip_maker.h"

#define MAX_VIDEOS      512
#define MAX_SEGMENTS    10000
#define MAX_LINE_LEN    4096

/* ── Static assertions ── */
_Static_assert(MAX_VIDEOS >= 468, "MAX_VIDEOS must cover full library");
_Static_assert(MAX_LINE_LEN >= 2048, "MAX_LINE_LEN must cover long transcript lines");

/* ── Video index entry ── */
typedef struct {
    char video_id[16];
    char title[256];
    char filename[512];
    uint32_t total_segments;
    uint32_t total_words;
    uint32_t duration_sec;
} __attribute__((aligned(64))) VideoIndex;

/* ── Global index ── */
static VideoIndex g_index[MAX_VIDEOS];
static uint32_t g_video_count = 0;

/* ── Scan directory for transcript files ── */
static int scan_transcripts(const char *dir) {
    DIR *dp = opendir(dir);
    if (!dp) {
        fprintf(stderr, "[index] Cannot open %s: %s\n", dir, strerror(errno));
        return -1;
    }
    
    struct dirent *entry;
    while ((entry = readdir(dp)) != NULL) {
        if (entry->d_name[0] == '.') continue;
        
        size_t len = strlen(entry->d_name);
        if (len < 5) continue;
        
        /* Check if it's a transcript file */
        const char *ext = entry->d_name + len - 4;
        if (strcmp(ext, ".txt") != 0) continue;
        
        if (g_video_count >= MAX_VIDEOS) break;
        
        /* Parse filename: TITLE_VIDEOID_transcript.txt or TITLE_VIDEOID_engagement.txt */
        char *underscore = strrchr(entry->d_name, '_');
        if (!underscore) continue;
        
        /* Extract video ID (last 11 chars before _transcript.txt or _engagement.txt) */
        char vid[16] = {0};
        size_t vid_offset = 0;
        
        if (strstr(entry->d_name, "_engagement.txt")) {
            vid_offset = strlen(entry->d_name) - strlen("_engagement.txt") - 11;
        } else if (strstr(entry->d_name, "_transcript.txt")) {
            vid_offset = strlen(entry->d_name) - strlen("_transcript.txt") - 11;
        } else {
            continue;
        }
        
        memcpy(vid, entry->d_name + vid_offset, 11);
        vid[11] = '\0';
        
        /* Store in index */
        VideoIndex *vi = &g_index[g_video_count];
        strncpy(vi->video_id, vid, sizeof(vi->video_id) - 1);
        strncpy(vi->filename, entry->d_name, sizeof(vi->filename) - 1);
        
        /* Title = everything before the video ID */
        size_t title_len = vid_offset;
        if (title_len > 0 && entry->d_name[title_len - 1] == '_') title_len--;
        if (title_len >= sizeof(vi->title)) title_len = sizeof(vi->title) - 1;
        memcpy(vi->title, entry->d_name, title_len);
        vi->title[title_len] = '\0';
        
        g_video_count++;
    }
    
    closedir(dp);
    return (int)g_video_count;
}

/* ── Build word counts for each transcript ── */
static void build_stats(const char *dir) {
    char path[1024];
    
    for (uint32_t i = 0; i < g_video_count; i++) {
        snprintf(path, sizeof(path), "%s/%s", dir, g_index[i].filename);
        
        FILE *fp = fopen(path, "r");
        if (!fp) {
            g_index[i].total_words = 0;
            g_index[i].total_segments = 0;
            continue;
        }
        
        char line[MAX_LINE_LEN];
        uint32_t words = 0;
        uint32_t segments = 0;
        
        while (fgets(line, sizeof(line), fp)) {
            /* Skip header lines */
            if (line[0] == '#') continue;
            if (line[0] == '\n') continue;
            
            /* Count segments (lines with [MM:SS]) */
            if (strchr(line, '[') && strchr(line, ']')) {
                segments++;
            }
            
            /* Count words */
            char *p = line;
            bool in_word = false;
            while (*p) {
                if (*p > ' ' && *p < 127) {
                    if (!in_word) {
                        words++;
                        in_word = true;
                    }
                } else {
                    in_word = false;
                }
                p++;
            }
        }
        
        g_index[i].total_words = words;
        g_index[i].total_segments = segments;
        fclose(fp);
    }
}

/* ── Output index as JSON ── */
static void write_index_json(const char *output_path) {
    FILE *fp = fopen(output_path, "w");
    if (!fp) {
        fprintf(stderr, "[index] Cannot write %s\n", output_path);
        return;
    }
    
    fprintf(fp, "{\n");
    fprintf(fp, "  \"total_videos\": %u,\n", g_video_count);
    fprintf(fp, "  \"videos\": [\n");
    
    uint64_t total_words = 0;
    uint64_t total_segments = 0;
    
    for (uint32_t i = 0; i < g_video_count; i++) {
        VideoIndex *vi = &g_index[i];
        total_words += vi->total_words;
        total_segments += vi->total_segments;
        
        fprintf(fp, "    {\n");
        fprintf(fp, "      \"video_id\": \"%s\",\n", vi->video_id);
        fprintf(fp, "      \"title\": \"%s\",\n", vi->title);
        fprintf(fp, "      \"filename\": \"%s\",\n", vi->filename);
        fprintf(fp, "      \"words\": %u,\n", vi->total_words);
        fprintf(fp, "      \"segments\": %u\n", vi->total_segments);
        fprintf(fp, "    }%s\n", (i < g_video_count - 1) ? "," : "");
    }
    
    fprintf(fp, "  ],\n");
    fprintf(fp, "  \"totals\": {\n");
    fprintf(fp, "    \"words\": %llu,\n", (unsigned long long)total_words);
    fprintf(fp, "    \"segments\": %llu\n", (unsigned long long)total_segments);
    fprintf(fp, "  }\n");
    fprintf(fp, "}\n");
    
    fclose(fp);
    fprintf(stderr, "[index] Wrote %s (%u videos, %llu words)\n",
            output_path, g_video_count, (unsigned long long)total_words);
}

/* ── Main ── */
int main(int argc, char **argv) {
    if (argc < 3) {
        fprintf(stderr, "Usage: %s <transcript_dir> <output_dir>\n", argv[0]);
        fprintf(stderr, "\n");
        fprintf(stderr, "Scans transcript files, builds timestamp index,\n");
        fprintf(stderr, "outputs JSON with word counts and metadata.\n");
        return 1;
    }
    
    const char *input_dir = argv[1];
    const char *output_dir = argv[2];
    
    /* Ensure output directory exists */
    mkdir(output_dir, 0755);
    
    /* Scan */
    fprintf(stderr, "[index] Scanning %s...\n", input_dir);
    int count = scan_transcripts(input_dir);
    if (count < 0) return 1;
    fprintf(stderr, "[index] Found %d transcripts\n", count);
    
    /* Build stats */
    fprintf(stderr, "[index] Building word counts...\n");
    build_stats(input_dir);
    
    /* Write index */
    char json_path[1024];
    snprintf(json_path, sizeof(json_path), "%s/timestamp_index.json", output_dir);
    write_index_json(json_path);
    
    return 0;
}
