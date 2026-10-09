#!/usr/bin/env python3
"""Tukar dokumen 'Koleksi Lengkap 30 Set Prompt Bersiri 3 Scene' (.docx) kepada JSON untuk Storyboard Vault.

Format: 'SET #NN: TAJUK' atau 'SET NN — TAJUK' -> 'SCENE N: TAJUK' -> '(A) ...' image prompt -> '(B) ...' video prompt.
Scene 1/2: dialog selepas 'DO NOT TRANSLATE THESE LINES:' (Nama: "baris") atau 'Dialogue (...)' (bernombor),
timeline 'a-bs ...' / '- a-bs: ...'.
Scene 3: panel storyboard 'N. Nama - SHOT' + 'Action:'/'Time:', dialog bernombor selepas 'Dialogue (spoken ...)'.
Jadual ringkasan (#NN / NN, sudut/persona, tajuk, gaya) dibaca untuk tajuk & gaya setiap set.

Guna:  python3 tools/script_docx_to_json.py sources/xxx.docx --id s01-script --label "Script-01" --tags "kucing,emas"
"""
import argparse, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from docx_to_json import DATA, clean_block, read_paragraphs


SET_RE = re.compile(r"^SET #?(\d+)\s*[:—–-]\s*(.*)$")
ROW_RE = re.compile(r"^#?(\d{1,2})$")


def parse_table(paras):
    """Jadual ringkasan sebelum SET pertama: no, persona/sudut, tajuk, gaya.
    Pulangkan (rows, (mula, akhir)) — julat termasuk tajuk jadual + 4 header lajur."""
    texts = [t.strip() for _, t in paras]
    out, first, last = {}, None, None
    for i, t in enumerate(texts[:-3]):
        if SET_RE.match(t):
            break
        m = ROW_RE.match(t)
        if m:
            out[int(m.group(1))] = {"persona": texts[i + 1], "title": texts[i + 2], "gaya": texts[i + 3]}
            first = i if first is None else first
            last = i + 3
    return out, ((first - 5, last) if first is not None else (-1, -1))


def parse_guide(paras, span):
    guide, items = [], None
    for i, (style, text) in enumerate(paras):
        t = text.strip()
        if SET_RE.match(t):
            break
        if span[0] <= i <= span[1]:
            items = None
            continue
        bullet = style == "ListBullet" or t.startswith("- ")
        if not bullet and (re.match(r"^\d+\.\s+[A-Z]", t) or t.startswith("BAHAGIAN")
                           or (t.endswith(":") and len(t) < 90)):
            guide.append({"h": t.rstrip(":")})
            items = None
        elif not guide:
            continue
        elif bullet:
            if items is None:
                items = []
                guide.append({"items": items})
            items.append(t[2:] if t.startswith("- ") else t)
        else:
            # baris pendek tanpa noktah = nama watak / sub-tajuk dalam Character Reference Sheet
            guide.append({"h": t} if len(t) < 60 and "." not in t else {"p": t})
            items = None
    return guide


def parse_scene(num, heading, body):
    start = next((i for i, l in enumerate(body) if l.strip().startswith("(A)")), 0)
    split = next((i for i, l in enumerate(body) if l.strip().startswith("(B)")), len(body))
    img, vid = body[start:split], body[split:]
    image_prompt, video_prompt = clean_block(img[1:]), clean_block(vid[1:])

    dialog, timeline, panels = [], [], []
    on = False
    for l in vid:
        s = l.strip()
        if s.startswith("DO NOT TRANSLATE") or s.startswith("Dialogue ("):
            on = True
            continue
        if on:
            m = re.match(r'^([^:"]+):\s*"(.*)"$', s)
            n = re.match(r"^\d+\.\s+(.*)$", s)
            if m:
                dialog.append({"who": m.group(1).strip(), "line": m.group(2).strip()})
            elif n:
                dialog.append({"who": "Hos" if num == 3 else "", "line": n.group(1).strip()})
            else:
                on = False
        m = re.match(r"^(?:-\s*)?([\d.]+-[\d.]+s):?\s+(.*)$", s)
        if m:
            timeline.append({"time": m.group(1), "action": m.group(2)})

    cur = None
    for l in img:
        s = l.strip()
        m = re.match(r"^(\d+)\.\s+(.+?\s-\s.+)$", s)
        if m:
            cur = {"n": int(m.group(1)), "time": "", "action": m.group(2)}
            panels.append(cur)
        elif cur and s.startswith("Action:"):
            cur["action"] += ": " + s[7:].strip()
        elif cur and s.startswith("Time:"):
            cur["time"] = s[5:].strip()

    return {
        "scene": num,
        "heading": heading,
        "imageLabel": img[0].strip() if img else "",
        "imagePrompt": image_prompt,
        "videoLabel": vid[0].strip() if vid else "",
        "videoPrompt": video_prompt,
        "dialog": dialog,
        "timeline": timeline,
        "panels": panels,
    }


def parse(path):
    paras = [(s, t) for s, t in read_paragraphs(path) if t.strip()]
    title = paras[0][1].replace("\n", " ").strip() if paras else ""
    table, span = parse_table(paras)
    guide = parse_guide(paras, span)
    sets, cur_set, cur_scene, buf = [], None, None, []

    def flush():
        nonlocal buf, cur_scene
        if cur_set is not None and cur_scene is not None:
            cur_set["scenes"].append(parse_scene(cur_scene[0], cur_scene[1], buf))
        buf, cur_scene = [], None

    for _, text in paras:
        t = text.strip()
        m = SET_RE.match(t)
        if m:
            flush()
            n = int(m.group(1))
            row = table.get(n, {})
            cur_set = {"set": n, "title": row.get("title") or m.group(2).strip(), "arc": "",
                       "gaya": row.get("gaya", ""), "persona": row.get("persona", ""), "scenes": []}
            sets.append(cur_set)
            continue
        m = re.match(r"^SCENE (\d+):\s*(.*)$", t)
        if m and cur_set is not None:
            flush()
            cur_scene = (int(m.group(1)), m.group(2).strip())
            continue
        if cur_set is None:
            continue
        if cur_scene is None:
            if not cur_set["arc"]:
                cur_set["arc"] = re.sub(r"\s*\n\s*", " | ", t)
            continue
        buf.append(text)
    flush()
    return title, guide, sets


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("docx")
    ap.add_argument("--id", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--tags", default="")
    a = ap.parse_args()

    title, guide, sets = parse(a.docx)
    if not sets:
        sys.exit("Tiada 'SET #NN:' / 'SET NN —' dijumpai — semak format docx.")
    out = {
        "id": a.id,
        "label": a.label,
        "title": title,
        "source": Path(a.docx).name,
        "tags": [t.strip() for t in a.tags.split(",") if t.strip()],
        "guide": guide,
        "sets": sets,
    }
    DATA.mkdir(exist_ok=True)
    (DATA / f"{a.id}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    mpath = DATA / "manifest.json"
    manifest = json.loads(mpath.read_text()) if mpath.exists() else {"batches": []}
    manifest["batches"] = [b for b in manifest["batches"] if b["id"] != a.id]
    manifest["batches"].append({"id": a.id, "label": a.label, "file": f"{a.id}.json"})
    manifest["batches"].sort(key=lambda b: b["id"])
    mpath.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")

    n = sum(len(s["scenes"]) for s in sets)
    print(f"OK: {len(sets)} set, {n} scene -> data/{a.id}.json")
    for s in sets:
        if len(s["scenes"]) != 3: print(f"  ! Set {s['set']:02d}: scene={len(s['scenes'])}")
        for sc in s["scenes"]:
            flags = []
            if len(sc["dialog"]) != 4: flags.append(f"dialog={len(sc['dialog'])}")
            if not sc["imagePrompt"] or not sc["videoPrompt"]: flags.append("prompt kosong")
            if sc["scene"] == 3 and len(sc["panels"]) != 8: flags.append(f"panel={len(sc['panels'])}")
            if sc["scene"] != 3 and len(sc["timeline"]) != 4: flags.append(f"timeline={len(sc['timeline'])}")
            if flags: print(f"  ! Set {s['set']:02d} Scene {sc['scene']}: {', '.join(flags)}")


if __name__ == "__main__":
    main()
