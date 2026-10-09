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
tools/script_docx_to_json.py # penukar docx SET #NN / SCENE N -> json
```

## Tambah batch baru

Tab sekarang: **Script-01** (30 set × 3 scene = 90 scene, edisi kucing 3D & storyboard emas).

1. Letak docx dalam `sources/`.
2. Jalankan converter ikut format docx:
   - Format `SET #NN:` / `SCENE N:` (Script-01):
     ```bash
     python3 tools/script_docx_to_json.py sources/xxx.docx --id s02-script --label "Script-02" --tags "kucing,emas,3-scene,script-02"
     ```
   - Format lama `Set NN:` (Heading 1) / `Scene N:` (Heading 2): `tools/docx_to_json.py`
   - Format B-Roll `Klip N :`: `tools/broll_docx_to_json.py`

   Script akan tulis `data/<id>.json`, kemas kini `data/manifest.json`, dan beri amaran kalau ada scene yang dialog/panel/timeline tak cukup.
3. Commit & push. GitHub Pages terus update.

## Test local

```bash
python3 -m http.server 8000   # buka http://localhost:8000
```

Status "dah guna" disimpan dalam `localStorage` browser — tak sync antara device.
