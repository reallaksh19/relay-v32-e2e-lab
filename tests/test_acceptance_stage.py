import pathlib
import sys
import unittest
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import acceptance_stage

class StageSelectionTests(unittest.TestCase):
    def test_r01_does_not_require_unimplemented_r02_or_r03(self):
        self.assertEqual(['test_r01_input.py'], acceptance_stage.stage_patterns('lab/r01'))
    def test_r02_includes_r01_predecessor(self):
        self.assertEqual(['test_r01_input.py', 'test_r02_compare.py'], acceptance_stage.stage_patterns('lab/r02'))
    def test_r03_and_main_cover_all_acceptance(self):
        self.assertEqual(list(acceptance_stage.PATTERNS['R03']), acceptance_stage.stage_patterns('lab/r03'))
        self.assertEqual(list(acceptance_stage.PATTERNS['R03']), acceptance_stage.stage_patterns('main'))
    def test_ungoverned_branch_fails_closed(self):
        for value in ['feature/new', 'lab/r04', 'lab/r01-unsafe', '', 'release/main']:
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'BRANCH_UNGOVERNED'):
                acceptance_stage.stage_patterns(value)
    def test_scope_control_is_only_on_real_branch_name(self):
        self.assertEqual(['test_r01_input.py'], acceptance_stage.stage_patterns('lab/r01/fix-parse'))
