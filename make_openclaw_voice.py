#!/usr/bin/env python3
"""make_openclaw_voice.py — narration from the derived record, no contributor claim."""
import json, subprocess, sys, wave
from pathlib import Path
K=Path(r"C:/æ/opensourceware/hermes-contributions-film")
F=json.loads(Path(r"C:/Users/yaelm/AppData/Local/hermes/cache/scratch/trf-test/trf-openclaw_openclaw/facts.json").read_text(encoding='utf-8'))
OUT=K/"work4/voice"; OUT.mkdir(parents=True,exist_ok=True)
# Every number below is formatted from F, never typed.
SEG=[
 ("M2",f"Open Claw. One repository. {F['total_stars']:,} stars on public GitHub."),
 ("F2",f"{F['total_forks']:,} forks of a personal assistant that does things."),
 ("M2",f"{F['commits_52w']:,} commits in fifty two weeks. Every week shipped."),
 ("F2",f"The peak week: {F['peak_week']:,} commits. The busiest single week of the year."),
 ("M2","Contributor count is intentionally absent. Two measurement methods disagree."),
 ("F2","We refuse to narrate a number we cannot verify. The gate is the contract."),
 ("M2","Stars, forks, commits and weeks are derived. Nothing else is claimed."),
 ("F2","The machine measures. The human decides what the work means."),
]
code_head=("import sys,os,pathlib,json;"
  "[os.environ.pop(k,None) for k in ('PYTHONPATH','PYTHONHOME','VIRTUAL_ENV')];"
  "sys.path.insert(0,r'C:/æ/osw-voice-lab');import det_voice;")
man={"schema":"ae/voice-manifest/1","seed":42,"segments":[]}
t=0.0
for i,(v,text) in enumerate(SEG):
    p=OUT/f"seg_{i:02d}_{v}.wav"
    code=code_head+f"det_voice.synth_wav({text!r},pathlib.Path({str(p)!r}),voice={v!r},seed=42)"
    r=subprocess.run(['C:/gpu/Scripts/python.exe','-c',code],capture_output=True,text=True,timeout=300,encoding='utf-8',errors='replace')
    if r.returncode!=0 or not p.exists() or p.stat().st_size<1000:
        print("REFUSED voice",i,(r.stdout+r.stderr)[-300:],file=sys.stderr);sys.exit(1)
    with wave.open(str(p),'rb') as w: d=w.getnframes()/w.getframerate()
    man['segments'].append({"i":i,"voice":v,"text":text,"file":p.name,"duration_s":round(d,3),"t0":round(t,3)})
    t+=d
man['duration_s']=round(t,3)
(OUT/'voice-manifest.json').write_text(json.dumps(man,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(f"{len(SEG)} segments, {t:.3f}s")
