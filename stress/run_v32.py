"""Independent OFFLINE probes against the actual pinned V3.2 Python engine.

No fake DELP implementation: only call importlib on --engine supplied by the user.
These checks do not fetch source and cannot award trusted GitHub evidence.
"""
from __future__ import annotations
import argparse,copy,importlib.util,json,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]

def verify(engine_path:pathlib.Path, graph_path:pathlib.Path)->dict:
    if not engine_path.exists():raise RuntimeError('Common V3.2 source engine is not present')
    spec=importlib.util.spec_from_file_location('lab_actual_delp_v32',engine_path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    graph=json.loads(graph_path.read_text())
    indexed=module.validate_graph(graph)
    report=module.decomposition_report(graph)
    if report.get('release_state')!='RELEASEABLE' or report['summary']['not_releasable']:
        raise AssertionError('actual Proposal-V2 not releaseable: '+json.dumps(report['leaves'])[:1200])
    leaf=next(ref for ref,node in indexed['nodes'].items() if node['kind']=='LEAF' and node.get('responsibility_id')=='R01')
    sha='a'*40;changed='b'*40
    observation={leaf:{'candidate_sha':sha,'liveness':'ACTIVE'}}
    zero=module.project(graph,[],observation)['nodes'][leaf]['progress']
    if zero['P']!=0 or zero['E']!=0:raise AssertionError('new responsibility awarded progress before facts')
    unit=indexed['nodes'][leaf]['units'][0]['id']
    base={
       'schema':module.FACTS_SCHEMA,
       'responsibility':{'issue':leaf,'id':'R01'},
       'material':{'candidate_sha':sha},
       'units':[{'id':unit,'state':'COMPLETE','result':'VERIFIED','evidence_refs':[]}],
       'next':{'unit':indexed['nodes'][leaf]['units'][1]['id'],'action':'continue implementation'},
       'blocker':'NONE','owner_action':'NONE'
    }
    ledger=[{'source':'test://local-unauthenticated/1','order':1,'facts':base}]
    no_evidence=module.project(graph,ledger,observation)['nodes'][leaf]
    if no_evidence['progress']['P']<=0 or no_evidence['progress']['E']!=0:
        raise AssertionError('declared completion/evidence axes incorrectly collapsed')
    complete=copy.deepcopy(base);complete['units'][0]['evidence_refs']=['lab://synthetic-reference-not-provider-authenticated']
    candidate_ledger=[{'source':'test://local-unauthenticated/2','order':1,'facts':complete}]
    current=module.project(graph,candidate_ledger,observation)['nodes'][leaf]['progress']
    if current['E']<=0 or current['E']!=current['P']:
        raise AssertionError('local same-head E was not recomputed from claimed refs')
    stale=module.project(graph,candidate_ledger,{leaf:{'candidate_sha':changed,'liveness':'ACTIVE'}})['nodes'][leaf]['progress']
    if stale['P']!=current['P'] or stale['E']!=0:
        raise AssertionError('changed head did not invalidate evidenced axis without changing P')
    forged=copy.deepcopy(complete);forged['progress']={'P':100}
    pr=module.project(graph,[{'source':'test://malicious','order':1,'facts':forged}],observation)
    if not pr['rejected_facts'] or pr['nodes'][leaf]['progress']['P']!=0:
        raise AssertionError('agent-authored progress was not rejected')
    # This is an explicit known limit: a synthetic nonempty reference can count
    # to the V1 pure projector. Provider authenticity must be independently checked.
    return {'status':'OFFLINE_GATES_PASS_WITH_KNOWN_AUTHENTICITY_LIMIT',
            'engine':str(engine_path),'root':indexed['root'],'leaf':leaf,
            'checks':['V2 released proposal','initial zero','P without E','E with synthetically matched candidate','candidate drift E=0','forged progress rejected'],
            'known_gap':'V1 offline projector does not independently authenticate evidence_refs, source identity or provider currentness',
            'baseline':zero,'no_evidence':no_evidence['progress'],'synthetic_current':current,'stale':stale}

def main():
    p=argparse.ArgumentParser();p.add_argument('--engine',required=True);p.add_argument('--graph',default='governance/released-graph.json');args=p.parse_args()
    graph=(ROOT/args.graph).resolve()
    if not graph.is_file():p.error('released graph missing: bootstrap actual GitHub issues first')
    report=verify(pathlib.Path(args.engine).resolve(),graph)
    outfile=ROOT/'evidence/offline-harness-result.json';outfile.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
