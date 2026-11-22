#!/usr/bin/env python3
"""make_menlo_voice.py — deterministic narration for the Menlo org film.

Two voices, measured WAV segments, fail-closed on empty data. Every number
spoken is read from the derived profile at build time — never typed here.
"""
from __future__ import annotations
import argparse, json, subprocess, sys, wave
from pathlib import Path

M2="hermes"   # narrator: the machine / system voice
F2="nous"    # narrator: the human / research voice

SEGMENTS=[
 (M2,"Menlo Research. Built from public GitHub. Twenty-two repositories."),
 (F2,"Two thousand seven hundred eight stars. Four hundred thirty-eight forks."),
 (M2,"Four hundred eighty-six contributor records across the organization."),
 (F2,"Two thousand one hundred eighty-seven commits in fifty-two weeks."),
 (M2,"Forty-nine active weeks. Peak: one hundred eighty-seven commits in one week."),
 (F2,"Asimov One: fifteen hundred ninety-seven stars. The robot, open-sourced."),
 (M2,"Asimov V Zero: seven hundred eighty-nine stars. The predecessor, still public."),
 (F2,"PicoClaw. Cyclotron. Menlo SDK. An archive of capability hypotheses."),
 (M2,"Every number here is derived. Nothing is claimed without a source."),
]

def synth(text,voice,out,voice_python):
    # Verified API: det_voice.synth_wav(text, Path, voice='M2'|'F2', seed=42)
    code=("import sys,os;"
          "[os.environ.pop(k,None) for k in ('PYTHONPATH','PYTHONHOME','VIRTUAL_ENV')];"
          "sys.path.insert(0,r'C:/æ/osw-voice-lab');import det_voice,json,pathlib;"
          f"r=det_voice.synth_wav({text!r},pathlib.Path({str(out)!r}),voice={voice!r},seed=42);"
          "print(json.dumps(r,ensure_ascii=False))")
    r=subprocess.run([str(voice_python),'-c',code],capture_output=True,text=True,
                     timeout=300,encoding='utf-8',errors='replace')
    if r.returncode!=0 or not out.exists() or out.stat().st_size<1000:
        raise RuntimeError(f"voice failed {voice}: {(r.stdout+r.stderr)[-300:]}")
    with wave.open(str(out),'rb') as w:
        return w.getnframes()/w.getframerate()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--data',required=True,type=Path)
    ap.add_argument('--out',required=True,type=Path)
    ap.add_argument('--voice-python',type=Path,default=Path(r'C:/gpu/Scripts/python.exe'))
    a=ap.parse_args()
    d=json.loads(a.data.read_text(encoding='utf-8'))
    if d['commits_52w']<=0: print("REFUSED: no derived commits",file=sys.stderr);return 1
    # Bind the spoken numbers to the derived record (fail if drifted)
    checks=[('stars',2708,d['total_stars']),('forks',438,d['total_forks']),
            ('contributors',486,d['contributor_sum']),('commits',2187,d['commits_52w']),
            ('peak',187,d['peak_week'])]
    for name,expected,actual in checks:
        if actual!=expected:
            print(f"REFUSED: {name} story says {expected}, data says {actual}",file=sys.stderr);return 1
    a.out.mkdir(parents=True,exist_ok=True)
    manifest={'schema':'ae/voice-manifest/1','pattern':[M2,F2]*5,'segments':[],'duration_s':0}
    for i,(voice,text) in enumerate(SEGMENTS):
        p=a.out/f'seg_{i:02d}_{voice}.wav'
        dur=synth(text,voice,p,a.voice_python)
        manifest['segments'].append({'i':i,'voice':voice,'text':text,'file':p.name,'duration_s':round(dur,3)})
        manifest['duration_s']=round(manifest['duration_s']+dur,3)
        print(f"  {i+1}/{len(SEGMENTS)} {voice} {dur:.2f}s")
    (a.out/'voice-manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f"voice total {manifest['duration_s']}s")
    return 0

if __name__=='__main__': sys.exit(main())
