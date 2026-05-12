Songpraise.com énekek musescore kompatibilis formába való konvertálása

Használati útmutató:
1. [songpraise](songpraise.com) weboldalon kiválasztjuk az énekünket.
2. Az url címet berakjuk




Dev run:
```
uv run musescore-lyrics
```

Build:
```
uv run pyinstaller musescore-lyrics.spec
```

or 
```
uv run pyinstaller --onefile --windowed --name musescore-lyrics src/musescore_lyrics/main.py
```