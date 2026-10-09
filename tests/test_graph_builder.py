import pathlib, sys, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from graph_builder import pre_graph,released_graph,SPECS

class GraphBuilderTests(unittest.TestCase):
    def setUp(self):
        self.repo='sample-user/relay-v32-e2e-lab'
        self.n={'ROOT':1,'PHASE_CORE':2,'PHASE_DELIVERY':3,'R01':4,'R02':5,'R03':6}
    def test_prematerialization_no_child_issue_is_fabricated(self):
        x=pre_graph(self.repo,1)
        self.assertEqual(1,len(x['nodes']))
        self.assertEqual('V2',x['programme']['decomposition_proposal']['version'])
        self.assertEqual(100,sum(c['weight'] for c in x['programme']['acceptance_claims']))
        self.assertNotIn('bindings',x['programme']['decomposition_proposal'])
    def test_released_bindings_are_actual_provider_ids_not_titles(self):
        x=released_graph(self.repo,self.n,'sha256:'+'f'*64)
        p=x['programme']['decomposition_proposal']
        self.assertEqual({f'{self.repo}#{i}' for i in (4,5,6)},{z['ref'] for z in p['bindings']})
        self.assertEqual([7,3],[z['weight'] for z in x['nodes'][1:3]])
        self.assertEqual([3,4,3],[z['weight'] for z in x['nodes'][3:]])
        self.assertEqual([f'{self.repo}#4'],x['nodes'][4]['depends_on'])
        self.assertEqual([f'{self.repo}#5'],x['nodes'][5]['depends_on'])
    def test_no_unowned_or_duplicate_semantic_claim(self):
        rows=pre_graph(self.repo,1)['programme']['decomposition_proposal']['responsibilities']
        self.assertEqual(len(SPECS),len({x for r in rows for x in r['owns_claims']}))
        self.assertEqual({x['id'] for x in pre_graph(self.repo,1)['programme']['acceptance_claims']},{x for r in rows for x in r['owns_claims']})
    def test_every_unit_has_meaningful_outcome_and_verification(self):
        for item in pre_graph(self.repo,1)['programme']['decomposition_proposal']['responsibilities']:
            self.assertEqual(100,sum(x['weight'] for x in item['semantic_units']))
            self.assertTrue(item['independence_basis'])
            self.assertTrue(all(u['outcome'] and u['verify'] and u['kind']=='SEMANTIC' for u in item['semantic_units']))
