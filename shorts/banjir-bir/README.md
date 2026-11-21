# Banjir Bir London (cartoon-3d-short)

- `SCRIPT.md`: fakta + sumber + script VO
- `voice/`: VO asli, `words.json` (timing per kata, dari `tools/align.py`)
- `remotion/`: project Remotion (komposisi `BeerShort`, 1080x1920, 30 fps, 1845 frame)
- `audio/beer_audio.py`: musik polka + SFX sintetis + mix dengan VO -> `audio/mix.wav`

Render (di folder `remotion/`, setelah `npm i`):
```
npx remotion render src/index.ts BeerShort out/video.mp4 --codec h264 --crf 18
ffmpeg -i out/video.mp4 -i ../audio/mix.wav -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k -shortest final.mp4
```
