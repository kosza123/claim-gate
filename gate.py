#!/usr/bin/env python3
"""Claim Gate production judge.

Untrusted: claim.json (the producer).
Trusted: LAW.md from the base ref, this file, the Action.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ENGINE = "claim-gate/gate.py@2"
FLOOR_DEFAULT = 0.70
ADVERSARIAL_X = (0.5, 0.0, 1.0, -1.0, 2.0)
PESEL = re.compile(r"\b\d{11}\b")
RANK = {"ADMIT": 0, "INCOMPLETE": 1, "REJECT": 2}


def digest(payload) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def parse_laws(text: str) -> dict:
    laws, current = {}, {}

    def flush():
        if not current:
            return
        law_id = current.get("id") or current.get("heading")
        if not law_id:
            return
        require = tuple(p.strip() for p in current.get("require", "").split(",") if p.strip())
        floor = current.get("floor")
        laws[law_id] = {
            "id": law_id,
            "statement": current.get("statement", ""),
            "check": current.get("check", ""),
            "require": require,
            "floor": float(floor) if floor else None,
            "source": current,
        }

    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("## "):
            flush()
            current = {"heading": line[3:].strip()}
            continue
        if line.startswith("- ") and ":" in line:
            key, value = line[2:].split(":", 1)
            current[key.strip()] = value.strip()
    flush()
    return laws


def check_balance(evidence, law):
    start = int(evidence.get("opening_balance", 0))
    running = start
    withdrawals = evidence.get("withdrawals")
    if withdrawals is None:
        return {"broken_law": "withdrawals missing"}
    for amount in withdrawals:
        running -= int(amount)
        if running < 0:
            return {
                "opening_balance": start,
                "withdrawal": int(amount),
                "resulting_balance": running,
                "broken_law": "balance never negative",
            }
    return None


def check_email(evidence, law):
    rows = evidence.get("users_after_migration")
    if rows is None:
        return {"broken_law": "users_after_migration missing"}
    for row in rows:
        if row.get("email") in (None, ""):
            return {
                "row_id": row.get("id"),
                "email": row.get("email"),
                "broken_law": "users.email remains NOT NULL",
            }
    return None


def check_formula(evidence, law):
    samples = list(evidence.get("samples") or [])
    for raw in list(ADVERSARIAL_X) + samples:
        x = float(raw)
        if x * x < 2.0 * x:
            return {
                "x": x,
                "left": x * x,
                "right": 2.0 * x,
                "broken_law": "x^2 >= 2x for all real x",
                "injected": x in ADVERSARIAL_X,
            }
    return None


def check_facts(evidence, law):
    facts = evidence.get("facts")
    if not facts:
        return {"facts": facts, "broken_law": "SUCCESS/ALLOW requires non-empty facts"}
    return None


def check_consistency(evidence, law):
    score = float(evidence.get("consistency_score", 0))
    floor = law.get("floor") if law.get("floor") is not None else FLOOR_DEFAULT
    if score < floor:
        return {
            "consistency_score": score,
            "floor": floor,
            "broken_law": "consistency at or above floor for SUCCESS",
        }
    return None


def check_no_exfil(evidence, law):
    outbound = evidence.get("outbound")
    if outbound is None:
        return {"broken_law": "outbound missing"}
    for call in outbound:
        dest = str(call.get("destination") or "")
        kind = str(call.get("kind") or "")
        if kind == "model":
            continue
        if dest and dest not in ("browser-local", "model"):
            return {
                "destination": dest,
                "kind": kind,
                "broken_law": "notes stay in the browser except the model call",
            }
    return None


def check_pii(evidence, law):
    trace = evidence.get("response_trace")
    blob = json.dumps(trace).lower()
    if PESEL.search(blob) or "national_id" in blob or "pesel" in blob:
        return {"broken_law": "API responses never contain raw national IDs"}
    return None


def check_self(evidence, law):
    failures = attack_matrix()
    if failures:
        return {"broken_law": "self-check failed", "failures": failures[:8]}
    return None


CHECKS = {
    "balance_never_negative": check_balance,
    "email_not_null": check_email,
    "formula_always_holds": check_formula,
    "facts_non_empty": check_facts,
    "consistency_floor": check_consistency,
    "no_exfil": check_no_exfil,
    "no_raw_national_id": check_pii,
    "self_check": check_self,
}

CI_GENERATED = {"self_check"}


def judge_one(law, claim):
    check = law.get("check") or ""
    if not check or check == "none":
        return "INCOMPLETE", {"unknown_check": check or "none"}
    checker = CHECKS.get(check)
    if checker is None:
        return "INCOMPLETE", {"unknown_check": check}
    if check in CI_GENERATED:
        hit = checker({}, law)
        return ("REJECT", hit) if hit else ("ADMIT", None)
    evidence = claim.get("evidence") or {}
    if not isinstance(evidence, dict):
        return "INCOMPLETE", {"bad_evidence": type(evidence).__name__}
    missing = [k for k in law["require"] if k not in evidence]
    if missing:
        return "INCOMPLETE", {
            "missing_evidence": missing,
            "producer_said_success": claim.get("claim_success"),
        }
    try:
        hit = checker(evidence, law)
    except Exception as exc:
        return "INCOMPLETE", {"checker_error": str(exc)}
    if hit:
        return "REJECT", hit
    return "ADMIT", None


def evaluate(law_text: str, claim, meta=None):
    meta = meta or {}
    if not (law_text or "").strip():
        return "INCOMPLETE", [("LAW.md", "INCOMPLETE", {"empty_policy": True}, "")]
    try:
        laws = parse_laws(law_text)
    except Exception as exc:
        return "INCOMPLETE", [("LAW.md", "INCOMPLETE", {"parse_error": str(exc)}, "")]
    if not laws:
        return "INCOMPLETE", [("LAW.md", "INCOMPLETE", {"empty_policy": True}, "")]
    # Producer cannot choose a subset. Extra names are ignored.
    overall, rows = "ADMIT", []
    for law_id, law in laws.items():
        verdict, witness = judge_one(law, claim)
        if RANK[verdict] > RANK[overall]:
            overall = verdict
        receipt = digest(
            {
                "engine": ENGINE,
                "law_id": law_id,
                "law": {k: law[k] for k in ("id", "statement", "check", "require", "floor")},
                "verdict": verdict,
                "witness": witness,
                "claim": claim,
                "head_sha": meta.get("head_sha"),
                "base_sha": meta.get("base_sha"),
                "run_id": meta.get("run_id"),
            }
        )
        rows.append((law_id, verdict, witness, receipt))
    return overall, rows


def render(overall, rows) -> str:
    lines = [
        "## Claim Gate",
        "",
        f"**{overall}** — producer is untrusted. `claim_success` is not evidence. Policy comes from the base ref, not this PR.",
        "",
    ]
    for law_id, verdict, witness, receipt in rows:
        lines.append(f"### `{law_id}` — {verdict}")
        if witness:
            lines.append(f"- witness: `{json.dumps(witness)}`")
        lines.append(f"- receipt: `{receipt}`")
        lines.append("")
    if overall != "ADMIT":
        lines.append("_Fail closed. Merge stays blocked._")
    return "\n".join(lines) + "\n"


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except Exception as exc:
        return None, str(exc)


def attack_matrix():
    """Return list of failed case names. Must not recurse into check_self."""
    cases = []

    def law(body):
        return "# Laws\n\n" + body

    cases.append(("empty_policy", "", {"evidence": {}}, "INCOMPLETE"))
    cases.append(("no_laws_heading", "# Laws\n\njust text", {"evidence": {}}, "INCOMPLETE"))
    cases.append(
        (
            "check_none",
            law("## pii\n- id: pii\n- check: none\n- require: response_trace\n"),
            {"evidence": {"response_trace": {"national_id": "12345678901"}}},
            "INCOMPLETE",
        )
    )
    cases.append(
        (
            "pii_leak",
            law("## pii\n- id: pii\n- check: no_raw_national_id\n- require: response_trace\n"),
            {"evidence": {"response_trace": {"national_id": "44051401359"}}},
            "REJECT",
        )
    )
    cases.append(
        (
            "formula_cherry_pick",
            law("## formula\n- id: formula\n- check: formula_always_holds\n- require: samples\n"),
            {"evidence": {"samples": [3, 4]}},
            "REJECT",
        )
    )
    cases.append(
        (
            "balance_negative",
            law(
                "## balance\n- id: balance\n- check: balance_never_negative\n- require: opening_balance, withdrawals\n"
            ),
            {"claim_success": True, "evidence": {"opening_balance": 40, "withdrawals": [100]}},
            "REJECT",
        )
    )
    cases.append(
        (
            "balance_omit_key",
            law(
                "## balance\n- id: balance\n- check: balance_never_negative\n- require: opening_balance, withdrawals\n"
            ),
            {"evidence": {"opening_balance": 40}},
            "INCOMPLETE",
        )
    )
    cases.append(
        (
            "agent_picks_subset",
            law(
                "## balance\n- id: balance\n- check: balance_never_negative\n- require: opening_balance, withdrawals\n\n"
                "## formula\n- id: formula\n- check: formula_always_holds\n- require: samples\n"
            ),
            {
                "laws": ["formula"],
                "evidence": {"opening_balance": 40, "withdrawals": [100], "samples": [3]},
            },
            "REJECT",
        )
    )
    cases.append(
        (
            "agent_sets_floor",
            law(
                "## consistency\n- id: consistency\n- check: consistency_floor\n- floor: 0.70\n- require: consistency_score\n"
            ),
            {"evidence": {"consistency_score": 0.01, "consistency_floor": 0}},
            "REJECT",
        )
    )
    cases.append(
        (
            "facts_empty",
            law("## facts\n- id: facts\n- check: facts_non_empty\n- require: facts\n"),
            {"claim_success": True, "evidence": {"facts": []}},
            "REJECT",
        )
    )
    cases.append(
        (
            "honest_balance",
            law(
                "## balance\n- id: balance\n- check: balance_never_negative\n- require: opening_balance, withdrawals\n"
            ),
            {"evidence": {"opening_balance": 40, "withdrawals": [10]}},
            "ADMIT",
        )
    )

    failures = []
    for name, law_text, claim, expected in cases:
        overall, _rows = evaluate(law_text, claim, meta={"head_sha": "test"})
        if overall != expected:
            failures.append(f"{name}: got {overall} want {expected}")
    # receipts for honest vs forged balance must differ when evidence differs
    law_b = law(
        "## balance\n- id: balance\n- check: balance_never_negative\n- require: opening_balance, withdrawals\n"
    )
    _, honest_rows = evaluate(
        law_b, {"evidence": {"opening_balance": 40, "withdrawals": [10]}}, meta={"head_sha": "a"}
    )
    _, forged_rows = evaluate(
        law_b, {"evidence": {"opening_balance": 40, "withdrawals": [100]}}, meta={"head_sha": "a"}
    )
    if honest_rows[0][3] == forged_rows[0][3]:
        failures.append("receipt_collision: honest and forged share receipt")
    return failures


def write_out(out: Path, overall: str, md: str):
    out.mkdir(parents=True, exist_ok=True)
    (out / "verdict.txt").write_text(overall + "\n", encoding="utf-8")
    (out / "comment.md").write_text(md, encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--claim", type=Path)
    parser.add_argument("--law", type=Path, default=Path("LAW.md"))
    parser.add_argument("--out", type=Path, default=Path("out"))
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--head-sha", default="")
    parser.add_argument("--base-sha", default="")
    parser.add_argument("--run-id", default="")
    args = parser.parse_args(argv)

    if args.self_check:
        failures = attack_matrix()
        if failures:
            sys.stdout.write("SELF-CHECK FAIL\n" + "\n".join(failures) + "\n")
            write_out(args.out, "REJECT", "## Claim Gate\n\n**REJECT** self-check\n")
            return 1
        sys.stdout.write("SELF-CHECK PASS\n")
        write_out(args.out, "ADMIT", "## Claim Gate\n\n**ADMIT** self-check\n")
        return 0

    if args.claim is None:
        write_out(
            args.out,
            "INCOMPLETE",
            "## Claim Gate\n\n**INCOMPLETE** — no claim.json.\n",
        )
        sys.stdout.write("INCOMPLETE — no claim.json\n")
        return 1

    if not args.law.exists():
        write_out(
            args.out,
            "INCOMPLETE",
            "## Claim Gate\n\n**INCOMPLETE** — no trusted LAW.md.\n",
        )
        sys.stdout.write("INCOMPLETE — no trusted LAW.md\n")
        return 1

    claim, err = load_json(args.claim)
    if err:
        write_out(
            args.out,
            "INCOMPLETE",
            f"## Claim Gate\n\n**INCOMPLETE** — claim.json unreadable: {err}\n",
        )
        sys.stdout.write("INCOMPLETE — bad claim.json\n")
        return 1
    if not isinstance(claim, dict):
        write_out(
            args.out,
            "INCOMPLETE",
            "## Claim Gate\n\n**INCOMPLETE** — claim.json must be an object.\n",
        )
        return 1

    overall, rows = evaluate(
        args.law.read_text(encoding="utf-8"),
        claim,
        meta={"head_sha": args.head_sha, "base_sha": args.base_sha, "run_id": args.run_id},
    )
    md = render(overall, rows)
    write_out(args.out, overall, md)
    sys.stdout.write(md)
    return 0 if overall == "ADMIT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
