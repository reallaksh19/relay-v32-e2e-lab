"""BR-09 Buddy Runner trial protocol and evidence admission (lab only).

Evaluate four matched experimental conditions without allowing self-reported
provider fields, synthetic actors or local test passes to grant production
successor authority. Caller-provided records are NOT authenticated provider
proof. This module has NO network, source writes or GitHub mutations.
"""
from __future__ import annotations
import hashlib
import json
import re

SCHEMA = "v32-buddy-br09-trial-set-v1"
MODES = ("CONTROL", "EARLY_50", "TARGET_70", "LATE_85")
PHASES = ("ORIGINAL_START", "RUNNER_BLIND_READ", "RUNNER_PLAN_SEALED",
          "WITNESS_PROVIDER_READBACK", "AGENT1_INTERRUPTED",
          "STAGE2_SOURCE_RECONCILED", "GOLDEN_ORACLE", "COST_CAPTURE")
_SHA = re.compile(r"^[a-f0-9]{40}$")
_HASH = re.compile(r"^sha256:[a-f0-9]{64}$")
_ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,79}$")
_ROOT_KEYS = {"schema", "case_id", "source_start_sha", "owner_intent_digest",
              "golden_fixture_digest", "trials"}
_TRIAL_KEYS = {"mode", "run_id", "source_start_sha", "owner_intent_digest",
               "golden_fixture_digest", "case_parameters_digest",
               "runner_kind", "interruption_kind", "golden_result",
               "readback_status", "phases", "metrics"}
_PHASE_KEYS = {"name", "artifact_sha256", "provider_ref", "observed_by", "result"}
_METRICS = {"agent1_tokens", "runner_tokens", "reviewer_tokens",
            "agent1_cost_microusd", "runner_cost_microusd",
            "reviewer_cost_microusd", "recovery_seconds"}


class TrialError(ValueError):
    pass


def _require(test, message):
    if not test:
        raise TrialError(message)


def strict_loads(text):
    def unique(pairs):
        result = {}
        for k, v in pairs:
            _require(k not in result, "DUPLICATE_JSON_KEY:" + k)
            result[k] = v
        return result
    return json.loads(text, object_pairs_hook=unique)


def _validate_sha(value, where, *, git=False):
    _require(type(value) is str and
             (bool(_SHA.fullmatch(value)) if git else bool(_HASH.fullmatch(value))),
             "INVALID_HASH:" + where)


def _phase(row):
    _require(type(row) is dict and set(row) == _PHASE_KEYS, "PHASE_SCHEMA_INVALID")
    _require(row["name"] in PHASES, "PHASE_NAME_INVALID")
    _validate_sha(row["artifact_sha256"], row["name"])
    for key in ("provider_ref", "observed_by"):
        _require(type(row[key]) is str and 0 < len(row[key]) <= 300, "PHASE_SOURCE_MISSING")
    _require(row["result"] in ("PASS", "FAIL", "UNKNOWN"), "PHASE_RESULT_INVALID")


def _trial(row, root):
    _require(type(row) is dict and set(row) == _TRIAL_KEYS, "TRIAL_SCHEMA_INVALID")
    _require(row["mode"] in MODES and type(row["run_id"]) is str and
             _ID.fullmatch(row["run_id"]), "TRIAL_ID_INVALID")
    for key in ("source_start_sha", "owner_intent_digest", "golden_fixture_digest"):
        _require(row[key] == root[key], "UNMATCHED_TRIAL_INPUT:" + key)
    _validate_sha(row["case_parameters_digest"], "case_parameters")
    _require(row["runner_kind"] in ("REAL_AGENT", "DETERMINISTIC_FIXTURE", "NONE"),
             "RUNNER_KIND_INVALID")
    _require(row["interruption_kind"] in ("OBSERVED", "SIMULATED", "NONE"),
             "INTERRUPTION_KIND_INVALID")
    _require(row["golden_result"] in ("PASS", "FAIL", "UNKNOWN"),
             "GOLDEN_RESULT_INVALID")
    _require(row["readback_status"] in ("INDEPENDENTLY_ATTESTED", "STRUCTURAL_ONLY",
                                        "NOT_OBSERVED"), "READBACK_STATUS_INVALID")
    phases = row["phases"]
    _require(type(phases) is list and len(phases) == len(PHASES), "PHASE_COUNT_INVALID")
    for event in phases:
        _phase(event)
    _require([event["name"] for event in phases] == list(PHASES),
             "PHASE_ORDER_INVALID")
    metrics = row["metrics"]
    _require(type(metrics) is dict and set(metrics) == _METRICS, "METRIC_SCHEMA_INVALID")
    for key, value in metrics.items():
        _require(value is None or (type(value) is int and value >= 0),
                 "METRIC_MISSING_OR_INVALID:" + key)
    return row


def evaluate(value):
    _require(type(value) is dict and set(value) == _ROOT_KEYS, "TRIAL_SET_SCHEMA_INVALID")
    _require(value["schema"] == SCHEMA and type(value["case_id"]) is str and
             _ID.fullmatch(value["case_id"]), "TRIAL_CASE_INVALID")
    _validate_sha(value["source_start_sha"], "source_start_sha", git=True)
    for key in ("owner_intent_digest", "golden_fixture_digest"):
        _validate_sha(value[key], key)
    rows = value["trials"]
    _require(type(rows) is list and len(rows) == 4, "FOUR_TRIALS_REQUIRED")
    for row in rows:
        _trial(row, value)
    _require([r["mode"] for r in rows] == list(MODES), "TRIAL_ORDER_INVALID")
    _require(len(set(r["run_id"] for r in rows)) == 4, "DUPLICATE_RUN")
    same_input = len({r["case_parameters_digest"] for r in rows}) == 1
    _require(same_input, "UNMATCHED_CASE_PARAMETERS")

    comparisons = []
    all_measured = True
    for row in rows:
        m = row["metrics"]
        complete_metrics = all(v is not None for v in m.values())
        all_measured = all_measured and complete_metrics
        comparisons.append({
            "mode": row["mode"], "golden_result": row["golden_result"],
            "runner_kind": row["runner_kind"],
            "actual_interruption": row["interruption_kind"],
            "phase_pass_count": sum(p["result"] == "PASS" for p in row["phases"]),
            "phase_unknown_count": sum(p["result"] == "UNKNOWN" for p in row["phases"]),
            "total_tokens": sum(m[k] for k in ("agent1_tokens","runner_tokens","reviewer_tokens"))
                            if complete_metrics else None,
            "total_cost_microusd": sum(m[k] for k in
                            ("agent1_cost_microusd","runner_cost_microusd","reviewer_cost_microusd"))
                            if complete_metrics else None,
            "recovery_seconds": m["recovery_seconds"] if complete_metrics else None,
        })

    real_successor = all(
        r["runner_kind"] == "REAL_AGENT"
        and r["interruption_kind"] == "OBSERVED"
        and r["golden_result"] == "PASS"
        and r["readback_status"] == "INDEPENDENTLY_ATTESTED"
        and all(p["result"] == "PASS" for p in r["phases"])
        for r in rows if r["mode"] != "CONTROL")
    _require(rows[0]["runner_kind"] == "NONE", "CONTROL_MUST_HAVE_NO_RUNNER")
    _require(rows[0]["interruption_kind"] == "NONE", "CONTROL_MUST_NOT_INTERRUPT")
    _require(all(r["runner_kind"] != "NONE" for r in rows[1:]),
             "TREATMENT_WITHOUT_RUNNER")
    # These statuses are self-reported. Even every field set to PASS cannot
    # attest the external source, signing principal, exact-head CI or Owner.
    return {
        "schema": "v32-buddy-br09-evaluation-v1",
        "case_id": value["case_id"],
        "same_frozen_source_and_fixture": True,
        "comparison_order": list(MODES),
        "comparisons": comparisons,
        "all_costs_observed_in_supplied_record": all_measured,
        "claimed_real_successor_contract_complete": real_successor,
        "external_evidence_authentication": "NOT_VERIFIED_BY_THIS_EVALUATOR",
        "qualification": "EXTERNAL_VERIFIER_REQUIRED",
        "production_write_authority": "NOT_GRANTED",
        "delp_progress_effect": "NONE",
        "input_digest": "sha256:"+hashlib.sha256(
            json.dumps(value, sort_keys=True, separators=(",",":")).encode()).hexdigest(),
    }
