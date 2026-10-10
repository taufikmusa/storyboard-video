#!/usr/bin/env python3
"""Selaraskan shot breakdown video prompt Scene 1/2 dengan dialog (untuk Google Flow lip-sync).

Babak baharu disimpan dalam data/beats/<id>.json:  {"SS-N": ["babak 1", "babak 2", "babak 3", "babak 4"]}
(SS = nombor set 2 digit, N = scene). Babak ke-i mesti fokus pada watak yang menyebut baris dialog ke-i.
Masa setiap babak dikira automatik ikut bilangan perkataan baris dialog (min 2.0s, gandaan 0.5s, jumlah 10s).

script_docx_to_json.py memanggil apply() selepas parse, jadi semakan kekal bila docx dijana semula.

Guna:  python3 tools/video_beats.py dump s01-script        # papar dialog + babak asal untuk disemak
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BEATS = ROOT / "data" / "beats"
TIME_RE = re.compile(r"^(\s*)(-\s*)?([\d.]+-[\d.]+s)(:?)\s+(.*)$")


def timings(dialog, total=10.0, low=2.0):
    words = [max(1, len(d["line"].split())) for d in dialog]
    halves = [int(low * 2)] * len(words)  # kira dalam unit 0.5s
    spare = int(total * 2) - sum(halves)
    share = [w / sum(words) * spare for w in words]
    add = [int(s) for s in share]
    for i in sorted(range(len(words)), key=lambda i: share[i] - add[i], reverse=True)[:spare - sum(add)]:
        add[i] += 1
    out, t = [], 0.0
    for h, a in zip(halves, add):
        start, t = t, t + (h + a) / 2
        out.append(f"{start:.1f}-{t:.1f}s")
    return out


def rewrite(scene, beats):
    lines = scene["videoPrompt"].split("\n")
    idx = [i for i, l in enumerate(lines) if TIME_RE.match(l)]
    if len(idx) != len(beats) or len(beats) != len(scene["dialog"]):
        raise ValueError(f"babak={len(beats)} baris masa={len(idx)} dialog={len(scene['dialog'])}")
    times = timings(scene["dialog"])
    for i, beat, t in zip(idx, beats, times):
        indent, dash, _, colon, _ = TIME_RE.match(lines[i]).groups()
        lines[i] = f"{indent}{dash or ''}{t}{colon} {beat}"
    scene["videoPrompt"] = "\n".join(lines)
    scene["timeline"] = [{"time": t, "action": b} for t, b in zip(times, beats)]


def apply(data):
    path = BEATS / f"{data['id']}.json"
    if not path.exists():
        return 0
    beats = json.loads(path.read_text(encoding="utf-8"))
    n = 0
    for s in data["sets"]:
        for sc in s["scenes"]:
            key = f"{s['set']:02d}-{sc['scene']}"
            if key in beats:
                try:
                    rewrite(sc, beats[key])
                    n += 1
                except ValueError as e:
                    print(f"  ! beats {key}: {e}")
    return n


def dump(batch_id):
    data = json.loads((ROOT / "data" / f"{batch_id}.json").read_text(encoding="utf-8"))
    for s in data["sets"]:
        for sc in s["scenes"]:
            if sc["scene"] == 3:
                continue
            voice = re.search(r"Voice direction:\s*\n?(.*)", sc["videoPrompt"])
            print(f"## {s['set']:02d}-{sc['scene']} | {sc['heading']}")
            for d in sc["dialog"]:
                print(f"   D {d['who'] or '?'}: {d['line']}")
            for t in sc["timeline"]:
                print(f"   B {t['action']}")
            if voice:
                print(f"   V {voice.group(1).strip()}")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "dump":
        dump(sys.argv[2])
    else:
        sys.exit(__doc__)
