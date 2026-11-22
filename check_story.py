#!/usr/bin/env python3
"""check_story.py — semantic gate BEFORE rendering.

A pixel gate cannot tell whether 'ACTIVE DAYS' is labelling weekly data, or
whether a narrated number exists in the derived record. This gate reads the
declarative story spec + the derived JSON + the voice manifest and REFUSES
on any mismatch. Fail-closed: missing evidence is a refusal, never a pass.

    python check_story.py --spec story-spec.json --data org-activity.json \
        --manifest VOICE/voice-manifest.json --html contributions.html
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

# A label whose unit contradicts the data granularity is the exact defect
# the human vision gate caught in the v1 film. These are forbidden strings.
FORBIDDEN = [
    (r'active\s+days',   'weekly data must not be labelled "active days"'),
    (r'max\s*/\s*day',   'weekly peak must not be labelled "max/day"'),
    (r'\bper\s+day\b',   'weekly data must not use "per day"'),
]


def check(spec, data, man, html):
    fails = []
    # 1. every stat source exists in the derived record
    for s in spec['stats']:
        if s['source'] not in data:
            fails.append(f"stat[{s['id']}] source '{s['source']}' absent from derived data")
        if s['granularity'] == 'weekly' and not re.search(r'week', s['label'], re.I):
            fails.append(f"stat[{s['id']}] label '{s['label']}' lacks week granularity")
    # 2. forbidden labels in the rendered HTML
    for pat, why in FORBIDDEN:
        if re.search(pat, html, re.I):
            fails.append(f"HTML contains forbidden label ({pat}): {why}")
    # 3. every scene binds to real fields; narration numbers must equal derived values
    nums = {str(v) for v in data.values() if isinstance(v, (int, float))}
    nums |= {f"{v:,}" for v in data.values() if isinstance(v, (int, float))}
    for i, sc in enumerate(spec['scenes']):
        for b in sc['bind']:
            if b not in data:
                fails.append(f"scene[{i}] binds missing field '{b}'")
        if sc.get('voice') not in ('M2','F2'):
            fails.append(f"scene[{i}] unknown voice {sc.get('voice')}")
        # every 3+ digit number spoken must exist in derived data
        narration = re.sub(r'\b\d{4}-\d{2}-\d{2}\b', ' ', sc.get('narration',''))  # dates are not metrics
        for m in re.findall(r'\b\d[\d,]{2,}\b', narration):
            if m not in nums and m.replace(',','') not in nums:
                fails.append(f"scene[{i}] narrates {m} — not in derived data")
    # 4. scene timing must tile the narration without gaps/overlaps
    segs = man['segments']
    if len(segs) != len(spec['scenes']):
        fails.append(f"scene count {len(spec['scenes'])} != segment count {len(segs)}")
    for i,(sc,sg) in enumerate(zip(spec['scenes'],segs)):
        if abs(sc['t0']-sg['t0'])>0.01 or abs(sc['t1']-sg['t1'])>0.01:
            fails.append(f"scene[{i}] timing != manifest segment")
        if sc.get('voice') != sg['voice']:
            fails.append(f"scene[{i}] voice != manifest voice")
    # 5. seam: picture must exceed voice
    voice = man['total_s'] + 0.18*(len(segs)-1)
    if spec['picture_s'] <= voice:
        fails.append(f"picture {spec['picture_s']} <= voice+gap {voice:.3f} (-shortest would cut)")
    return fails


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--spec',required=True,type=Path)
    ap.add_argument('--data',required=True,type=Path)
    ap.add_argument('--manifest',required=True,type=Path)
    ap.add_argument('--html',required=True,type=Path)
    a=ap.parse_args()
    for p in [a.spec,a.data,a.manifest,a.html]:
        if not p.exists():
            print(f'REFUSED: missing {p}',file=sys.stderr); return 1
    spec=json.loads(a.spec.read_text(encoding='utf-8'))
    data=json.loads(a.data.read_text(encoding='utf-8'))
    man=json.loads(a.manifest.read_text(encoding='utf-8'))
    html=a.html.read_text(encoding='utf-8',errors='replace')
    fails=check(spec,data,man,html)
    scenes=len(spec.get('scenes',[]))
    if fails:
        print(f'REFUSED: {len(fails)} semantic violation(s):',file=sys.stderr)
        for f in fails: print(f'  - {f}',file=sys.stderr)
        return 1
    print(f'OK: {scenes} scenes bound, {len(spec["stats"])} stats typed, no forbidden labels')
    return 0

if __name__=='__main__': sys.exit(main())
