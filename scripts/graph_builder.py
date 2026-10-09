"""V3.2 Proposal-V2 pre-materialization and exact child binding for a private lab.

Only an authorized human may release the proposal; this helper computes its
candidate structure but cannot establish human provenance by itself.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLAIMS = {x['id']:x for x in json.loads((ROOT/'governance/acceptance-claims.json').read_text())['claims']}
SPECS = {
 'R01': {
   'claim':'CL-INPUT', 'points':30, 'phase':'PHASE_CORE',
   'outcome':'Reject invalid input sources and preserve each valid keyed record exactly.',
   'basis':'Input validity is independently decidable from parsing edge cases without finishing comparison or CLI.',
   'write_surface':['src/csv_auditor/parser.py'],
   'depends':[], 'methods':['python -m unittest discover -s acceptance -p test_r01_input.py -v'],
   'units':[('U01',30,'Reject empty ID and missing ID header'),('U02',35,'Reject duplicate IDs with a clear error'),('U03',35,'Retain every valid keyed row with unmodified column values')]
 },
 'R02': {
   'claim':'CL-DIFF', 'points':40, 'phase':'PHASE_CORE',
   'outcome':'Classify newly present, missing and changed keyed records without row-order errors.',
   'basis':'Change classification is independently verifiable on normalized dictionaries after R01 delivers the input contract.',
   'write_surface':['src/csv_auditor/compare.py'],
   'depends':['R01'], 'methods':['python -m unittest discover -s acceptance -p test_r02_compare.py -v'],
   'units':[('U01',30,'Identify newly present keys'),('U02',35,'Identify keys no longer present'),('U03',35,'Identify changed keyed values with deterministic ordering')]
 },
 'R03': {
   'claim':'CL-CLI', 'points':30, 'phase':'PHASE_DELIVERY',
   'outcome':'Produce deterministic JSON and an unambiguous nonzero error status on invalid input.',
   'basis':'The CLI exit contract and JSON output can be accepted separately when R01 and R02 are stable.',
   'write_surface':['src/csv_auditor/cli.py'],
   'depends':['R02'], 'methods':['python -m unittest discover -s acceptance -p test_r03_cli.py -v'],
   'units':[('U01',30,'Accept exactly two input paths'),('U02',35,'Emit stable added removed modified JSON'),('U03',35,'Return nonzero without successful payload for invalid inputs')]
 },
}


def acceptance_claims():
    return [{'id':s['claim'],'claim':CLAIMS[s['claim']]['claim'],'kind':'SEMANTIC','weight':s['points'],'shared':False} for s in SPECS.values()]


def proposal_rows():
    rows=[]
    for rid,s in SPECS.items():
        unitverify=s['methods'][0]
        rows.append({
            'id':rid,'work_class':'PRODUCT','owns_claims':[s['claim']],
            'claim_allocations':[{'claim_id':s['claim'],'weight':s['points']}],
            'outcome':s['outcome'],'independence_basis':s['basis'],
            'semantic_units':[{'id':uid,'kind':'SEMANTIC','weight':weight,'outcome':outcome,'verify':unitverify} for uid,weight,outcome in s['units']],
            'size_budget':{'target_loc':100,'hard_loc':400,'target_minutes':10,'hard_minutes':20},
            'write_surface':s['write_surface'],'acceptance_methods':s['methods'],'depends_on':s['depends']
        })
    return rows


def pre_graph(repo: str, root_number: int):
    return {
        'schema':'relay-v3.2-delp-execution-graph',
        'programme':{
           'id':'LAB-V32-CSV-AUDITOR','root':f'{repo}#{root_number}',
           'repository':repo,'total_weight':100,'base_ref':'main',
           'decomposition_policy':{'mode':'ENFORCED','claim_first':{'mode':'ENFORCED','require_independence_basis':True}},
           'acceptance_claims':acceptance_claims(),
           'decomposition_proposal':{'version':'V2','responsibilities':proposal_rows()}
        },
        'nodes':[{'ref':f'{repo}#{root_number}','kind':'ROOT'}]
    }


def released_graph(repo: str, ids: dict[str,int], release_digest: str):
    graph=pre_graph(repo,ids['ROOT'])
    pr=graph['programme']['decomposition_proposal']; pr['released_proposal_digest']=release_digest
    pr['bindings']=[{'responsibility_id':rid,'ref':f'{repo}#{ids[rid]}'} for rid in SPECS]
    root=f'{repo}#{ids["ROOT"]}'
    graph['nodes'] += [
       {'ref':f'{repo}#{ids["PHASE_CORE"]}','kind':'INTERMEDIATE','parent':root,'weight':7},
       {'ref':f'{repo}#{ids["PHASE_DELIVERY"]}','kind':'INTERMEDIATE','parent':root,'weight':3},
    ]
    for rid,s in SPECS.items():
        leaf={
          'ref':f'{repo}#{ids[rid]}','kind':'LEAF',
          'parent':f'{repo}#{ids[s["phase"]]}',
          'weight':s['points']//10,'responsibility_id':rid,
          'candidate_ref':f'lab/{rid.lower()}',
          'critical':True,'work_class':'PRODUCT','owns_claims':[s['claim']],
          'outcome':s['outcome'],'independence_basis':s['basis'],
          'write_surface':s['write_surface'],'acceptance_methods':s['methods'],
          'size_budget':{'target_loc':100,'hard_loc':400,'target_minutes':10,'hard_minutes':20},
          'depends_on':[f'{repo}#{ids[other]}' for other in s['depends']],
          'units':[{'id':uid,'weight':weight,'outcome':outcome,'verify':s['methods'][0]} for uid,weight,outcome in s['units']],
        }
        graph['nodes'].append(leaf)
    return graph
