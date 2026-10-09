import pathlib
import re
import unittest
ROOT = pathlib.Path(__file__).resolve().parents[1]

class AgentWorkpackContractTests(unittest.TestCase):
    def test_every_task_has_exact_id_and_one_checkbox(self):
        text = (ROOT/'LOCAL_AGENT_TASKS.md').read_text()
        got = re.findall(r'^- \[ \] \*\*LAB-(T\d\d) —', text, flags=re.M)
        self.assertEqual([f'T{i:02d}' for i in range(13)], got)

    def test_every_task_has_immediate_evidence_and_owner_stop(self):
        text = (ROOT/'LOCAL_AGENT_TASKS.md').read_text()
        self.assertIn('after EACH', text)
        self.assertIn('LAB-T05 — Owner approval STOP gate', text)
        self.assertIn('Agent MUST NOT post it', text)
        self.assertIn('Common #876', text)

    def test_template_keeps_unknown_evidence_and_no_fake_fact_claim(self):
        text = (ROOT/'evidence/TASK_EVIDENCE_TEMPLATE.md').read_text()
        for required in ('NOT_RUN / PASS / FAIL / BLOCKED','Exact','Exit code(s)', 'Durable source refs','Next authorized task'):
            self.assertIn(required.lower(), text.lower())
        self.assertIn('not** independent review', text.lower())
