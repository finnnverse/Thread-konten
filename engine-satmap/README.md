# engine-satmap

Engine video Shorts gaya "peta satelit + kartun" (skill `skills/satmap-story-shorts`).

Setup (sekali per container, butuh akses s3.amazonaws.com):
```
pip install faster-whisper scipy cairosvg
python3 engine/basemap.py      # unduh tile elevasi AWS Terrain Tiles -> levels/
python3 engine/colorize.py     # warnai jadi gaya satelit
python3 engine/sprites.py      # render maskot SVG -> sprites/ (lalu buat versi *_st stiker, lihat SKILL)
```
Per video: `projects/<slug>/vo.wav` + `video.py`, lalu
```
python3 engine/render.py projects/<slug> stills 1.0,5.0,...   # contact.jpg
python3 engine/render.py projects/<slug> full 4               # video_silent.mp4
python3 engine/audio.py projects/<slug>                       # mix_raw.wav
```
Folder data (`tiles/`, `levels/`, `sprites/`) dibuat ulang, tidak di-commit.
Catatan: `core.py` mencari `assets/`, `levels/`, `sprites/` satu tingkat di atas folder `engine/`.
