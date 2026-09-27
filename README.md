# 🎬 Storyboard Vault

Vault prompt storyboard & prompt video — cari, buka, salin. Static site untuk GitHub Pages (tiada build step).

## Struktur

```
index.html            # page utama
assets/style.css      # tema gelap + emas
assets/app.js         # carian, filter, salin, cadangan harian, "dah guna"
data/manifest.json    # senarai batch yang dimuatkan
data/<id>.json        # data setiap batch (dijana dari docx)
sources/*.docx        # dokumen asal
tools/docx_to_json.py # penukar docx -> json (stdlib Python sahaja)
```

## Tambah batch baru

1. Letak docx dalam `sources/`.
2. Jalankan:
   ```bash
   python3 tools/docx_to_json.py sources/Batch_02_xxx.docx --id lelaki-emas-02 \
     --label "Lelaki-Emas-3-Scene-02" --tags "lelaki,emas,3-scene,batch-02"
   ```
   Script akan tulis `data/lelaki-emas-02.json` dan kemas kini `data/manifest.json`, dan beri amaran kalau ada scene yang dialog/panel tak cukup.
3. Commit & push. GitHub Pages terus update.

Format docx yang dijangka: `Heading 1` = `Set NN: Tajuk`, `Heading 2` = `Scene N: ...`, prompt image bermula `(A)`/`Bahagian 1`, prompt video bermula `(B)`/`Bahagian 2`.

## Test local

```bash
python3 -m http.server 8000   # buka http://localhost:8000
```

Status "dah guna" disimpan dalam `localStorage` browser — tak sync antara device.
