"""Create a private lab only after explicit local execution by authenticated Owner."""
import argparse,re,subprocess,pathlib,sys,json
ROOT=pathlib.Path(__file__).resolve().parents[1]
def run(args,check=True): return subprocess.run(args,cwd=ROOT,text=True,capture_output=True,check=check)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repository',required=True);args=ap.parse_args()
    repo=args.repository
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repo): ap.error('repository must be owner/name')
    if (ROOT/'.git').exists(): ap.error('refusing: git repository already exists')
    try:
        run(['gh','auth','status'])
    except (subprocess.CalledProcessError,FileNotFoundError): ap.error('authenticated gh CLI required')
    existing=run(['gh','api',f'repos/{repo}'],check=False)
    if existing.returncode==0: ap.error(f'repository {repo} already exists; refusing overwrite')
    if existing.returncode!=0 and ('Not Found' not in existing.stderr and '404' not in existing.stderr):
        ap.error('cannot distinguish absent repository from auth or network error: '+existing.stderr[:180])
    run(['git','init','-b','main'])
    run(['git','add','.'])
    run(['git','-c','user.name=V3.2 Lab Bootstrap','-c','user.email=v32lab@example.invalid','commit','-m','lab: preserve Owner request and precommitted RED feature oracles'])
    created=run(['gh','repo','create',repo,'--private','--source=.','--remote=origin','--push'])
    out=run(['gh','api',f'repos/{repo}'])
    if json.loads(out.stdout).get('private') is not True: raise RuntimeError('new lab did not read back as private: STOP')
    print('CREATED_PRIVATE_LAB',repo);print('INITIAL_HEAD',run(['git','rev-parse','HEAD']).stdout.strip())
if __name__=='__main__':main()
