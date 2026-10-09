"""Two-stage GitHub bootstrap: real Owner proposal approval BEFORE child issues.

prepare: create only root issue and V2 pre-materialization proposal, print digest+SHA.
release: verify exact GitHub Owner approval comment, then create phase/leaf issues.

A green model decision never creates its own Owner authority. All provider IDs
are returned by the actual gh API, and a child cannot be created in prepare.
"""
import argparse,json,re,subprocess,sys,pathlib
from graph_builder import pre_graph,released_graph,SPECS
ROOT=pathlib.Path(__file__).resolve().parents[1]
STATE=ROOT/'.lab-bootstrap-state.json'

def cmd(*args,input=None,check=True):
    p=subprocess.run(list(args),input=input,text=True,capture_output=True,cwd=ROOT,check=False)
    if check and p.returncode: raise RuntimeError(f'{list(args)}: {p.stderr[:400]}')
    return p

def api(method,repo,uri='',payload=None):
    endpoint=f'repos/{repo}'+('/'+uri if uri else '')
    args=['gh','api','-X',method,endpoint]
    if payload is not None: args+=['--input','-']
    r=cmd(*args,input=json.dumps(payload) if payload is not None else None)
    return json.loads(r.stdout)

def save(state):
    tmp=STATE.with_suffix('.tmp');tmp.write_text(json.dumps(state,indent=2)+'\n');tmp.replace(STATE)

def issue(repo,state,key,title,body):
    if key in state['issues']: return state['issues'][key]
    all_issues=api('GET',repo,'issues?state=all&per_page=100')
    matches=[it for it in all_issues if it.get('title')==title and 'pull_request' not in it]
    if len(matches)>1: raise RuntimeError('ambiguous recovery: duplicate issue titles '+title)
    row=matches[0] if matches else api('POST',repo,'issues',{'title':title,'body':body})
    state['issues'][key]=int(row['number']); save(state)
    return int(row['number'])

def jsonfile(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')

def proposal_check(engine,graph_path):
    r=cmd(sys.executable,str(engine),'decompose-check','--graph',str(graph_path),'--json')
    output=json.loads(r.stdout)
    if output.get('release_state')!='RELEASEABLE' or output['summary']['not_releasable']!=0:
        raise RuntimeError('Proposal-V2 NOT releaseable: '+r.stdout[:1500])
    digest=output.get('proposal_digest')
    if not isinstance(digest,str) or not re.fullmatch(r'sha256:[0-9a-f]{64}',digest):raise RuntimeError('proposal digest missing')
    return digest

def commit_push(*paths):
    cmd('git','add',*paths)
    staged=cmd('git','diff','--cached','--quiet',check=False)
    if staged.returncode:
        cmd('git','-c','user.name=V3.2 Lab Bootstrap','-c','user.email=v32lab@example.invalid','commit','-m','lab: retain reviewed V2 proposal or bound graph')
        cmd('git','push','origin','main')
    return cmd('git','rev-parse','HEAD').stdout.strip()

def owner_decision(repo,root,digest,pinned_sha):
    expected=f'APPROVE_LAB_PROPOSAL_V2 digest={digest} source_sha={pinned_sha}'
    comments=api('GET',repo,f'issues/{root}/comments?per_page=100')
    good=[x for x in comments if str((x.get('user') or {}).get('login') or '').lower()==repo.split('/')[0].lower() and str(x.get('body') or '').strip()==expected]
    if len(good)!=1:
        raise RuntimeError('OWNER_APPROVAL_REQUIRED: Post EXACT comment on the real parent issue, then rerun --release:\n'+expected)
    return {'comment_id':int(good[0]['id']),'url':good[0].get('html_url'), 'author_login':good[0]['user']['login'], 'proposal_digest':digest,'proposal_sha':pinned_sha}

def run_bootstrap(repo,engine,mode):
    meta=api('GET',repo)
    if meta.get('private') is not True:raise RuntimeError('refusing non-private lab')
    if 'origin' not in cmd('git','remote').stdout.split():raise RuntimeError('no origin configured')
    if cmd('git','status','--porcelain').stdout.strip():raise RuntimeError('working tree must be clean; commit or remove local changes before bootstrap')
    state=json.loads(STATE.read_text()) if STATE.exists() else {'repository':repo,'issues':{}}
    if state['repository']!=repo:raise RuntimeError('bootstrap state from different repository')
    seed='[LAB-V32-CSV]'
    root=issue(repo,state,'ROOT',seed+' ROOT — Owner intent and semantic acceptance',
       'Original Owner request is in governance/owner-intent.md (permalink UNKNOWN). CSV brief is an explicitly synthetic laboratory selection. Child issues must be bound to an independently released Proposal-V2 digest. Post a separate Owner approval comment before any child materializes.')
    prepath=ROOT/'governance/pre-materialization-graph.json'
    candidate=pre_graph(repo,root)
    if prepath.exists():
        existing=json.loads(prepath.read_text())
        existing['programme']['decomposition_proposal'].pop('released_proposal_digest',None)
        if existing!=candidate:raise RuntimeError('preproposal drift: do not silently rewrite the released source basis')
    else:jsonfile(prepath,candidate)
    digest=proposal_check(engine,prepath)
    if mode=='prepare':
        sha=commit_push('governance/pre-materialization-graph.json')
        print(json.dumps({'status':'PREPARED_NOT_OWNER_APPROVED','root_issue':f'https://github.com/{repo}/issues/{root}',
                          'proposal_digest':digest,'pinned_sha':sha,
                          'required_comment':f'APPROVE_LAB_PROPOSAL_V2 digest={digest} source_sha={sha}',
                          'children_created':False},indent=2))
        return
    # RELEASE is explicitly separate from PREPARE and requires exact provider
    # readback of a comment made on the parent issue by the repository owner.
    # After partial release, recover the ORIGINAL approved proposal SHA rather
    # than misidentifying the newer released graph as the approved candidate.
    pinned_sha=(state.get('owner_approval') or {}).get('proposal_sha') or cmd('git','rev-parse','HEAD').stdout.strip()
    released_pre=cmd('git','show',f'{pinned_sha}:governance/pre-materialization-graph.json')
    if json.loads(released_pre.stdout)!=candidate:raise RuntimeError('original approved proposal source drift: prepare again')
    approval=owner_decision(repo,root,digest,pinned_sha)
    state['owner_approval']=approval; save(state)
    candidate['programme']['decomposition_proposal']['released_proposal_digest']=digest
    jsonfile(prepath,candidate)
    release_ref=commit_push('governance/pre-materialization-graph.json')
    issue(repo,state,'PHASE_CORE',seed+' PHASE — semantic core',f'Governed by #{root}, approved proposal ref {release_ref}; R01→R02 is serial.')
    issue(repo,state,'PHASE_DELIVERY',seed+' PHASE — delivery',f'Governed by #{root}, approved proposal ref {release_ref}; R03 follows R02.')
    for rid,spec in SPECS.items():
        body=(f'IMPLEMENTATION_PLAN — LAB {rid}\n\nClaim: {spec["claim"]}.\nOutcome: {spec["outcome"]}\nIndependence: {spec["basis"]}\n'
              f'Write surface: `{spec["write_surface"][0]}`.\nAccepted verification: `{spec["methods"][0]}`.\n'
              f'Owner approval: {approval["url"]} exact digest `{digest}` on pinned source `{pinned_sha}`.\n'
              f'Depends on: {spec["depends"] or "NONE"}.\n\nPublish only leaf TASK_EVIDENCE, never P/E/D or invented review.')
        issue(repo,state,rid,seed+f' {rid} — {spec["outcome"]}',body)
    graph=released_graph(repo,state['issues'],digest)
    graphpath=ROOT/'governance/released-graph.json';jsonfile(graphpath,graph)
    report=json.loads(cmd(sys.executable,str(engine),'decompose-check','--graph',str(graphpath),'--json').stdout)
    if report.get('release_state')!='RELEASEABLE' or report['summary']['not_releasable']:
        raise RuntimeError('binding/decomposition BLOCKED: '+json.dumps(report['leaves'])[:1800])
    jsonfile(ROOT/'governance/issue-map.json',state)
    ref=commit_push('governance/released-graph.json','governance/issue-map.json')
    for rid in SPECS:
        cmd('git','push','origin',f'{ref}:refs/heads/lab/{rid.lower()}')
    print(json.dumps({'status':'BOOTSTRAPPED_SOURCE_RELEASED','repository':repo,'owner_approval':approval,
                      'proposal_digest':digest,'pre_release_sha':release_ref,'graph_sha':ref,'issues':state['issues']},indent=2))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repository',required=True);ap.add_argument('--engine',required=True,
        help='Pinned Common V3.2 delp_projection_v32.py')
    group=ap.add_mutually_exclusive_group(required=True)
    group.add_argument('--prepare',action='store_true',help='Only root issue and candidate proposal; NO child issues')
    group.add_argument('--release',action='store_true',help='Requires genuine exact Owner GitHub approval comment')
    a=ap.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',a.repository):ap.error('repository must be owner/name')
    engine=pathlib.Path(a.engine).resolve()
    if not engine.is_file():ap.error('actual pinned V3.2 engine required')
    run_bootstrap(a.repository,engine,'prepare' if a.prepare else 'release')
if __name__=='__main__':main()
