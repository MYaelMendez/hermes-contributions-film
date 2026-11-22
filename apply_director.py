#!/usr/bin/env python3
"""apply_director.py — inject a scene director from story-spec.json into a studio HTML.

Each narration scene declares which derived stat it proves; the director
highlights that card and dims the others. Driven by the spec, not hardcoded.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path


LEGACY = {'commits':'s-total', 'active':'s-active', 'weeks':'s-weeks', 'peak':'s-max'}

def _legacy_id(stat_id):
    # the template's fetch writes to s-total/s-active/s-weeks/s-max.
    # Keep those ids present so the derived data still populates the cards.
    lid = LEGACY.get(stat_id)
    return f' id="{lid}"' if lid else ''

DIRECTOR = """
// ===== SCENE DIRECTOR (generated from story-spec.json) =====
window.__SCENES=__SCENES__;
window.__scene=-1;
window.__setScene=function(sec){
  let idx=-1;
  for(let i=0;i<window.__SCENES.length;i++){
    const x=window.__SCENES[i];
    if(sec>=x.t0 && sec<x.t1){idx=i;break;}
  }
  if(idx===window.__scene) return idx;
  window.__scene=idx;
  document.querySelectorAll('#directed-stats .card[data-stat]').forEach((c)=>{
    const focus=idx>=0?window.__SCENES[idx].focus:'';
    const active=(focus==='stat:'+c.getAttribute('data-stat'));
    c.style.outline=active?'2px solid #D4AF37':'1px solid #2b4a66';
    c.style.boxShadow=active?'0 0 30px rgba(212,175,55,0.35)':'';
    c.style.opacity=(idx>=0&&!active&&focus.indexOf('stat:')===0)?'0.55':'1';
    c.style.transition='opacity 0.35s, outline 0.35s, box-shadow 0.35s';
  });
  const t=document.getElementById('scene-title');
  if(t&&idx>=0) t.textContent=window.__SCENES[idx].id.toUpperCase().replace(/_/g,' ');
  return idx;
};
"""

def apply(studio: Path, spec: Path, out: Path):
    s=studio.read_text(encoding='utf-8',errors='replace')
    d=json.loads(spec.read_text(encoding='utf-8'))
    scenes=json.dumps([{'id':x['id'],'focus':x['focus'],'t0':x['t0'],'t1':x['t1'],'voice':x['voice']}
                       for x in d['scenes']])
    cards='\n'.join(
      f'    <div class="card" data-stat="{st["id"]}"><div class="label">{st["label"]}</div>'
      f'<div class="value" id="o-{st["id"]}">—</div></div>' for st in d['stats'])
    block=f'  <div class="stats" id="directed-stats" style="margin-top:18px">\n{cards}\n  </div>\n'
    # the directed row REPLACES the ENTIRE original .stats block (no duplicates).
    # The template's first .stats block holds 4 cards; remove through its closing tag.
    start=s.find('  <div class="stats">')
    if start<0: raise SystemExit('REFUSED: no .stats block to replace')
    depth=0; end=-1
    for i in range(start,len(s)):
        if s.startswith('<div',i): depth+=1
        if s.startswith('</div>',i):
            depth-=1
            if depth==0: end=i+len('</div>'); break
    if end<0: raise SystemExit('REFUSED: unbalanced .stats block')
    s=s[:start]+block.strip()+s[end:]
    pop='\n'.join(
      f"   document.getElementById('o-{st['id']}').textContent=d.{st['source']}.toLocaleString();"
      for st in d['stats'])
    # the template's fetch writes to s-total/s-active/s-weeks/s-max.
    # Redirect those writes to our directed card ids so no null.textContent.
    for legacy,stat in [('s-total','commits'),('s-active','active'),('s-weeks','weeks'),('s-max','peak')]:
        s=s.replace(f"getElementById('{legacy}')", f"getElementById('o-{stat}')")
    s=s.replace('   window.__data=d;',pop+'\n   window.__data=d;')
    s=s.replace('<div class="status" id="status">LOADING…</div>',
      '<div class="status" id="status">LOADING…</div>\n'
      '<div id="scene-title" style="font-size:10px;color:#D4AF37;letter-spacing:.18em;margin-top:6px">—</div>')
    for st in d['stats']:
        s=s.replace(f'<div class="label">{st["label"]}</div>',
                    f'<div class="label" data-stat="{st["id"]}">{st["label"]}</div>')
    s=s.replace('  const seg=window.__segT0.findIndex',
                '  if(window.__setScene) window.__setScene(sec);\n  const seg=window.__segT0.findIndex')
    s=s.replace('</script>',DIRECTOR.replace('__SCENES__',scenes)+'\n</script>',1)
    ok=all(k in s for k in ('window.__setTime=function','window.__setScene=function',
                            'data-stat="stars"','scene-title'))
    if not ok: raise SystemExit('REFUSED: director injection incomplete')
    out.write_text(s,encoding='utf-8')
    print(f'director applied: {out} ({out.stat().st_size:,}B, {len(d["scenes"])} scenes)')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--studio',required=True,type=Path)
    ap.add_argument('--spec',required=True,type=Path)
    ap.add_argument('--out',required=True,type=Path)
    a=ap.parse_args()
    apply(a.studio,a.spec,a.out)

if __name__=='__main__': main()
