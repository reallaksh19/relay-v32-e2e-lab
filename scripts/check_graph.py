"""Actual V3.2 source on disk; no mock projection."""
import argparse,json,subprocess,sys,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--engine',required=True);p.add_argument('--live-readonly',action='store_true');a=p.parse_args()
    engine=pathlib.Path(a.engine).resolve();graph=ROOT/'governance/released-graph.json'
    if not engine.is_file() or not graph.is_file():p.error('need actual pinned Common V3.2 engine and bootstrapped released graph')
    for step in (['validate-graph','--graph',str(graph)],['decompose-check','--graph',str(graph)]):
        cp=subprocess.run([sys.executable,str(engine),*step],check=False)
        if cp.returncode:raise SystemExit(cp.returncode)
    if a.live_readonly:
        repo=json.loads(graph.read_text())['programme']['repository']
        cp=subprocess.run([sys.executable,str(engine),'sync-github','--graph',str(graph),'--repository',repo,'--dry-run'],check=False)
        if cp.returncode:raise SystemExit(cp.returncode)
    print('GRAPH_GATES_COMPLETE; no live writer enabled')
if __name__=='__main__':main()
