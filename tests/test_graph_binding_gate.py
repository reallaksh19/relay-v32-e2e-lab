import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / 'scripts' / 'validate_graph_binding.py'
spec = importlib.util.spec_from_file_location('validate_graph_binding', MODULE)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def fixture():
    graph = {'programme': {'repository': 'reallaksh19/relay-v32-e2e-lab', 'base_ref': 'main',
                           'decomposition_proposal': {'version': 'V2'}},
             'nodes': [{'kind': 'ROOT', 'ref': 'reallaksh19/relay-v32-e2e-lab#1'},
                       {'kind': 'LEAF', 'ref': 'reallaksh19/relay-v32-e2e-lab#4',
                        'responsibility_id': 'R01', 'candidate_ref': 'lab/r01',
                        'units': [{'id': 'U01', 'weight': 30}, {'id': 'U02', 'weight': 35},
                                  {'id': 'U03', 'weight': 35}]}]}
    after = json.loads(json.dumps(graph))
    after['nodes'][1]['primary_pr'] = 'reallaksh19/relay-v32-e2e-lab#8'
    pr = {'number': 8, 'head': {'ref': 'lab/r01', 'sha': 'a' * 40,
                                  'repo': {'full_name': 'reallaksh19/relay-v32-e2e-lab'}},
          'base': {'ref': 'main', 'repo': {'full_name': 'reallaksh19/relay-v32-e2e-lab'}}}
    return graph, after, pr


class GraphBindingTests(unittest.TestCase):
    def check(self, before, after, pr=None, paths=None):
        return gate.verify_binding(before, after,
                                  changed_paths=paths or ['governance/released-graph.json'], pr=pr)

    def test_clean_single_binding(self):
        a, b, pr = fixture()
        result = self.check(a, b, pr)
        self.assertEqual('GRAPH_ONLY_MATERIAL_BINDING', result['status'])
        self.assertEqual('NONE', result['progress_credit'])

    def test_no_mutation_fails(self):
        a, b, pr = fixture()
        with self.assertRaisesRegex(ValueError, 'SEMANTIC_GRAPH_DRIFT'):
            self.check(a, a, pr)

    def test_changed_unit_weight(self):
        a, b, pr = fixture()
        b['nodes'][1]['units'][0]['weight'] = 31
        with self.assertRaisesRegex(ValueError, 'SEMANTIC_GRAPH_DRIFT'):
            self.check(a, b, pr)

    def test_changed_other_node(self):
        a, b, pr = fixture()
        b['nodes'][0]['other'] = 'tamper'
        with self.assertRaisesRegex(ValueError, 'SEMANTIC_GRAPH_DRIFT|NON_NEW_LEAF_BINDING'):
            self.check(a, b, pr)

    def test_changed_claim_digest(self):
        a, b, pr = fixture()
        b['programme']['decomposition_proposal']['version'] = 'V3'
        with self.assertRaisesRegex(ValueError, 'SEMANTIC_GRAPH_DRIFT'):
            self.check(a, b, pr)

    def test_extra_changed_file(self):
        a, b, pr = fixture()
        with self.assertRaisesRegex(ValueError, 'NOT_GRAPH_ONLY_CHANGE'):
            self.check(a, b, pr, paths=['governance/released-graph.json', 'src/csv_auditor/parser.py'])

    def test_wrong_pr(self):
        a, b, pr = fixture()
        pr['number'] = 9
        with self.assertRaisesRegex(ValueError, 'WRONG_PROVIDER_PR_NUMBER'):
            self.check(a, b, pr)

    def test_wrong_repo(self):
        a, b, pr = fixture()
        b['nodes'][1]['primary_pr'] = 'other/repo#8'
        with self.assertRaisesRegex(ValueError, 'INVALID_PR_REPOSITORY'):
            self.check(a, b, pr)

    def test_wrong_head_branch(self):
        a, b, pr = fixture()
        pr['head']['ref'] = 'lab/r02'
        with self.assertRaisesRegex(ValueError, 'HEAD_BRANCH_DOES_NOT_MATCH'):
            self.check(a, b, pr)

    def test_wrong_base_branch(self):
        a, b, pr = fixture()
        pr['base']['ref'] = 'dev'
        with self.assertRaisesRegex(ValueError, 'BASE_BRANCH_MISMATCH'):
            self.check(a, b, pr)

    def test_nonsha_head(self):
        a, b, pr = fixture()
        pr['head']['sha'] = 'not-a-sha'
        with self.assertRaisesRegex(ValueError, 'PR_HEAD_SHA_NOT_VERIFIED'):
            self.check(a, b, pr)

    def test_json_duplicate_keys_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)/'a.json'
            p.write_text('{"nodes": [], "nodes": []}', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'DUPLICATE_JSON_KEY'):
                gate.strict_json(str(p))

    def test_adding_second_binding_fails(self):
        a, b, pr = fixture()
        a['nodes'].append({'kind':'LEAF', 'ref':'reallaksh19/relay-v32-e2e-lab#5','responsibility_id':'R02', 'candidate_ref':'lab/r02'})
        b['nodes'].append({'kind':'LEAF', 'ref':'reallaksh19/relay-v32-e2e-lab#5','responsibility_id':'R02', 'candidate_ref':'lab/r02','primary_pr':'reallaksh19/relay-v32-e2e-lab#9'})
        with self.assertRaisesRegex(ValueError, 'SEMANTIC_GRAPH_DRIFT'):
            self.check(a, b, pr)


if __name__ == '__main__':
    unittest.main()
