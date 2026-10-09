"""Real namespace execution and simulated interruption; NOT an actual second LLM."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
import unittest
import test_runner_stage1 as seed
from runner_stage1 import digest
from runner_readiness import assess, render_task_evidence
from runner_protocol import activate, seal_activated_plan
from recorder_custody import append, verify_journal
from stage2_reconcile import reconcile
from namespace_runner import run_fixture
import test_stage2_reconcile as stage

KEY=bytes.fromhex('b4'*32)   # Synthetic test-only key, no production auth.

class EpisodeTests(unittest.TestCase):
    _git=seed.Stage1Tests._git
    capture=seed.Stage1Tests.capture
    def setUp(self):
        seed.Stage1Tests.setUp(self)
        self.capture()
        self.out=self.root/'runner-output'; self.out.mkdir()
        self.newroot=self.root/'runner-root'; self.newroot.mkdir()
        self.rec=self.root/'recorder'; self.rec.mkdir()
    def test_original_seed_blind_runner_after_simulated_agent_interruption(self):
        start=append(self.rec/'events.jsonl',KEY,'START_PINNED',self.snapshot)
        candidate=self.repo/'src/csv_auditor/parser.py'
        candidate.write_text('AGENT_ONE_PRIVATE_HOW_NEVER_VISIBLE_IN_STAGE1')
        self._git('add','.'); self._git('commit','-qm','simulated Agent1 progress')
        head=self._git('rev-parse','HEAD').strip()
        signal=assess({'run_id':'RUN-1','responsibility':'reallaksh19/relay-v32-e2e-lab#4',
            'candidate_sha':head,'source_kind':'AGENT_SELF_ESTIMATE',
            'used_context_tokens':None,'usable_context_tokens':None,
            'episode_consumed_percent':70,'next_unit_demand_tokens':None,
            'safety_reserve_tokens':None,'cognitive_warning':'NONE',
            'interruption_risk':'IMMINENT','agent_requests_runner':True,'confidence':'LOW'})
        self.assertEqual('URGENT_RUNNER',signal['advisory']['decision'])
        activate(self.snapshot,seed.PACKET,readiness_evidence=render_task_evidence(signal))
        request=append(self.rec/'events.jsonl',KEY,'RUNNER_REQUESTED',self.snapshot,
                       expected_last_mac=start['mac'])
        program=Path(__file__).with_name('ns_fixture_runner.py')
        entry=Path(__file__).with_name('ns_entry.sh')
        sha=lambda p:'sha256:'+hashlib.sha256(p.read_bytes()).hexdigest()
        run=run_fixture(self.snapshot,self.out,self.newroot,
            runner_program=program,approved_program_digest=sha(program),
            entry_script=entry,approved_entry_digest=sha(entry))
        self.assertEqual('ISOLATED_FIXTURE_EXECUTED',run['status'])
        plan=json.loads((self.out/'runner_plan.json').read_text())
        self.assertNotIn('PRIVATE_HOW',json.dumps(plan))
        self.assertNotIn('PRIVATE_HOW',json.dumps(run))
        receipt=self.rec/'plan.json'; gate=self.rec/'gate.json'
        seal_activated_plan(self.snapshot,receipt,gate,plan)
        sealed=append(self.rec/'events.jsonl',KEY,'PLAN_SEALED',self.snapshot,
                      receipt=receipt,gate=gate,expected_last_mac=request['mac'])
        incumbent=stage.INCUMBENT
        disclosure={'run_id':'RUN-1','candidate_sha':head,
            'incumbent_plan_digest':digest(incumbent),
            'source_context_digest':'sha256:'+'4'*64}
        opened=append(self.rec/'events.jsonl',KEY,'STAGE2_DISCLOSED',self.snapshot,
                      receipt=receipt,gate=gate,disclosure=disclosure,
                      expected_last_mac=sealed['mac'])
        state=verify_journal(self.rec/'events.jsonl',KEY,anchor=opened['mac'])
        self.assertEqual(4,state['events'])
        report=reconcile(self.snapshot,receipt,gate,self.repo,head,
                         incumbent,stage.DECISIONS,self.rec/'stage2.json')
        self.assertEqual(plan,report['independent_plan'])
        self.assertEqual('NOT_GRANTED',report['execution_authority'])
        self.assertEqual(['src/csv_auditor/parser.py'],report['source_observation']['changed_paths'])
