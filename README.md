Songpraise.com énekek musescore kompatibilis formába való konvertálása

Használati útmutató:
1. [songpraise](songpraise.com) weboldalon kiválasztjuk az énekünket.
2. Az url címet berakjuk fentre a song url-be
3. Rámegyünk hogy 'fetch', majd ellenőrizzük hogy jót kaptunk el
4. Rámegyünk hogy 'process', majd ellenőrizzük hogy jó lett-e (Néha van hogy nem szed szét bizonyos szavakat)
5. A 'copy' gombbal pedig automatikuson kimásolja a szövegünket

Ezután már a musescoreba a ctr+v -t nyomogatva tudunk végig menni a szavakon.

Vannak eszközök, amiket a "select custom tool" -ban lehet elérni, ezek meg tudják mutatni ha valahol nincs elválasztva és esetleg ezeket elválasztja.




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