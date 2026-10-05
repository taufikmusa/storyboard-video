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
tools/broll_docx_to_json.py # penukar docx B-Roll (Klip N) -> json
```

## Tambah batch baru

1. Letak docx dalam `sources/`.
2. Jalankan:
   ```bash
   python3 tools/docx_to_json.py sources/Batch_07_xxx.docx --id b07-nama-batch \
     --label "Nama-Batch-3-Scene-07" --tags "lelaki,emas,3-scene,batch-07"
   ```
   Script akan tulis `data/b07-nama-batch.json` dan kemas kini `data/manifest.json`, dan beri amaran kalau ada scene yang dialog/panel tak cukup.
3. Commit & push. GitHub Pages terus update.

Format docx yang dijangka: `Heading 1` = `Set NN: Tajuk`, `Heading 2` = `Scene N: ...`, prompt image bermula `(A)`/`Bahagian 1`, prompt video bermula `(B)`/`Bahagian 2`.

## Tab B-Roll

Docx B-Roll guna format `Klip N : Nama` (setiap klip = 1 scene, 8 saat, tanpa dialog). Id `b00-broll` supaya tab ni sentiasa paling depan.

```bash
python3 tools/broll_docx_to_json.py sources/B_Roll_Koleksi_9_Skrip_Viral_Short.docx --id b00-broll --label "B-Roll"
```

## Test local

```bash
python3 -m http.server 8000   # buka http://localhost:8000
```

Status "dah guna" disimpan dalam `localStorage` browser — tak sync antara device.
