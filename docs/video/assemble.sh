#!/bin/bash
set -e
cd "$(dirname "$0")"
SCENES=(01_title 02_architecture 03_tests 04_demo_run 05_metrics 06_idempotency 07_abstain 08_tamper 09_scope 10_whatbroke 11_closing)
mkdir -p clips
rm -f clips/*.mp4

for s in "${SCENES[@]}"; do
  dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "audio/${s}.wav")
  # pad 0.6s of silence before and after each clip so cuts don't feel abrupt
  padded=$(awk -v d="$dur" 'BEGIN{printf "%.3f", d + 1.2}')
  ffmpeg -y -loop 1 -i "slides/${s}.png" -i "audio/${s}.wav" \
    -filter_complex "[1:a]adelay=600|600,apad=pad_dur=0.6[a]" \
    -map 0:v -map "[a]" \
    -c:v libx264 -tune stillimage -pix_fmt yuv420p -r 30 \
    -c:a aac -b:a 192k -t "$padded" \
    "clips/${s}.mp4" -loglevel error
  echo "built clips/${s}.mp4  (${padded}s)"
done

# concat (relative paths, run from clips/ dir — ffmpeg on Windows can't resolve git-bash's /h/... paths)
printf "" > clips/list.txt
for s in "${SCENES[@]}"; do
  echo "file '${s}.mp4'" >> clips/list.txt
done

(cd clips && ffmpeg -y -f concat -safe 0 -i list.txt -c copy ../../rebound-demo.mp4 -loglevel error)
echo "DONE: docs/rebound-demo.mp4"
ffprobe -v error -show_entries format=duration -of csv=p=0 ../rebound-demo.mp4
