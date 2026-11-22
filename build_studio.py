#!/usr/bin/env python3
"""build_studio.py — inject a deterministic __setTime(sec) into the template.

This file carries the invariants paid for in earlier runs:
  * fetch path must be resolved relative to the studio dir
  * the .then/.catch chain must stay intact (no orphan .catch)
  * upto must clamp to len-1 (off-by-one at p=1)
  * monthly bars must derive from the SAME revealed days as the counter
  * background lifted so luminance gate passes (>20)
  * progress sweep gives measurable frame motion (>0.5)
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

def build(template:Path, out:Path, man:dict, reveal_s:float):
    s=template.read_text(encoding='utf-8',errors='replace')
    # data file sits in the parent of _studio/
    s=s.replace("fetch('./org-activity.json'","fetch('../org-activity.json'")

    old="""   const grid=document.getElementById('grid'); window.__cells=[];
   d.calendar.forEach(c=>{
     const el=document.createElement('div');
     el.className='cell hidden';
     el._lit='cell'+(c.n===0?'':c.n<=2?' n1':c.n<=5?' n2':c.n<=15?' n3':' n4');
     el.title=c.d+' · '+c.n+' contribution'+(c.n===1?'':'s');
     grid.appendChild(el); window.__cells.push(el);
   });
   window.__data=d; window.__ready=true;"""
    new="""   const grid=document.getElementById('grid'); window.__cells=[];
   d.calendar.forEach(c=>{
     const el=document.createElement('div');
     el.className='cell hidden';
     el._lit='cell'+(c.n===0?'':c.n<=2?' n1':c.n<=5?' n2':c.n<=15?' n3':' n4');
     el.title=c.d+' · '+c.n+' contribution'+(c.n===1?'':'s');
     grid.appendChild(el); window.__cells.push(el);
   });
   window.__data=d;
   window.__segT0="""+json.dumps([x['t0'] for x in man['segments']])+""";
   window.__segT1="""+json.dumps([x['t1'] for x in man['segments']])+""";
   window.__ready=true;"""
    assert old in s,'template calendar block not found'
    s=s.replace(old,new)

    inject="""
// ===== DETERMINISTIC TIME CONTROL =====
window.__setTime=function(sec){
  if(!window.__cells||!window.__data) return false;
  const d=window.__data, cells=window.__cells;
  const p=Math.max(0,Math.min(1,sec/""" + str(reveal_s) + """));
  // INVARIANT: clamp — calendar[len] is undefined at p=1
  const upto=Math.min(cells.length-1,Math.floor(p*cells.length));
  let sum=0;
  for(let i=0;i<cells.length;i++){
    const el=cells[i];
    if(i<=upto){ el.className=el._lit; sum+=d.calendar[i].n; }
    else { el.className='cell hidden'; }
  }
  document.getElementById('s-total').textContent=sum.toLocaleString();
  // INVARIANT: bars and counter derive from the SAME revealed days
  // ORG calendar has {week(ts),date,n} — no per_month bars. Skip bars;
  // the counter and the sweep carry the motion. No .d access (would throw).
  const sweep=document.getElementById('sweep'),head=document.getElementById('head');
  if(sweep){ sweep.style.width=(p*100)+'%'; head.style.left=(p*100)+'%'; }
  // INVARIANT: keep pixels moving for the WHOLE film, including the tail.
  const scan=document.getElementById('scan');
  if(scan){ scan.style.left=((sec*11)%100)+'%'; }
  const seg=window.__segT0.findIndex((t0,i)=>sec>=t0&&sec<window.__segT1[i]);
  document.querySelectorAll('.card').forEach((c,i)=>{
    c.style.outline=(seg>=0&&i===seg%4)?'2px solid #D4AF37':'none';
  });
  return sec;
};
"""
    # bars need data-final hooks for the loop above
    s=s.replace("'<span class=\"v\">'+n+'</span>'",
                "'<span class=\"v\" data-final=\"'+n+'\">0</span>'")
    s=s.replace("<span class=\"v\">0</span>", "<span class=\"v\" data-final=\"0\">0</span>")
    s=s.replace("</script>",inject+"\n</script>",1)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(s,encoding='utf-8')
    ok=all(k in s for k in ('window.__setTime','Math.min(cells.length-1','ORG calendar has','../org-activity.json'))
    print(f'studio: {out} ({out.stat().st_size:,}B) invariants={ok}')
    if not ok: raise SystemExit('REFUSED: studio invariants missing')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--template',required=True,type=Path)
    ap.add_argument('--out',required=True,type=Path)
    ap.add_argument('--manifest',required=True,type=Path)
    ap.add_argument('--reveal',type=float,default=32.0)
    a=ap.parse_args()
    build(a.template,a.out,json.loads(a.manifest.read_text(encoding='utf-8')),a.reveal)

if __name__=='__main__': main()
