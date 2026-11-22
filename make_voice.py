#!/usr/bin/env python3
"""make_voice.py — narrate the org's derived activity with deterministic tiny-voca.

Every number comes from org-activity.json. The story: a leading OSS project
where the OWNER wrote zero commits in the last 12 weeks — the community did.
"""
from __future__ import annotations
import argparse, json, os, sys, wave
from pathlib import Path
for k in ('PYTHONPATH','PYTHONHOME','VIRTUAL_ENV'): os.environ.pop(k,None)

def emit(segs,outdir,voice,seed):
    import det_voice
    outdir.mkdir(parents=True,exist_ok=True)
    meta={'schema':'ae/hermes-film/voice/1','voice':voice,'seed':seed,'segments':[]}
    t0=0.0
    for i,text in enumerate(segs):
        p=outdir/f'seg_{i:02d}.wav'
        r=det_voice.synth_wav(text,p,voice=voice,seed=seed)
        with wave.open(str(p),'rb') as w: dur=w.getnframes()/w.getframerate()
        meta['segments'].append({'index':i,'text':text,'file':str(p),
          'measured_s':round(dur,6),'t0':round(t0,6),'t1':round(t0+dur,6),
          'pcm_sha256':r['pcm_sha256'],'receipt':r['receipt']})
        t0+=dur
    meta['total_s']=round(t0,6)
    mp=outdir.parent/'voice-manifest.json'
    mp.write_text(json.dumps(meta,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f'voice: {len(segs)} segments, {t0:.3f}s -> {mp}')

def build(data,outdir,voice,seed,lab,quick=False):
    sys.path.insert(0,str(lab)); import det_voice
    segs=[
      "This is Hermes Agent. One of the most starred open source projects on GitHub.",
      f"{data['stars']:,} stars. {data['forks']:,} forks. {data['contributors']:,} contributors.",
      f"In the last fifty two weeks: {data['total_commits']:,} commits across {data['active_weeks']} active weeks.",
      f"The busiest week: {data['peak_week']:,} commits, starting {data['peak_date']}.",
      f"And here is the proof it is truly open: {data['community_last12']:,} community commits in the last twelve weeks.",
      f"The owner wrote {data['owner_last12']} commits in that same period. The community carried the work.",
      "One human starts a project. Thousands of agents and people make it a standard. That is open source at global scale.",
    ]
    if quick: segs=segs[:2]
    return emit(segs,outdir,voice,seed)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--data',required=True,type=Path)
    ap.add_argument('--out',required=True,type=Path)
    ap.add_argument('--voice',default='hermes')
    ap.add_argument('--seed',type=int,default=42)
    ap.add_argument('--voice-lab',default=os.environ.get('VOICE_LAB','C:/æ/osw-voice-lab'),type=Path)
    ap.add_argument('--quick',action='store_true')
    a=ap.parse_args()
    build(json.loads(a.data.read_text(encoding='utf-8')),a.out,a.voice,a.seed,a.voice_lab,a.quick)

if __name__=='__main__': main()
