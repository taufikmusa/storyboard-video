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
tools/video_beats.py  # selaraskan shot breakdown video Scene 1/2 dengan dialog
data/beats/<id>.json  # babak video yang dah diselaraskan (dipakai automatik oleh converter)
```

## Tambah batch baru

Tab sekarang: **Script-01** hingga **Script-07** (setiap satu 30 set × 3 scene = 90 scene, edisi kucing 3D & storyboard emas).

1. Letak docx dalam `sources/`.
2. Jalankan converter ikut format docx:
   - Format `SET #NN:` / `SCENE N:` (Script-01):
     ```bash
     python3 tools/script_docx_to_json.py sources/xxx.docx --id s02-script --label "Script-02" --tags "kucing,emas,3-scene,script-02"
     ```
   - Format lama `Set NN:` (Heading 1) / `Scene N:` (Heading 2): `tools/docx_to_json.py`
   - Format B-Roll `Klip N :`: `tools/broll_docx_to_json.py`

   Nombor set dalam docx diabaikan — setiap tab sentiasa Set-01 hingga Set-30 ikut susunan dalam docx.

   Script akan tulis `data/<id>.json`, kemas kini `data/manifest.json`, dan beri amaran kalau ada scene yang dialog/panel/timeline tak cukup.
3. Commit & push. GitHub Pages terus update.

## Video prompt selari dengan dialog (Google Flow)

Untuk lip-sync Google Flow, setiap babak dalam shot breakdown Scene 1/2 mesti fokus pada watak yang sedang menyebut baris dialog itu, ikut turutan (babak 1 = baris 1, dan seterusnya). Dialog tak diubah.

- Babak disimpan dalam `data/beats/<id>.json` sebagai `{"SS-N": [babak1, babak2, babak3, babak4]}`.
- Masa babak dikira automatik ikut panjang baris dialog (min 2.0s, jumlah 10s).
- `script_docx_to_json.py` guna fail ni setiap kali jalan, jadi semakan kekal bila docx dijana semula.
- Untuk tab baru: `python3 tools/video_beats.py dump s08-script` untuk tengok dialog + babak asal, tulis `data/beats/s08-script.json`, kemudian jalankan semula converter.

## Test local

```bash
python3 -m http.server 8000   # buka http://localhost:8000
```

Status "dah guna" disimpan dalam `localStorage` browser — tak sync antara device.
