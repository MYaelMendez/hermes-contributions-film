#!/usr/bin/env python3
"""gen_org_activity.py — derive a repo's PUBLIC activity into a 52-week calendar.

An Organization has no `contributionsCollection` in GitHub GraphQL (verified:
`undefinedField` on type Organization). The honest source for a leading OSS
project is REST `stats/commit_activity` + the contributors list.

    python gen_org_activity.py --repo NousResearch/hermes-agent --out org-activity.json
    python gen_org_activity.py --repo ... --out ... --check

No credential is written. Only public aggregate data. Contributors are counted
from the Link header's `last` page (the exact count, not an estimate).
"""
from __future__ import annotations
import argparse, json, os, re, subprocess, sys, urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

UA={'User-Agent':'Mozilla/5.0','Accept':'application/vnd.github+json'}

def get(url:str):
    req=urllib.request.Request(url,headers=UA)
    with urllib.request.urlopen(req,timeout=45) as r:
        return json.loads(r.read()), r.headers

def contributor_count(repo:str)->int:
    url=f"https://api.github.com/repos/{repo}/contributors?per_page=1&anon=true"
    _,h=get(url)
    link=h.get('Link','')
    m=re.search(r'[?&]page=(\d+)>;\s*rel="last"',link)
    if m: return int(m.group(1))
    d,_=get(url)
    return len(d)

def derive(repo:str)->dict:
    act,_=get(f"https://api.github.com/repos/{repo}/stats/commit_activity")
    part,_=get(f"https://api.github.com/repos/{repo}/stats/participation")
    meta,_=get(f"https://api.github.com/repos/{repo}")
    ncontrib=contributor_count(repo)
    weeks=[{'week':w['week'],'n':w['total'],
            'date':datetime.fromtimestamp(w['week'],tz=timezone.utc).date().isoformat()} for w in act]
    total=sum(w['n'] for w in weeks)
    active=sum(1 for w in weeks if w['n']>0)
    peak=max(weeks,key=lambda w:w['n']) if weeks else {'n':0,'date':None}
    owner=part.get('owner',[])
    community=sum(part.get('all',[])[-12:])-sum(owner[-12:]) if owner else 0
    return {
      'schema':'ae/github-org-activity/1',
      'source':'GitHub REST public stats/commit_activity + contributors (Organization: no contributionsCollection)',
      'repo':repo,
      'derived_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),
      'total_commits':total,'weeks':len(weeks),'active_weeks':active,
      'peak_week':peak['n'],'peak_date':peak['date'],
      'contributors':ncontrib,
      'stars':meta['stargazers_count'],'forks':meta['forks_count'],
      'community_last12':community,
      'owner_last12':sum(owner[-12:]) if owner else 0,
      'calendar':weeks,
      'note':'Derived from public REST. No credential stored. Community commits = all - owner (last 12 weeks).',
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--repo',required=True)
    ap.add_argument('--out',required=True,type=Path)
    ap.add_argument('--check',action='store_true')
    a=ap.parse_args()
    new=derive(a.repo)
    if a.check:
        if not a.out.exists(): print('MISSING: '+str(a.out),file=sys.stderr);return 1
        cur=json.loads(a.out.read_text(encoding='utf-8'))
        keys=[k for k in new if k!='derived_at']
        if any(cur.get(k)!=new[k] for k in keys):
            print('STALE: differs from GitHub — regenerate',file=sys.stderr);return 1
        print(f"OK current: commits={new['total_commits']} contributors={new['contributors']}");return 0
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(new,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f"wrote {a.out}: commits={new['total_commits']:,} weeks={new['weeks']} "
          f"contributors={new['contributors']:,} stars={new['stars']:,} forks={new['forks']:,}")
    return 0

if __name__=='__main__': sys.exit(main())
