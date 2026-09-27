#!/usr/bin/env python3
"""Tukar dokumen 'Siri Prompt 3 Scene' (.docx) kepada JSON untuk Storyboard Vault.

Guna:  python3 tools/docx_to_json.py sources/Batch_01_xxx.docx --id lelaki-emas-01 --label "Lelaki-Emas-3-Scene-01"
Output: data/<id>.json, dan data/manifest.json dikemas kini automatik.
Stdlib sahaja — tak perlu pip install apa-apa.
"""
import argparse, html, json, re, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def read_paragraphs(path):
    xml = zipfile.ZipFile(path).read("word/document.xml").decode("utf-8")
    out = []
    for p in re.findall(r"<w:p[ >].*?</w:p>", xml, flags=re.S):
        style = re.search(r'<w:pStyle w:val="([^"]+)"', p)
        parts = re.findall(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>|(<w:br\s*/>)|(<w:tab\s*/>)", p)
        text = "".join(t if t else ("\n" if br else "\t") for t, br, tab in parts)
        out.append((style.group(1) if style else "", html.unescape(text).rstrip()))
    return out


def clean_block(lines):
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def section(lines, header_re):
    """Pulangkan baris dalam blok [Header ...] sehingga baris kosong."""
    out, on = [], False
    for ln in lines:
        if re.match(header_re, ln.strip()):
            on = True
            continue
        if on:
            if not ln.strip() or ln.strip().startswith("["):
                break
            out.append(ln.strip())
    return out


GLASSES_LINE = "She wears glasses."


def add_glasses_line(prompt):
    """Tambah ayat cermin mata di hujung perenggan 'Main Character:' (storyboard Scene 3)."""
    m = re.search(r"Main Character:\n(.+?)(?=\n\n|$)", prompt, flags=re.S)
    if not m or GLASSES_LINE in m.group(1):
        return prompt
    return prompt[:m.end(1)] + " " + GLASSES_LINE + prompt[m.end(1):]


def parse_scene(num, heading, body):
    split = next((i for i, l in enumerate(body)
                  if re.match(r"^\(B\)|^Bahagian 2", l.strip())), len(body))
    img, vid = body[:split], body[split:]
    img_label = img[0].strip() if img else ""
    vid_label = vid[0].strip() if vid else ""
    image_prompt = add_glasses_line(clean_block(img[1:]))
    video_prompt = clean_block(vid[1:])

    dialog = []
    for d in section(vid, r"^\[Dialogue"):
        m = re.match(r'^([^:"]+):\s*"?(.*?)"?$', d)
        if m and not d.startswith('"'):
            dialog.append({"who": m.group(1).strip(), "line": m.group(2).strip()})
        else:
            dialog.append({"who": "Hos", "line": d.strip().strip('"')})

    timeline = []
    for t in section(vid, r"^\[Timeline"):
        m = re.match(r"^([\d.]+\s*-\s*[\d.]+s):\s*(.*)$", t)
        if m:
            timeline.append({"time": m.group(1), "action": m.group(2)})

    panels = []
    for l in img:
        m = re.match(r"^Panel (\d+) \[([^\]]+)\]:\s*(.*?)(?:\s*Legend:.*)?$", l.strip())
        if m:
            panels.append({"n": int(m.group(1)), "time": m.group(2), "action": m.group(3)})

    return {
        "scene": num,
        "heading": heading,
        "imageLabel": img_label,
        "imagePrompt": image_prompt,
        "videoLabel": vid_label,
        "videoPrompt": video_prompt,
        "dialog": dialog,
        "timeline": timeline,
        "panels": panels,
    }


def parse(path):
    paras = read_paragraphs(path)
    title = next((t for s, t in paras if t.strip()), "")
    guide, sets = [], []
    cur_set = cur_scene = None
    buf = []

    def flush_scene():
        nonlocal buf, cur_scene
        if cur_set is not None and cur_scene is not None:
            cur_set["scenes"].append(parse_scene(cur_scene[0], cur_scene[1], buf))
        buf, cur_scene = [], None

    for style, text in paras:
        if style == "Heading1" and re.match(r"^Set \d+", text):
            flush_scene()
            m = re.match(r"^Set (\d+):\s*(.*)$", text)
            cur_set = {"set": int(m.group(1)), "title": m.group(2).strip(), "arc": "", "scenes": []}
            sets.append(cur_set)
            continue
        if style == "Heading2" and cur_set is not None and re.match(r"^Scene \d+", text):
            flush_scene()
            m = re.match(r"^Scene (\d+):\s*(.*)$", text)
            cur_scene = (int(m.group(1)), m.group(2).strip())
            continue
        if cur_set is None:
            if style.startswith("Heading"):
                guide.append({"h": text})
            elif text.strip() and guide:
                items = [i.strip() for i in re.split(r"•", text) if i.strip()]
                guide.append({"items": items} if len(items) > 1 or text.lstrip().startswith("•") else {"p": text})
            continue
        if cur_scene is None:
            if text.strip() and not cur_set["arc"]:
                cur_set["arc"] = text.strip()
            continue
        buf.append(text)
    flush_scene()
    return title, guide, sets


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("docx")
    ap.add_argument("--id", required=True, help="id fail, cth lelaki-emas-01")
    ap.add_argument("--label", required=True, help="label chip kategori")
    ap.add_argument("--tags", default="", help="tag dipisah koma")
    a = ap.parse_args()

    title, guide, sets = parse(a.docx)
    if not sets:
        sys.exit("Tiada 'Set NN:' dijumpai — semak format docx.")
    gaya = lambda arc: (re.search(r"Gaya Bukaan Hos:\s*(.*)$", arc) or [None, ""])[1]
    out = {
        "id": a.id,
        "label": a.label,
        "title": title,
        "source": Path(a.docx).name,
        "tags": [t.strip() for t in a.tags.split(",") if t.strip()],
        "guide": guide,
        "sets": [dict(s, gaya=gaya(s["arc"])) for s in sets],
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
        for sc in s["scenes"]:
            flags = []
            if len(sc["dialog"]) != 4: flags.append(f"dialog={len(sc['dialog'])}")
            if not sc["imagePrompt"] or not sc["videoPrompt"]: flags.append("prompt kosong")
            if sc["scene"] == 3 and len(sc["panels"]) != 8: flags.append(f"panel={len(sc['panels'])}")
            if flags: print(f"  ! Set {s['set']:02d} Scene {sc['scene']}: {', '.join(flags)}")


if __name__ == "__main__":
    main()
