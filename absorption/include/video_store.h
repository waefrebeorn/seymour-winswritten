/**
 * video_store.h — Save transcripts to disk
 */
#ifndef VIDEO_STORE_H
#define VIDEO_STORE_H

#include <stddef.h>

void video_store_init(void);
int  video_store_save(const char *video_id, const char *data, size_t len);
bool video_store_has(const char *video_id);
int  video_store_count(void);

#endif /* VIDEO_STORE_H */
