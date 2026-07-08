/**
 * transcript_parser.h — Parse transcript files with timestamps
 */
#ifndef TRANSCRIPT_PARSER_H
#define TRANSCRIPT_PARSER_H

#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>

typedef struct {
    uint32_t timestamp_sec;  /* [MM:SS] → seconds */
    char *text;              /* Segment text (malloc'd) */
    uint16_t text_len;
    uint16_t words;
} TranscriptSegment;

typedef struct {
    char video_id[16];
    char title[256];
    TranscriptSegment *segments;
    uint32_t segment_count;
    uint32_t capacity;
    uint32_t total_words;
    uint32_t duration_sec;
} Transcript;

/* Parse a transcript file */
Transcript *transcript_parse(const char *path);

/* Free transcript memory */
void transcript_free(Transcript *t);

/* Extract video ID from filename */
int extract_video_id(const char *filename, char *vid_out, size_t vid_size);

#endif /* TRANSCRIPT_PARSER_H */
