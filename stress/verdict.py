"""15-case E2E acceptance gate; source/currentness verification is mandatory.

A pure JSON review NEVER yields a release PASS without real GitHub GET checks.
This gate is deliberately stricter than merely counting claimed PASS statuses.
"""
from __future__ import annotations
import argparse,json,pathlib,re,subprocess,sys,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
SHA=re.compile(r'^[0-9a-f]{40}$')
RUN=re.compile(r'^https://github\.com/([^/]+/[^/]+)/actions/runs/([1-9][0-9]*)$')
COMMENT=re.compile(r'^https://github\.com/([^/]+/[^/]+)/issues/([1-9][0-9]*)#issuecomment-([1-9][0-9]*)$')

def gh(path):
    p=subprocess.run(['gh','api',path],text=True,capture_output=True,check=False)
    if p.returncode:raise RuntimeError('provider readback failed: '+p.stderr[:180])
    return json.loads(p.stdout)

def evaluate(matrix:dict,observed:dict,*,live:bool=False,repo:str=''):
    expected={x['id'] for x in matrix['scenarios']}
    spec={x['id']:x['expect'] for x in matrix['scenarios']}
    rows=observed.get('scenarios')
    if not isinstance(rows,list):return {'status':'BLOCKED_MISSING_SCENARIOS','errors':['observations must be scenarios array']}
    ids=[x.get('id') for x in rows if isinstance(x,dict)]
    errors=[]
    if len(ids)!=len(set(ids)) or set(ids)!=expected:errors.append('MISSING_OR_DUPLICATE_SCENARIO_IDS')
    if not live:errors.append('LIVE_PROVIDER_READBACK_REQUIRED')
    for row in rows:
        if not isinstance(row,dict):errors.append('MALFORMED_SCENARIO');continue
        sid=row.get('id')
        if sid not in expected:continue
        if row.get('status')!='PASS':errors.append(f'{sid}:NOT_PASSED');continue
        if row.get('expected')!=spec[sid] or not isinstance(row.get('observed'),str) or not row['observed'].strip():
            errors.append(f'{sid}:EXPECTED_OR_OBSERVED_ORACLE_MISSING');continue
        sha=row.get('source_sha')
        if not isinstance(sha,str) or not SHA.fullmatch(sha):errors.append(f'{sid}:INVALID_SOURCE_SHA');continue
        refs=row.get('run_refs') or []
        if not isinstance(refs,list) or not refs:errors.append(f'{sid}:REAL_RUN_REF_REQUIRED');continue
        reviewer=row.get('independent_reviewer') or {}
        match=COMMENT.fullmatch(str(reviewer.get('comment_url') or ''))
        if not match or match.group(1)!=repo or not reviewer.get('login') or reviewer.get('login')==row.get('executor_login'):
            errors.append(f'{sid}:INDEPENDENT_REVIEW_MISSING');continue
        digest=hashlib.sha256(json.dumps({'id':sid,'expected':row['expected'],'observed':row['observed'],
                                         'source_sha':sha,'run_refs':refs},sort_keys=True,separators=(',',':')).encode()).hexdigest()
        if live:
            try:
                comment=gh(f'repos/{repo}/issues/comments/{match.group(3)}')
                if ((comment.get('user') or {}).get('login') != reviewer['login'] or
                    str(comment.get('issue_url') or '') != f'https://api.github.com/repos/{repo}/issues/{match.group(2)}' or
                    f'LAB_VERDICT {sid} PASS result_digest={digest}' not in str(comment.get('body') or '')):
                    errors.append(f'{sid}:REVIEWER_PROVIDER_MISMATCH')
                for url in refs:
                    found=RUN.fullmatch(str(url))
                    if not found or found.group(1)!=repo:
                        errors.append(f'{sid}:BAD_RUN_URL');continue
                    run=gh(f'repos/{repo}/actions/runs/{found.group(2)}')
                    if ((run.get('repository') or {}).get('full_name') != repo or
                        run.get('head_sha')!=sha or run.get('status')!='completed' or
                        run.get('conclusion')!='success'):
                        errors.append(f'{sid}:RUN_REPO_HEAD_OR_SUCCESS_MISMATCH')
            except (RuntimeError,KeyError,ValueError) as exc:
                errors.append(f'{sid}:PROVIDER_READBACK_FAILED:{str(exc)[:90]}')
    return {'status':'E2E_PASS_WITH_PROVIDER_READBACK' if not errors else 'E2E_NOT_QUALIFIED','checked':len(rows),'required':len(expected),'errors':errors}

def main():
    p=argparse.ArgumentParser();p.add_argument('--results',required=True);p.add_argument('--repository',required=True);p.add_argument('--readback',action='store_true',help='real GitHub API GETs required to qualify release');a=p.parse_args()
    report=evaluate(json.loads((ROOT/'stress/scenarios.json').read_text()),json.loads(pathlib.Path(a.results).read_text()),live=a.readback,repo=a.repository)
    print(json.dumps(report,indent=2));return 0 if report['status']=='E2E_PASS_WITH_PROVIDER_READBACK' else 1
if __name__=='__main__':raise SystemExit(main())
