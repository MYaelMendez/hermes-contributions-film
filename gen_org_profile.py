#!/usr/bin/env python3
"""gen_org_profile.py — derive an org-wide OSS profile from PUBLIC GitHub REST.

Unlike a single repo, an organization's story is the sum of its repos. This
aggregates contributors (via Link header per repo), stars/forks, and weekly
commit activity into one derived record with a --check gate.

    python gen_org_profile.py --org menloresearch --out menlo-profile.json
    python gen_org_profile.py --org menloresearch --out ... --check
"""
from __future__ import annotations
import argparse, json, os, re, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

UA={'User-Agent':'Mozilla/5.0','Accept':'application/vnd.github+json'}

def get(url):
    # gh CLI is authenticated (5000 req/h) vs urllib anonymous (60/h).
    # Parse the API path and let gh handle auth, headers and rate limits.
    path=url.replace('https://api.github.com','')
    r=subprocess.run(['gh','api',path],capture_output=True,text=True,
                     timeout=60,encoding='utf-8',errors='replace',env=os.environ.copy())
    if r.returncode!=0:
        raise RuntimeError('gh api failed '+path+': '+(r.stderr or r.stdout)[:150])
    # gh returns body only; contributors() paginates explicitly instead
    class H(dict):
        def get(self,k,default=None): return dict.get(self,k,default)
    return json.loads(r.stdout), H()


def contributors(repo):
    # full list with anon=true, paginated by gh; count distinct logins/ids
    all_c=[]
    for page in range(1,6):
        path=f"/repos/{repo}/contributors?per_page=100&page={page}&anon=true"
        r=subprocess.run(['gh','api',path],capture_output=True,text=True,
                         timeout=60,encoding='utf-8',errors='replace',env=os.environ.copy())
        if r.returncode!=0: break
        chunk=json.loads(r.stdout)
        if not isinstance(chunk,list) or not chunk: break
        all_c.extend(chunk)
        if len(chunk)<100: break
    return len({c.get('id') or c.get('login') for c in all_c})

def activity(repo):
    url=f"https://api.github.com/repos/{repo}/stats/commit_activity"
    for i in range(5):
        d,_=get(url)
        if isinstance(d,list) and d: return d
        time.sleep(2)
    return []

def derive(org: str) -> dict:
    meta,_=get(f"https://api.github.com/orgs/{org}")
    repos,_=get(f"https://api.github.com/orgs/{org}/repos?per_page=100&sort=updated")
    total_stars=sum(r['stargazers_count'] for r in repos)
    total_forks=sum(r['forks_count'] for r in repos)
    weeks=[0]*52
    repo_detail=[]
    contrib_sum=0
    for r in repos:
        full=r['full_name']
        nc=contributors(full)
        contrib_sum+=nc
        act=activity(full)
        for i,w in enumerate(act[:52]):
            weeks[i]+=w.get('total',0)
        repo_detail.append({'name':r['name'],'stars':r['stargazers_count'],
          'forks':r['forks_count'],'contributors':nc,'commits_52w':sum(w.get('total',0) for w in act)})
    peak=max(weeks) if weeks else 0
    return {
      'schema':'ae/github-org-profile/1',
      'source':'GitHub REST public: orgs, repos, contributors, stats/commit_activity',
      'org':org,'derived_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),
      'public_repos':len(repos),'followers':meta.get('followers',0),
      'total_stars':total_stars,'total_forks':total_forks,
      'contributor_sum':contrib_sum,
      'commits_52w':sum(weeks),'active_weeks':sum(1 for w in weeks if w>0),
      'peak_week':peak,'weeks':52,
      'calendar':[{'i':i,'n':w} for i,w in enumerate(weeks)],
      'repos':sorted(repo_detail,key=lambda x:x['stars'],reverse=True),
      'note':'Derived from public REST. contributor_sum is per-repo (may double-count).',
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--org',required=True)
    ap.add_argument('--out',required=True,type=Path)
    ap.add_argument('--check',action='store_true')
    a=ap.parse_args()
    new=derive(a.org)
    if a.check:
        if not a.out.exists(): print('MISSING: '+str(a.out),file=sys.stderr); return 1
        cur=json.loads(a.out.read_text(encoding='utf-8'))
        keys=[k for k in new if k!='derived_at']
        if any(cur.get(k)!=new[k] for k in keys):
            print('STALE: differs from GitHub — regenerate',file=sys.stderr); return 1
        print(f"OK current: repos={new['public_repos']} stars={new['total_stars']} commits={new['commits_52w']}")
        return 0
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(new,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f"wrote {a.out}: repos={new['public_repos']} stars={new['total_stars']:,} "
          f"forks={new['total_forks']:,} contributors(sum)={new['contributor_sum']:,} "
          f"commits/52w={new['commits_52w']:,} active_weeks={new['active_weeks']}/52")
    return 0

if __name__=='__main__': sys.exit(main())
