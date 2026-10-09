"""BR-09 contract: every apparent success still requires external verification."""
from __future__ import annotations
import copy
import json
import unittest

from trial_evaluator import evaluate, strict_loads, TrialError, MODES, PHASES, SCHEMA

BASE = {
    "schema": SCHEMA,
    "case_id": "csv-r01-seed",
    "source_start_sha": "a"*40,
    "owner_intent_digest": "sha256:"+"b"*64,
    "golden_fixture_digest": "sha256:"+"c"*64,
}
METRIC_KEYS=("agent1_tokens","runner_tokens","reviewer_tokens",
             "agent1_cost_microusd","runner_cost_microusd",
             "reviewer_cost_microusd","recovery_seconds")


def build():
    trials=[]
    for idx, mode in enumerate(MODES):
        phases=[{"name":name, "artifact_sha256":"sha256:"+format(i+1,"064x"),
                 "provider_ref":"unqualified:test-only-fixture",
                 "observed_by":"synthetic-recorder",
                 "result":("NOT_APPLICABLE" if idx==0 and name in {
                     "RUNNER_BLIND_READ", "RUNNER_PLAN_SEALED", "WITNESS_PROVIDER_READBACK",
                     "AGENT1_INTERRUPTED", "STAGE2_SOURCE_RECONCILED"} else "PASS")}
                for i,name in enumerate(PHASES)]
        trials.append({
            "mode": mode, "run_id": "trial-"+str(idx),
            "source_start_sha":BASE["source_start_sha"],
            "owner_intent_digest":BASE["owner_intent_digest"],
            "golden_fixture_digest":BASE["golden_fixture_digest"],
            "case_parameters_digest":"sha256:"+"d"*64,
            "runner_kind":"NONE" if idx==0 else "DETERMINISTIC_FIXTURE",
            "interruption_kind":"NONE" if idx==0 else "SIMULATED",
            "golden_result":"PASS", "readback_status":"STRUCTURAL_ONLY",
            "trigger_percent":None if idx==0 else (50,70,85)[idx-1],
            "trigger_source_kind":"NONE" if idx==0 else "AGENT_SELF_ESTIMATE",
            "phases":phases,
            "metrics":{key: (0 if idx==0 and key in
                        ("runner_tokens","runner_cost_microusd") else 100+idx)
                        for key in METRIC_KEYS},
        })
    return {**BASE,"trials":trials}


class TrialEvaluatorTests(unittest.TestCase):
    def test_matched_four_trial_fixture_never_qualifies_production(self):
        report=evaluate(build())
        self.assertEqual(["CONTROL","EARLY_50","TARGET_70","LATE_85"], report["comparison_order"])
        self.assertEqual("EXTERNAL_VERIFIER_REQUIRED",report["qualification"])
        self.assertEqual("NOT_GRANTED",report["production_write_authority"])
        self.assertFalse(report["claimed_real_successor_contract_complete"])
        self.assertEqual(3*101,report["comparisons"][1]["total_cost_microusd"])
        self.assertTrue(report["all_metric_fields_supplied_not_authenticated"])

    def test_all_self_claimed_real_success_does_not_grant_merge(self):
        item=build()
        for row in item["trials"][1:]:
            row.update(runner_kind="REAL_AGENT", interruption_kind="OBSERVED",
                       readback_status="INDEPENDENTLY_ATTESTED")
        report=evaluate(item)
        self.assertTrue(report["claimed_real_successor_contract_complete"])
        self.assertEqual("EXTERNAL_VERIFIER_REQUIRED",report["qualification"])
        self.assertEqual("NOT_GRANTED",report["production_write_authority"])

    def test_missing_metric_remains_unknown_not_zero(self):
        item=build()
        item["trials"][2]["metrics"]["runner_cost_microusd"]=None
        report=evaluate(item)
        self.assertIsNone(report["comparisons"][2]["total_cost_microusd"])
        self.assertIsNone(report["comparisons"][2]["total_tokens"])
        self.assertFalse(report["all_costs_observed_in_supplied_record"])

    def test_unmatched_owner_or_golden_forbidden(self):
        for key, val in (("owner_intent_digest","sha256:"+"e"*64),
                         ("golden_fixture_digest","sha256:"+"f"*64),
                         ("source_start_sha","f"*40)):
            with self.subTest(key=key):
                item=build()
                item["trials"][1][key]=val
                with self.assertRaisesRegex(TrialError,"UNMATCHED_TRIAL_INPUT"):
                    evaluate(item)

    def test_unmatched_scenario_parameters_rejected(self):
        item=build()
        item["trials"][3]["case_parameters_digest"]="sha256:"+"f"*64
        with self.assertRaisesRegex(TrialError,"UNMATCHED_CASE_PARAMETERS"):
            evaluate(item)

    def test_wrong_trial_order_or_repeat_rejected(self):
        item=build()
        item["trials"][1],item["trials"][2]=item["trials"][2],item["trials"][1]
        with self.assertRaisesRegex(TrialError,"TRIAL_ORDER_INVALID"):
            evaluate(item)

    def test_duplicate_run_rejected(self):
        item=build()
        item["trials"][1]["run_id"]=item["trials"][0]["run_id"]
        with self.assertRaisesRegex(TrialError,"DUPLICATE_RUN"):
            evaluate(item)

    def test_fake_non_control_runner_required(self):
        item=build()
        item["trials"][1]["runner_kind"]="NONE"
        with self.assertRaisesRegex(TrialError,"TREATMENT_WITHOUT_RUNNER"):
            evaluate(item)

    def test_control_cannot_be_runner_treatment(self):
        item=build()
        item["trials"][0]["runner_kind"]="REAL_AGENT"
        with self.assertRaisesRegex(TrialError,"CONTROL_MUST_HAVE_NO_RUNNER"):
            evaluate(item)

    def test_phase_drift_or_missing_evidence_rejected(self):
        item=build()
        item["trials"][1]["phases"][0]["name"]="RUNNER_PLAN_SEALED"
        with self.assertRaisesRegex(TrialError,"PHASE_ORDER_INVALID"):
            evaluate(item)
        item=build()
        item["trials"][1]["phases"][1]["artifact_sha256"]="invalid"
        with self.assertRaisesRegex(TrialError,"INVALID_HASH"):
            evaluate(item)

    def test_negative_or_string_costs_refused(self):
        for bad in (-1,"100",True,1.5):
            with self.subTest(bad=bad):
                item=build()
                item["trials"][1]["metrics"]["agent1_cost_microusd"]=bad
                with self.assertRaisesRegex(TrialError,"METRIC_MISSING_OR_INVALID"):
                    evaluate(item)

    def test_extra_claim_fields_blocked(self):
        item=build()
        item["trials"][1]["owner_approved"]=True
        with self.assertRaisesRegex(TrialError,"TRIAL_SCHEMA_INVALID"):
            evaluate(item)

    def test_trigger_bands_and_source_type_checked(self):
        item=build()
        item["trials"][1]["trigger_percent"]=87
        with self.assertRaisesRegex(TrialError,"TREATMENT_TRIGGER_INVALID"):
            evaluate(item)
        item=build()
        item["trials"][2]["trigger_source_kind"]="NONE"
        with self.assertRaisesRegex(TrialError,"TREATMENT_TRIGGER_INVALID"):
            evaluate(item)

    def test_control_must_skip_runner_steps_and_have_no_runner_cost(self):
        item=build()
        item["trials"][0]["phases"][1]["result"]="PASS"
        with self.assertRaisesRegex(TrialError,"CONTROL_RUNNER_PHASE_MUST_BE_SKIPPED"):
            evaluate(item)
        item=build()
        item["trials"][0]["metrics"]["runner_cost_microusd"]=9
        with self.assertRaisesRegex(TrialError,"CONTROL_RUNNER_COST_MUST_BE_ZERO"):
            evaluate(item)

    def test_duplicate_json_keys_refused(self):
        with self.assertRaisesRegex(TrialError,"DUPLICATE_JSON_KEY"):
            strict_loads('{"schema":"bad","schema":"good"}')

    def test_cost_is_sum_of_all_three_agents(self):
        item=build()
        for i,key in enumerate(("agent1_cost_microusd","runner_cost_microusd","reviewer_cost_microusd")):
            item["trials"][3]["metrics"][key]=[100,250,45][i]
        report=evaluate(item)
        self.assertEqual(395,report["comparisons"][3]["total_cost_microusd"])
        self.assertEqual(103,report["comparisons"][3]["recovery_seconds"])


if __name__=="__main__":
    unittest.main()
