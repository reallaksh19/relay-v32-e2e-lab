import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from runner_readiness import ReadinessError, assess, render_task_evidence, parse_task_evidence

BASE = {
    "run_id": "buddy-run-001", "responsibility": "reallaksh19/relay-v32-e2e-lab#4",
    "candidate_sha": "a" * 40, "source_kind": "PROVIDER_REPORTED",
    "used_context_tokens": 7000, "usable_context_tokens": 10000,
    "episode_consumed_percent": None, "next_unit_demand_tokens": None,
    "safety_reserve_tokens": None, "cognitive_warning": "NONE",
    "interruption_risk": "NONE", "agent_requests_runner": False, "confidence": "MEDIUM"
}


class ReadinessTests(unittest.TestCase):
    def make(self, **kwargs):
        return assess({**BASE, **kwargs})

    def test_exact_threshold_requests_runner(self):
        r = self.make()
        self.assertEqual("REQUEST_RUNNER", r["advisory"]["decision"])
        self.assertEqual("SEVENTY_PERCENT_TRIGGER", r["advisory"]["reason"])
        self.assertEqual("NONE", r["advisory"]["delp_progress_effect"])
        self.assertEqual("NOT_GRANTED", r["advisory"]["promotion"])

    def test_sixty_prepares_without_launch(self):
        r = self.make(used_context_tokens=6000)
        self.assertEqual("PREPARE", r["advisory"]["decision"])
        self.assertFalse(r["advisory"]["time_for_runner"])

    def test_early_remaining_work_warning(self):
        r = self.make(used_context_tokens=5500, next_unit_demand_tokens=4000, safety_reserve_tokens=500)
        self.assertEqual("NEXT_UNIT_EXCEEDS_RELIABLE_RUNWAY", r["advisory"]["reason"])

    def test_severe_warning_urgent_even_without_telemetry(self):
        r = self.make(source_kind="UNAVAILABLE", used_context_tokens=None,
                      usable_context_tokens=None, cognitive_warning="SEVERE")
        self.assertEqual("URGENT_RUNNER", r["advisory"]["decision"])

    def test_unknown_stays_unknown_not_healthy(self):
        r = self.make(source_kind="UNAVAILABLE", used_context_tokens=None, usable_context_tokens=None,
                      confidence="UNKNOWN")
        self.assertEqual("UNKNOWN", r["advisory"]["decision"])
        self.assertFalse(r["advisory"]["time_for_runner"])

    def test_explicit_agent_request_is_advisory(self):
        r = self.make(source_kind="UNAVAILABLE", used_context_tokens=None, usable_context_tokens=None,
                      agent_requests_runner=True, confidence="LOW")
        self.assertEqual("AGENT_SELF_REQUEST", r["advisory"]["reason"])
        self.assertEqual("NOT_GRANTED", r["advisory"]["execution_authority"])

    def test_episode_proxy_distinct_from_provider_telemetry(self):
        r = self.make(source_kind="CALIBRATED_EPISODE", used_context_tokens=None,
                      usable_context_tokens=None, episode_consumed_percent=71)
        self.assertEqual("REQUEST_RUNNER", r["advisory"]["decision"])
        self.assertEqual("CALIBRATED_EPISODE", r["observation"]["source_kind"])

    def test_85_is_urgent(self):
        r = self.make(used_context_tokens=8500)
        self.assertEqual("URGENT_RUNNER", r["advisory"]["decision"])

    def test_partial_or_faked_telemetry_rejected(self):
        bad = [dict(used_context_tokens=None), dict(used_context_tokens=10001),
               dict(source_kind="AGENT_SELF_ESTIMATE"), dict(usable_context_tokens=0),
               dict(episode_consumed_percent=75), dict(next_unit_demand_tokens=500),
               dict(used_context_tokens=True), dict(agent_requests_runner="yes")]
        for x in bad:
            with self.subTest(x=x), self.assertRaises(ReadinessError):
                self.make(**x)

    def test_render_and_parse_roundtrip_exact(self):
        r = self.make()
        text = render_task_evidence(r)
        self.assertTrue(text.startswith("TASK_EVIDENCE — CHECKPOINT"))
        self.assertIn("TIME_FOR_RUNNER", text)
        self.assertEqual(r, parse_task_evidence(text))
        self.assertNotIn("CHECKPOINT_FACTS_V1", text)

    def test_tampered_decision_rejected(self):
        r = self.make()
        changed = copy.deepcopy(r)
        changed["advisory"]["execution_authority"] = "GRANTED"
        with self.assertRaises(ReadinessError):
            render_task_evidence(changed)
        text = render_task_evidence(r)
        with self.assertRaises(ReadinessError):
            parse_task_evidence(text.replace("NOT_GRANTED", "GRANTED"))

    def test_ambiguous_extra_comment_rejected(self):
        with self.assertRaises(ReadinessError):
            parse_task_evidence(render_task_evidence(self.make()) + "later plan\n")

    def test_cli_output_and_verify(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            source = root / "observation.json"
            source.write_text(json.dumps(BASE))
            output = root / "evidence.md"
            script = Path(__file__).with_name("runner_readiness.py")
            one = subprocess.run([sys.executable, str(script), "render", "--observation", str(source),
                                  "--output", str(output)], capture_output=True, text=True)
            self.assertEqual(0, one.returncode, one.stderr)
            two = subprocess.run([sys.executable, str(script), "verify", "--evidence", str(output)],
                                  capture_output=True, text=True)
            self.assertEqual(0, two.returncode, two.stderr)
            self.assertEqual("REQUEST_RUNNER", json.loads(two.stdout)["decision"])
            again = subprocess.run([sys.executable, str(script), "render", "--observation", str(source),
                                    "--output", str(output)], capture_output=True, text=True)
            self.assertEqual(2, again.returncode)


if __name__ == "__main__":
    unittest.main()
