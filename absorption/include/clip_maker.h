/**
 * clip_maker.h — Selective clipping based on topic/keyword matching
 */
#ifndef CLIP_MAKER_H
#define CLIP_MAKER_H

#include "transcript_parser.h"
#include <stddef.h>
#include <stdint.h>

typedef struct {
    char keyword[64];
    char topic[128];
    uint32_t padding_sec;  /* Seconds to add before/after match */
} ClipRule;

typedef struct {
    ClipRule *rules;
    uint32_t rule_count;
    uint32_t max_rules;
} ClipFilter;

/* Create a clip filter */
ClipFilter *clip_filter_create(uint32_t max_rules);

/* Add a rule */
int clip_filter_add(ClipFilter *f, const char *keyword, 
                    const char *topic, uint32_t padding_sec);

/* Free filter */
void clip_filter_free(ClipFilter *f);

/* Produce a clipped transcript, returns malloc'd string */
char *clip_transcript(const Transcript *t, const ClipFilter *filter,
                      uint32_t *matched_segments_out);

/* Export as SRT with timestamps */
char *transcript_to_srt(const Transcript *t);

#endif /* CLIP_MAKER_H */
