#!/usr/bin/env bash
# Launch stream whisper batch as a proper daemon
cd /home/wubu/seymour-project/whiteboard/seymour-pipe
source /home/wubu/seymour-project/.venv/bin/activate
nohup python3 stream_whisper_batch.py --input remaining_v4.txt > stream_batch.log 2>&1 &
echo $!