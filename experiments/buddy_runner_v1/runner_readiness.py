"""Experimental V3.2 Buddy Runner *advisory* health/runway observation.

The input is supplied by an agent/observer and is NOT independently authenticated.
No DELP percentage, execution admission, lease, or handover authorization is
produced. In particular, remaining context is not inferred if telemetry is
absent. This module has no network or GitHub write operations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

SCHEMA = "v32-buddy-runner-readiness-v1"
BODY_HEADER = "TASK_EVIDENCE — CHECKPOINT\n\n"
START = "TIME_FOR_RUNNER — "
SOURCE_KINDS = {"PROVIDER_REPORTED", "CALIBRATED_EPISODE", "AGENT_SELF_ESTIMATE", "UNAVAILABLE"}
CONFIDENCE = {"LOW", "MEDIUM", "HIGH", "UNKNOWN"}
WARNINGS = {"NONE", "MILD", "SEVERE"}
INTERRUPTION_RISKS = {"NONE", "POSSIBLE", "IMMINENT"}
DECISIONS = {"UNKNOWN", "CONTINUE", "PREPARE", "REQUEST_RUNNER", "URGENT_RUNNER"}
SHA = re.compile(r"^[a-f0-9]{40}$")
RUN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
REF = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+#[1-9][0-9]*$")
TOP_KEYS = {"run_id", "responsibility", "candidate_sha", "source_kind", "used_context_tokens",
            "usable_context_tokens", "episode_consumed_percent", "next_unit_demand_tokens",
            "safety_reserve_tokens", "cognitive_warning", "interruption_risk",
            "agent_requests_runner", "confidence"}


class ReadinessError(ValueError):
    pass


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value):
    return "sha256:" + hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _nonnegative_or_none(value, field):
    if value is not None and (type(value) is not int or value < 0):
        raise ReadinessError("INVALID_" + field.upper())


def assess(observation):
    """Conservative, source-labelled advisory. Never claims independent telemetry."""
    if type(observation) is not dict or set(observation) != TOP_KEYS:
        raise ReadinessError("READINESS_INPUT_SCHEMA_MISMATCH")
    if not RUN.fullmatch(observation["run_id"] or ""):
        raise ReadinessError("INVALID_RUN_ID")
    if not REF.fullmatch(observation["responsibility"] or ""):
        raise ReadinessError("INVALID_RESPONSIBILITY")
    if not SHA.fullmatch(observation["candidate_sha"] or ""):
        raise ReadinessError("INVALID_CANDIDATE_SHA")
    if observation["source_kind"] not in SOURCE_KINDS:
        raise ReadinessError("INVALID_SOURCE_KIND")
    if observation["confidence"] not in CONFIDENCE:
        raise ReadinessError("INVALID_CONFIDENCE")
    if observation["cognitive_warning"] not in WARNINGS:
        raise ReadinessError("INVALID_COGNITIVE_WARNING")
    if observation["interruption_risk"] not in INTERRUPTION_RISKS:
        raise ReadinessError("INVALID_INTERRUPTION_RISK")
    if type(observation["agent_requests_runner"]) is not bool:
        raise ReadinessError("INVALID_AGENT_REQUEST")
    for name in ("used_context_tokens", "usable_context_tokens", "episode_consumed_percent",
                 "next_unit_demand_tokens", "safety_reserve_tokens"):
        _nonnegative_or_none(observation[name], name)
    used, capacity = observation["used_context_tokens"], observation["usable_context_tokens"]
    episode = observation["episode_consumed_percent"]
    kind = observation["source_kind"]
    if (used is None) != (capacity is None):
        raise ReadinessError("PARTIAL_CONTEXT_TELEMETRY")
    if used is not None:
        if kind != "PROVIDER_REPORTED" or capacity == 0 or used > capacity:
            raise ReadinessError("INCONSISTENT_CONTEXT_TELEMETRY")
    if kind == "PROVIDER_REPORTED" and used is None:
        raise ReadinessError("PROVIDER_TELEMETRY_MISSING")
    if episode is not None and episode > 100:
        raise ReadinessError("EPISODE_PERCENT_OUT_OF_RANGE")
    if kind == "UNAVAILABLE" and (episode is not None or used is not None):
        raise ReadinessError("UNAVAILABLE_HAS_METRICS")
    if episode is not None and kind not in {"CALIBRATED_EPISODE", "AGENT_SELF_ESTIMATE"}:
        raise ReadinessError("EPISODE_SOURCE_MISMATCH")
    if kind in {"CALIBRATED_EPISODE", "AGENT_SELF_ESTIMATE"} and episode is None:
        raise ReadinessError("ESTIMATE_MISSING")
    demand, reserve = observation["next_unit_demand_tokens"], observation["safety_reserve_tokens"]
    if (demand is None) != (reserve is None):
        raise ReadinessError("PARTIAL_WORK_DEMAND")
    if demand is not None and used is None:
        raise ReadinessError("WORK_DEMAND_WITHOUT_CAPACITY")
    if observation["cognitive_warning"] == "SEVERE" or observation["interruption_risk"] == "IMMINENT":
        verdict, reason = "URGENT_RUNNER", "CRITICAL_RELIABILITY_WARNING"
    elif used is not None and demand is not None and demand + reserve >= capacity - used:
        verdict, reason = "REQUEST_RUNNER", "NEXT_UNIT_EXCEEDS_RELIABLE_RUNWAY"
    else:
        pct = (100 * used // capacity) if used is not None else episode
        if observation["agent_requests_runner"]:
            verdict, reason = "REQUEST_RUNNER", "AGENT_SELF_REQUEST"
        elif observation["cognitive_warning"] == "MILD":
            verdict, reason = "REQUEST_RUNNER", "COGNITIVE_WARNING"
        elif pct is None:
            verdict, reason = "UNKNOWN", "NO_LIFE_ESTIMATE_AVAILABLE"
        elif pct >= 85:
            verdict, reason = "URGENT_RUNNER", "LATE_RUNWAY_THRESHOLD"
        elif pct >= 70:
            verdict, reason = "REQUEST_RUNNER", "SEVENTY_PERCENT_TRIGGER"
        elif pct >= 60:
            verdict, reason = "PREPARE", "APPROACHING_TRIGGER"
        else:
            verdict, reason = "CONTINUE", "RUNWAY_ESTIMATE_BELOW_TRIGGER"
    return {"schema": SCHEMA, "observation": observation, "observation_digest": _digest(observation),
            "advisory": {"decision": verdict, "reason": reason,
                         "time_for_runner": verdict in {"REQUEST_RUNNER", "URGENT_RUNNER"},
                         "source_trust": "SUPPLIED_INPUT_NOT_INDEPENDENTLY_AUTHENTICATED",
                         "execution_authority": "NOT_GRANTED", "delp_progress_effect": "NONE",
                         "promotion": "NOT_GRANTED", "runner_launch": "NOT_EXECUTED"}}


def render_task_evidence(assessment):
    verified = assess(assessment.get("observation"))
    if verified != assessment:
        raise ReadinessError("READINESS_DECISION_TAMPERED")
    decision = verified["advisory"]["decision"]
    return (BODY_HEADER + START + decision + " (AGENT ADVISORY; NO CUSTODY TRANSFER)\n\n"
            + "\u0060\u0060\u0060json\n" + _canonical({"RUNNER_READINESS_V1": verified}) + "\n\u0060\u0060\u0060\n")


def parse_task_evidence(text):
    if not isinstance(text, str) or not text.startswith(BODY_HEADER + START):
        raise ReadinessError("NOT_NORMAL_TASK_EVIDENCE")
    match = re.fullmatch(re.escape(BODY_HEADER + START)
                         + r"([A-Z_]+) \(AGENT ADVISORY; NO CUSTODY TRANSFER\)\n\n\u0060\u0060\u0060json\n(.+)\n\u0060\u0060\u0060\n",
                         text, flags=re.DOTALL)
    if not match:
        raise ReadinessError("RUNNER_BLOCK_MISSING_OR_AMBIGUOUS")
    try:
        payload = json.loads(match.group(2))
    except json.JSONDecodeError as exc:
        raise ReadinessError("RUNNER_BLOCK_NOT_JSON") from exc
    if type(payload) is not dict or set(payload) != {"RUNNER_READINESS_V1"}:
        raise ReadinessError("RUNNER_BLOCK_SCHEMA_INVALID")
    assessment = payload["RUNNER_READINESS_V1"]
    if not isinstance(assessment, dict) or set(assessment) != {"schema", "observation", "observation_digest", "advisory"}:
        raise ReadinessError("READINESS_RECORD_SCHEMA_INVALID")
    if assess(assessment["observation"]) != assessment or match.group(1) != assessment["advisory"]["decision"]:
        raise ReadinessError("RUNNER_DECISION_BASIS_MISMATCH")
    return assessment


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    a = sub.add_parser("render")
    a.add_argument("--observation", required=True)
    a.add_argument("--output", required=True)
    b = sub.add_parser("verify")
    b.add_argument("--evidence", required=True)
    args = parser.parse_args()
    try:
        if args.command == "render":
            record = assess(json.loads(Path(args.observation).read_text(encoding="utf-8")))
            target = Path(args.output)
            if target.exists():
                raise ReadinessError("OUTPUT_ALREADY_EXISTS")
            with target.open("x", encoding="utf-8") as f:
                f.write(render_task_evidence(record))
        else:
            record = parse_task_evidence(Path(args.evidence).read_text(encoding="utf-8"))
        print(_canonical({"status": "AGENT_ADVISORY_ONLY", "decision": record["advisory"]["decision"],
                          "run_id": record["observation"]["run_id"],
                          "execution_authority": "NOT_GRANTED"}))
    except (ReadinessError, OSError, ValueError, TypeError) as exc:
        parser.exit(2, "RUNNER_READINESS_FAIL_CLOSED: " + str(exc) + "\n")


if __name__ == "__main__":
    main()
