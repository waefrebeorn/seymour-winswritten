#!/bin/bash
mkdir -p /tmp/oga_manifests
cd /tmp/oga_manifests
for i in $(seq -w 0 28); do
  f="2D_Art_${i}.jsonl.zst"
  timeout 40 curl -sL --max-time 35 "https://huggingface.co/datasets/nyuuzyou/OpenGameArt-CC0/resolve/main/$f" -o "$f"
done
echo "fetched: $(ls *.zst 2>/dev/null | wc -l) manifests"
