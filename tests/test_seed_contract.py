import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from csv_auditor import parser, compare, cli

class SeedContractTests(unittest.TestCase):
    def test_real_leaf_entrypoints_remain_callable_as_product_evolves(self):
        # Never require NotImplementedError here: that would make healthy future
        # implementation of R01/R02/R03 regress the seed smoke suite.
        for fn in (parser.read_rows, compare.diff, cli.main):
            with self.subTest(fn=fn.__name__):
                self.assertTrue(callable(fn))

    def test_claims_and_owner_source_are_distinct(self):
        import json
        doc = json.loads((ROOT/'governance/acceptance-claims.json').read_text())
        self.assertEqual('SYNTHETIC_LAB_PROPOSAL_NOT_OWNER_PRODUCT_VERBATIM', doc['authority'])
        self.assertEqual({'R01','R02','R03'}, {x['owner'] for x in doc['claims']})
        owner = (ROOT/'governance/owner-intent.md').read_text()
        self.assertIn('permalink: **UNKNOWN**', owner)

if __name__ == '__main__': unittest.main()
