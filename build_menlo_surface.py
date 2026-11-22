#!/usr/bin/env python3
"""build_menlo_surface.py — derive a gold-on-void org surface from menlo-profile.json.

One surface, one responsibility: present ONLY derived numbers. No hardcoded
claims, no decorative stats. Drift is visible, never hidden.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

def build(d: dict) -> str:
    weeks=d['calendar']
    peak=max(w['n'] for w in weeks) or 1
    bars=''.join(
      f'<div class="bar" style="height:{max(2,round(w["n"]/peak*100))}%" '
      f'title="week {w["i"]+1}: {w["n"]} commits"></div>' for w in weeks)
    months=''.join(
      f'<div class="mrow"><span class="mlab">w{w["i"]+1:02d}</span>'
      f'<div class="mbar" style="width:{round(w["n"]/peak*100)}%"></div>'
      f'<span class="mval">{w["n"]}</span></div>'
      for w in sorted(weeks,key=lambda x:x['n'],reverse=True)[:6])
    repos=''.join(
      f'<div class="repo"><span class="rname">{r["name"]}</span>'
      f'<span class="rstars">★{r["stars"]:,}</span>'
      f'<span class="rc">⑂{r["forks"]:,} · {r["contributors"]} contributors</span></div>'
      for r in d['repos'][:8])
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>æ:// MENLO RESEARCH · derived</title>
<style>
:root{{--gold:#D4AF37;--void:#050505;--dim:#8a8577;--line:#1f1e1a}}
*{{box-sizing:border-box}}html,body{{margin:0;background:var(--void);color:#e8e4d8;
font-family:'JetBrains Mono',ui-monospace,monospace;padding:26px 34px}}
h1{{font-size:24px;letter-spacing:.12em;margin:0 0 3px;color:var(--gold);font-weight:600}}
.tag{{color:var(--dim);font-size:12px;letter-spacing:.05em;margin-bottom:14px}}
.grid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:14px 0 20px}}
.kpi{{border:1px solid var(--line);padding:12px 14px}}
.kpi .k{{font-size:10px;color:var(--dim);letter-spacing:.16em}}
.kpi .v{{font-size:26px;color:var(--gold);margin-top:4px}}
.panel{{border:1px solid var(--line);padding:12px 14px;margin-bottom:14px}}
h3{{font-size:11px;color:var(--dim);letter-spacing:.16em;margin:0 0 12px;font-weight:500}}
.bars{{display:flex;gap:2px;height:80px;align-items:flex-end}}
.bar{{flex:1;background:linear-gradient(180deg,var(--gold),#6b5718);min-height:2px}}
.mrow{{display:flex;align-items:center;gap:10px;margin:6px 0;font-size:11px}}
.mlab{{width:34px;color:var(--dim)}}.mbar{{height:9px;background:var(--gold)}}
.mval{{color:var(--gold);width:40px;text-align:right}}
.repo{{display:grid;grid-template-columns:1fr auto auto;gap:14px;font-size:12px;padding:4px 0;border-bottom:1px solid var(--line)}}
.rname{{color:#e8e4d8}}.rstars{{color:var(--gold)}}.rc{{color:var(--dim)}}
.foot{{font-size:10px;color:var(--dim);margin-top:16px;letter-spacing:.06em}}
</style></head><body>
<h1>æ:// MENLO RESEARCH</h1>
<div class="tag" id="sub">{d['source']} · derived · {d['derived_at']}</div>
<div class="grid">
 <div class="kpi"><div class="k">PUBLIC REPOS</div><div class="v" id="s-repos">{d['public_repos']:,}</div></div>
 <div class="kpi"><div class="k">TOTAL STARS</div><div class="v" id="s-stars">{d['total_stars']:,}</div></div>
 <div class="kpi"><div class="k">CONTRIBUTORS (sum)</div><div class="v" id="s-contributors">{d['contributor_sum']:,}</div></div>
 <div class="kpi"><div class="k">COMMITS / 52W</div><div class="v" id="s-commits">{d['commits_52w']:,}</div></div>
</div>
<div class="panel"><h3>WEEKLY COMMITS · {d['active_weeks']}/52 ACTIVE · PEAK {d['peak_week']}</h3>
 <div class="bars" id="bars">{bars}</div></div>
<div class="panel"><h3>PEAK WEEKS</h3>{months}</div>
<div class="panel"><h3>TOP REPOS · {d['total_forks']:,} TOTAL FORKS · {d['followers']:,} FOLLOWERS</h3>{repos}</div>
<div class="foot" id="foot">SCHEMA {d['schema']} · {d['note']}</div>
<script>window.__setTime=function(){{}};window.__ready=true;</script>
</body></html>'''

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--data',required=True,type=Path)
    ap.add_argument('--out',required=True,type=Path)
    a=ap.parse_args()
    d=json.loads(a.data.read_text(encoding='utf-8'))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(build(d),encoding='utf-8')
    print(f"wrote {a.out}: {a.out.stat().st_size:,}B")
    return 0

if __name__=='__main__': sys.exit(main())
