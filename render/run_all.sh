#!/bin/bash
# Render the full video in parallel chunks, then mux with the final audio.
set -e
cd "$(dirname "$0")"; source env.sh
OUT=$SCR/out; mkdir -p $OUT
NF=$((DUR*30)); P=${P:-4}; STEP=$(( (NF + P - 1) / P ))
pids=()
for i in $(seq 0 $((P-1))); do
  a=$((i*STEP)); b=$(( (i+1)*STEP )); [ $b -gt $NF ] && b=$NF
  python3 render.py $a $b $OUT/chunk_$i.mp4 > $OUT/chunk_$i.log 2>&1 &
  pids+=($!)
done
for p in "${pids[@]}"; do wait $p; done
: > $OUT/list.txt; for i in $(seq 0 $((P-1))); do echo "file 'chunk_$i.mp4'" >> $OUT/list.txt; done
ffmpeg -y -v error -f concat -safe 0 -i $OUT/list.txt -c copy $OUT/video.mp4
ffmpeg -y -v error -i $OUT/video.mp4 -i $SCR/audio/final_audio.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -ar 48000 \
  -frames:v $NF -t $DUR -movflags +faststart $OUT/mesir_explainer.mp4
echo RENDER_DONE
