#!/usr/bin/env python3
"""build_narration.py — concat measured segments, apad to picture, no -shortest."""
from __future__ import annotations
import argparse, json, subprocess
from pathlib import Path

def ffprobe(p,ffmpeg_dir):
    fp=ffmpeg_dir/'ffprobe.exe' if (ffmpeg_dir/'ffprobe.exe').exists() else 'ffprobe'
    r=subprocess.run([str(fp),'-v','error','-show_entries','format=duration',
                      '-of','default=noprint_wrappers=1:nokey=1',str(p)],
                     capture_output=True,text=True,timeout=30)
    return float(r.stdout.strip())

def build(man:dict, here:Path, ffmpeg_dir:Path, picture:float, gap:float=0.18):
    ff=ffmpeg_dir/'ffmpeg.exe' if (ffmpeg_dir/'ffmpeg.exe').exists() else 'ffmpeg'
    voice=man['total_s']+gap*(len(man['segments'])-1)
    print(f'voice+gap={voice:.3f}s picture={picture:.3f}s headroom={picture-voice:.3f}s')
    if picture<=voice:
        raise SystemExit('REFUSED: picture must exceed narration (use -shortest never)')
    lines=[]
    for i,s in enumerate(man['segments']):
        lines.append("file '"+s['file'].replace('\\','/')+"'")
        if i<len(man['segments'])-1:
            g=here/f'gap_{i:02d}.wav'
            subprocess.run([str(ff),'-y','-f','lavfi','-i','anullsrc=r=24000:cl=mono',
                            '-t',str(gap),'-c:a','pcm_s16le',str(g)],capture_output=True,timeout=30)
            lines.append("file '"+str(g).replace('\\','/')+"'")
    (here/'concat.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    subprocess.run([str(ff),'-y','-f','concat','-safe','0','-i',str(here/'concat.txt'),
                    '-c:a','pcm_s16le',str(here/'concat.wav')],capture_output=True,timeout=60)
    subprocess.run([str(ff),'-y','-i',str(here/'concat.wav'),'-af',f'apad=whole_dur={picture}',
                    '-t',str(picture),'-c:a','pcm_s16le',str(here/'padded.wav')],capture_output=True,timeout=60)
    print(f'concat={ffprobe(here/"concat.wav",ffmpeg_dir):.3f}s padded={ffprobe(here/"padded.wav",ffmpeg_dir):.3f}s')
    man['picture_s']=picture; man['voice_total_s']=round(voice,6); man['gap_s']=gap
    (here.parent/'voice-manifest.json').write_text(json.dumps(man,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--manifest',required=True,type=Path)
    ap.add_argument('--here',required=True,type=Path)
    ap.add_argument('--ffmpeg-dir',required=True,type=Path)
    ap.add_argument('--picture',type=float,default=42.0)
    a=ap.parse_args()
    build(json.loads(a.manifest.read_text(encoding='utf-8')),a.here,a.ffmpeg_dir,a.picture)

if __name__=='__main__': main()
