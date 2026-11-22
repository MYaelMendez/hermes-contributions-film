#!/usr/bin/env python3
"""run.py — ONE COMMAND: GitHub account -> verified contribution film.

    python run.py --repo NousResearch/hermes-agent --out ./mi-film
    python run.py --repo NousResearch/hermes-agent --out ./smoke --quick

Everything is derived. Nothing is typed by hand. No credential is written.
"""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path

HERE=Path(__file__).resolve().parent

def sh(args,**kw):
    return subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace',**kw)

def need(cmd:str)->str:
    p=shutil.which(cmd)
    if not p: raise SystemExit(f'MISSING: {cmd} — install it, then rerun')
    return p

def find_ffmpeg(explicit:str|None):
    if explicit:
        p=Path(explicit)
        if not (p/'ffmpeg.exe').exists() and not (p/'ffmpeg').exists():
            raise SystemExit(f'MISSING: ffmpeg in {p}')
        return p
    cands=[Path(r'C:/Users/yaelm/AppData/Local/hermes/tools/ffmpeg-7.1-nvenc/bin'),
           Path('/usr/bin')]
    for c in cands:
        if (c/'ffmpeg.exe').exists() or (c/'ffmpeg').exists(): return c
    w=shutil.which('ffmpeg')
    if w: return Path(w).parent
    raise SystemExit('MISSING: ffmpeg — pass --ffmpeg-dir DIR')


def _tinyffmpeg_gate(path):
    """Bind the artifact to the build that encoded it (tinyffmpeg.integrate).
    Fail-closed: a file that exists is not an encode."""
    try:
        import importlib.util
        p = Path(r"C:\æ\tinyffmpeg\integrate.py")
        if not p.exists():
            return {"ok": False, "refusal": "tinyffmpeg.integrate no encontrado"}
        spec = importlib.util.spec_from_file_location("tinyffmpeg_integrate", p)
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        return m.gate(path)
    except Exception as e:
        return {"ok": False, "refusal": f"{type(e).__name__}: {e}"}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--repo',required=True,help='owner/repo, e.g. NousResearch/hermes-agent')
    ap.add_argument('--out',required=True,type=Path)
    ap.add_argument('--quick',action='store_true')
    ap.add_argument('--encoder',choices=['auto','nvenc','x264'],default='auto')
    ap.add_argument('--ffmpeg-dir',default=None)
    ap.add_argument('--voice-lab',default=os.environ.get('VOICE_LAB','C:/æ/osw-voice-lab'))
    ap.add_argument('--voice-python',default=None,help='python with dizione + onnxruntime')
    ap.add_argument('--gate-python',default=None,help='python with vision_supervision installed; omit = gate SKIPPED (reported, never faked PASS)')
    ap.add_argument('--port',type=int,default=0,help='0 = auto free port')
    a=ap.parse_args()

    need('gh'); node=need('node')
    chrome_bin=shutil.which('chrome')
    for c in [r'C:/Program Files/Google/Chrome/Application/chrome.exe',
              r'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
              r'C:/Program Files/Chromium/Application/chrome.exe']:
        if Path(c).exists(): chrome_bin=c; break
    if not chrome_bin: raise SystemExit('MISSING: chrome/chromium — install it or add to PATH')
    ffdir=find_ffmpeg(a.ffmpeg_dir)
    # Voice needs dizione/onnxruntime; the default python often lacks them.
    # Let VOICE_PYTHON point at the interpreter that has them (C:/gpu on Victus).
    PY_VOICE=a.voice_python or os.environ.get('VOICE_PYTHON') or PY
    ffmpeg=ffdir/'ffmpeg.exe' if (ffdir/'ffmpeg.exe').exists() else ffdir/'ffmpeg'
    out=a.out.resolve(); out.mkdir(parents=True,exist_ok=True)
    work=out/'work'; work.mkdir(exist_ok=True)
    PY=sys.executable

    # 1. derived calendar
    data=work/'org-activity.json'
    r=sh([PY,str(HERE/'gen_org_activity.py'),'--repo',a.repo,'--out',str(data)])
    if r.returncode: raise SystemExit(r.stdout+r.stderr)
    print(r.stdout.strip())

    # 2. deterministic voice + narration
    vdir=work/'voice'
    cmd=[PY_VOICE,str(HERE/'make_voice.py'),'--data',str(data),'--out',str(vdir),
         '--voice-lab',a.voice_lab]
    if a.quick: cmd.append('--quick')
    r=sh(cmd); 
    if r.returncode: raise SystemExit(r.stdout+r.stderr)
    print(r.stdout.strip())
    man=json.loads((work/'voice-manifest.json').read_text(encoding='utf-8'))
    fps=24
    voice=man['total_s']+0.18*(len(man['segments'])-1)
    picture=round(voice+2.5,3) if a.quick else 42.0
    total=round(picture*fps)
    r=sh([PY,str(HERE/'build_narration.py'),'--manifest',str(work/'voice-manifest.json'),
          '--here',str(vdir),'--ffmpeg-dir',str(ffdir),'--picture',str(picture)])
    if r.returncode: raise SystemExit(r.stdout+r.stderr)
    print(r.stdout.strip())

    # 3. studio html (deterministic)
    studio=work/'studio.html'
    r=sh([PY,str(HERE/'build_studio.py'),'--template',str(HERE/'contributions.html'),
          '--out',str(studio),'--manifest',str(work/'voice-manifest.json'),
          '--reveal',str(picture)])
    if r.returncode: raise SystemExit(r.stdout+r.stderr)
    print(r.stdout.strip())

    # 4. local HTTP server (fetch needs HTTP, not file://)
    port=a.port or 8200+int(time.time())%600
    srv=subprocess.Popen([PY,'-m','http.server',str(port)],cwd=str(work),
                         stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    chrome=None; userdir=None
    try:
        for _ in range(20):
            try:
                urllib.request.urlopen(f'http://127.0.0.1:{port}/studio.html',timeout=2); break
            except Exception: time.sleep(0.25)
        else: raise SystemExit('HTTP server did not start')

        # 5. Chrome headless with GPU (never --disable-gpu)
        userdir=tempfile.mkdtemp(prefix='cf-chrome-')
        chrome=subprocess.Popen([
          chrome_bin,'--headless=new','--force_high_performance_gpu','--use-angle=d3d11',
          '--remote-debugging-port=9333','--window-size=1920,1080','--no-first-run',
          '--no-default-browser-check','--disable-extensions',
          f'--user-data-dir={userdir}','about:blank'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        for _ in range(20):
            try:
                urllib.request.urlopen('http://127.0.0.1:9333/json',timeout=2); break
            except Exception: time.sleep(0.5)
        else: raise SystemExit('CDP did not start')

        # 6. capture (script asserts frame count)
        env=os.environ.copy(); env.update({
          'PAGE_URL':f'http://127.0.0.1:{port}/studio.html','FRAMES':str(work/'frames'),
          'TOTAL_FRAMES':str(total),'FPS':str(fps),'WIDTH':'1920','HEIGHT':'1080'})
        r=sh([node,str(HERE/'render.mjs')],env=env,timeout=1800)
        print(r.stdout.strip())
        if r.returncode: raise SystemExit(r.stderr[-1000:])

        # 7. encode + mux (never -shortest)
        codec='h264_nvenc' if a.encoder in ('auto','nvenc') else 'libx264'
        silent=work/'silent.mp4'
        enc=[str(ffmpeg),'-y','-framerate',str(fps),'-i',str(work/'frames/frame_%05d.png'),
             '-c:v',codec,'-b:v','6M' if codec=='h264_nvenc' else '4M',
             '-pix_fmt','yuv420p','-movflags','+faststart',str(silent)]
        r=sh(enc,timeout=900)
        if r.returncode: raise SystemExit(r.stderr[-800:])
        final=out/f'{a.repo.split("/")[-1]}-activity.mp4'
        r=sh([str(ffmpeg),'-y','-i',str(silent),'-i',str(vdir/'padded.wav'),
              '-c:v','copy','-c:a','aac','-b:a','128k','-t',str(picture),str(final)],timeout=600)
        if r.returncode: raise SystemExit(r.stderr[-800:])
    finally:
        if chrome: chrome.terminate()
        srv.terminate()
        if userdir: shutil.rmtree(userdir,ignore_errors=True)

    # 8. proof + receipt. Gate is HONEST: skipped is reported, never PASS.
    b=final.read_bytes()
    gate={'status':'SKIPPED','reason':'no --gate-python supplied; no pass claimed'}
    if a.gate_python:
        r=sh([a.gate_python,str(Path(r'C:/æ/vidæo/vidæo.py')),'verify',str(final)],timeout=300)
        gate={'status':'PASS' if 'PASS' in (r.stdout+r.stderr) else 'FAIL','raw':(r.stdout+r.stderr)[:600]}
    rec={'artifact':final.name,'sha256':hashlib.sha256(b).hexdigest(),
         'codec_gate':_tinyffmpeg_gate(final),
         'source':'contributions-film #opensourceware · derived from GitHub GraphQL',
         'repo':a.repo,'voice':{'engine':'tiny-voca','seed':42,'segments':len(man['segments'])},
         'picture':{'fps':fps,'duration_s':picture,'frames':total,'codec':codec},
         'seam':{'apad':True,'shortest':False},'gate':gate,
         'credential_leak':bool(__import__('re').search(r'gh[pous]_[A-Za-z0-9]{10,}|Bearer\s+\S+',b.decode('utf-8','replace')))}
    rp=out/'receipt.json'; rp.write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f'DONE {final} ({len(b):,}B) gate={gate["status"]} receipt={rp}')

if __name__=='__main__': main()
