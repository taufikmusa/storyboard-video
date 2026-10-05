#!/usr/bin/env python3
"""Tukar dokumen 'B-Roll Koleksi' (.docx) kepada JSON untuk Storyboard Vault.

Setiap 'Klip N : Nama' jadi satu set dengan 1 scene sahaja.

Boleh beri beberapa docx sekaligus; semua digabung dalam satu tab, nombor klip bersambung
ikut susunan fail, dan setiap klip ditanda kumpulan (Batch N / Live NN) dari nama fail.

Guna:  python3 tools/broll_docx_to_json.py sources/B_Roll_*.docx --id b00-broll --label "B-Roll"
Output: data/<id>.json, dan data/manifest.json dikemas kini automatik.
"""
import argparse, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from docx_to_json import DATA, clean_block, read_paragraphs


def field(text, name):
    m = re.search(rf"(?:^|\|)\s*{name}:\s*(.*?)\s*(?:\||$)", text, flags=re.M)
    return m.group(1).strip() if m else ""


def parse(path):
    paras = [(s, t) for s, t in read_paragraphs(path) if t.strip()]
    clips, cur, guide = [], None, []
    for _, text in paras:
        m = re.match(r"^Klip (\d+)\s*:\s*(.+)$", text.strip())
        if m:
            cur = {"n": int(m.group(1)), "name": m.group(2).strip(), "meta": "", "img": [], "vid": [], "on": None}
            clips.append(cur)
            continue
        if text.startswith("Jadual Ringkasan"):
            cur = None
            continue
        if text.startswith("Peringatan Penting"):
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            guide += [{"h": lines[0].rstrip(":")}, {"items": [re.sub(r"^\d+\.\s*", "", l) for l in lines[1:]]}]
            continue
        if cur is None:
            continue
        if text.startswith("Padanan Skrip"):
            cur["meta"] = text
        elif text.startswith("Bahagian 1"):
            cur["on"], cur["imgLabel"] = "img", text.strip()
        elif text.startswith("Bahagian 2"):
            cur["on"], cur["vidLabel"] = "vid", text.strip()
        elif cur["on"]:
            cur[cur["on"]].append(text)

    sets = []
    for c in clips:
        img, vid = clean_block(c["img"]), clean_block(c["vid"])
        skrip, shot, ayat = field(c["meta"], "Padanan Skrip"), field(c["meta"], "Jenis shot"), field(c["meta"], "Guna untuk ayat")
        panels = [{"n": int(m.group(1)), "time": m.group(2), "action": m.group(3).strip()}
                  for m in re.finditer(r"^Frame (\d+) - ([\d.]+s) - (.+)$", img, flags=re.M)]
        act = re.search(r"^ACTION:\s*(.*)$", vid, flags=re.M)
        timeline = []
        for chunk in re.split(r"\s+(?=[\d.]+-[\d.]+s\s)", act.group(1).strip() if act else ""):
            m = re.match(r"^([\d.]+-[\d.]+s)\s+(.*?)\.?$", chunk)
            if m:
                timeline.append({"time": m.group(1), "action": m.group(2)})
        dur = re.search(r"DURATION:\s*(\d+)\s*seconds", vid)
        sets.append({
            "set": c["n"],
            "title": c["name"],
            "arc": c["meta"].replace("\n", " | "),
            "gaya": shot,
            "duration": int(dur.group(1)) if dur else 8,
            "skrip": skrip,
            "ayat": ayat,
            "scenes": [{
                "scene": 1,
                "heading": skrip,
                "imageLabel": c.get("imgLabel", "Bahagian 1"),
                "imagePrompt": img,
                "videoLabel": c.get("vidLabel", "Bahagian 2"),
                "videoPrompt": vid,
                "dialog": [],
                "timeline": timeline,
                "panels": panels,
            }],
        })
    return guide, sets


def group_label(path):
    m = re.search(r"_(Batch|Live)_(\d+)$", Path(path).stem)
    return f"{m.group(1)} {m.group(2)}" if m else "Batch 1"


def group_key(path):
    m = re.search(r"_(Batch|Live)_(\d+)$", Path(path).stem)
    return (0, 1) if not m else (0 if m.group(1) == "Batch" else 1, int(m.group(2)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("docx", nargs="+")
    ap.add_argument("--id", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--tags", default="b-roll,8-saat,tanpa-dialog")
    a = ap.parse_args()

    guide, sets = [], []
    for path in sorted(a.docx, key=group_key):
        g, ss = parse(path)
        if not ss:
            sys.exit(f"Tiada 'Klip N :' dijumpai dalam {path} — semak format docx.")
        guide = guide or g
        for sc in ss:
            sc.update(set=len(sets) + 1, group=group_label(path), klip=sc["set"])
            sets.append(sc)
    out = {
        "id": a.id,
        "label": a.label,
        "kind": "broll",
        "title": "B-ROLL: KOLEKSI 9 SKRIP VIRAL SHORT",
        "source": ", ".join(Path(p).name for p in sorted(a.docx, key=group_key)),
        "tags": [t.strip() for t in a.tags.split(",") if t.strip()],
        "guide": [{"h": "Panduan B-Roll"},
                  {"p": "Pustaka klip 8 saat, 9:16 menegak, satu shot berterusan tanpa dialog. Setiap klip = 1 scene: "
                        "jana Storyboard Image (lampir gambar rujukan watak), kemudian Video Prompt."}] + guide,
        "sets": sets,
    }
    (DATA / f"{a.id}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    mpath = DATA / "manifest.json"
    manifest = json.loads(mpath.read_text())
    manifest["batches"] = [b for b in manifest["batches"] if b["id"] != a.id]
    manifest["batches"].append({"id": a.id, "label": a.label, "file": f"{a.id}.json"})
    manifest["batches"].sort(key=lambda b: b["id"])
    mpath.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"OK: {len(sets)} klip -> data/{a.id}.json")
    for s in sets:
        sc = s["scenes"][0]
        flags = []
        if len(sc["panels"]) != 4: flags.append(f"frame={len(sc['panels'])}")
        if len(sc["timeline"]) != 4: flags.append(f"action={len(sc['timeline'])}")
        if not sc["imagePrompt"] or not sc["videoPrompt"]: flags.append("prompt kosong")
        if flags: print(f"  ! Klip {s['set']:02d} ({s['group']} #{s['klip']}): {', '.join(flags)}")


if __name__ == "__main__":
    main()
