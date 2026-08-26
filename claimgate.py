#!/usr/bin/env python3
"""Claim Gate — ADMIT / REJECT / INCOMPLETE + witness + receipt.

Extracted from Hamada / Famada / OCOI and rebuilt as a product surface.
The original research repository kosza123/kosza123-semantic-language-2045
is not modified.

Kept from the original:
  - producer is untrusted (agent claim_success is never evidence)
  - fail-closed: missing proof is INCOMPLETE, not SUCCESS
  - explicit reason codes, not prose
  - receipt bound to every decision-relevant byte (SHA-256 commit)
  - invariant check before any ADMIT

Thrown away from the original:
  - SetZ language kernel as the product
  - worker/checkpoint protocol
  - "new language 2045" framing
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Mapping


class Verdict(str, Enum):
    ADMIT = "ADMIT"
    REJECT = "REJECT"
    INCOMPLETE = "INCOMPLETE"


class Reason(str, Enum):
    WITNESS_FOUND = "WITNESS_FOUND"
    OBLIGATION_BROKEN = "OBLIGATION_BROKEN"
    EVIDENCE_MISSING = "EVIDENCE_MISSING"
    CLAIM_UNBOUND = "CLAIM_UNBOUND"
    PRODUCER_NOT_EVIDENCE = "PRODUCER_NOT_EVIDENCE"
    INVARIANT_BROKEN = "INVARIANT_BROKEN"


def commit(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Law:
    """Durable semantic identity: what must remain true."""

    id: str
    statement: str
    check: Callable[[Mapping[str, Any]], Mapping[str, Any] | None]
    required_evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class Claim:
    """Untrusted producer output. Never treated as proof."""

    producer: str
    claim_success: bool
    change: str
    evidence: Mapping[str, Any] = field(default_factory=dict)
    world: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Receipt:
    verdict: Verdict
    reasons: tuple[str, ...]
    witness: Mapping[str, Any] | None
    law_id: str
    bound_law: str
    bound_claim: str
    bound_evidence: str
    receipt_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict.value,
            "reasons": list(self.reasons),
            "witness": self.witness,
            "law_id": self.law_id,
            "bound_law": self.bound_law,
            "bound_claim": self.bound_claim,
            "bound_evidence": self.bound_evidence,
            "receipt_sha256": self.receipt_sha256,
        }


def _inv(receipt_body: Mapping[str, Any]) -> None:
    if receipt_body["verdict"] == Verdict.ADMIT.value and receipt_body.get("witness"):
        raise RuntimeError("INVARIANT_BROKEN: ADMIT cannot carry a witness")
    if receipt_body["verdict"] == Verdict.REJECT.value and not receipt_body.get("witness"):
        raise RuntimeError("INVARIANT_BROKEN: REJECT must carry a witness")
    if receipt_body["verdict"] == Verdict.ADMIT.value and not receipt_body["reasons"]:
        raise RuntimeError("INVARIANT_BROKEN: ADMIT must name why")


def gate(law: Law, claim: Claim) -> Receipt:
    bound_law = commit({"id": law.id, "statement": law.statement})
    bound_claim = commit(
        {
            "producer": claim.producer,
            "claim_success": claim.claim_success,
            "change": claim.change,
        }
    )
    bound_evidence = commit(dict(claim.evidence))

    missing = [key for key in law.required_evidence if key not in claim.evidence]
    if missing:
        body = {
            "verdict": Verdict.INCOMPLETE.value,
            "reasons": [Reason.EVIDENCE_MISSING.value, Reason.PRODUCER_NOT_EVIDENCE.value],
            "witness": {"missing_evidence": missing, "producer_said_success": claim.claim_success},
            "law_id": law.id,
        }
        receipt_hash = commit({**body, "bound_law": bound_law, "bound_claim": bound_claim, "bound_evidence": bound_evidence})
        return Receipt(
            verdict=Verdict.INCOMPLETE,
            reasons=tuple(body["reasons"]),
            witness=body["witness"],
            law_id=law.id,
            bound_law=bound_law,
            bound_claim=bound_claim,
            bound_evidence=bound_evidence,
            receipt_sha256=receipt_hash,
        )

    hit = law.check({**claim.world, **claim.evidence, "change": claim.change})
    if hit is not None:
        body = {
            "verdict": Verdict.REJECT.value,
            "reasons": [Reason.WITNESS_FOUND.value, Reason.OBLIGATION_BROKEN.value],
            "witness": dict(hit),
            "law_id": law.id,
        }
        receipt_hash = commit({**body, "bound_law": bound_law, "bound_claim": bound_claim, "bound_evidence": bound_evidence})
        _inv(body)
        return Receipt(
            verdict=Verdict.REJECT,
            reasons=tuple(body["reasons"]),
            witness=body["witness"],
            law_id=law.id,
            bound_law=bound_law,
            bound_claim=bound_claim,
            bound_evidence=bound_evidence,
            receipt_sha256=receipt_hash,
        )

    body = {
        "verdict": Verdict.ADMIT.value,
        "reasons": ["OBLIGATIONS_HELD_ON_AVAILABLE_CHECKS"],
        "witness": None,
        "law_id": law.id,
    }
    _inv(body)
    receipt_hash = commit({**body, "bound_law": bound_law, "bound_claim": bound_claim, "bound_evidence": bound_evidence})
    return Receipt(
        verdict=Verdict.ADMIT,
        reasons=tuple(body["reasons"]),
        witness=None,
        law_id=law.id,
        bound_law=bound_law,
        bound_claim=bound_claim,
        bound_evidence=bound_evidence,
        receipt_sha256=receipt_hash,
    )


def _balance_never_negative(ctx: Mapping[str, Any]) -> Mapping[str, Any] | None:
    start = int(ctx.get("opening_balance", 0))
    withdrawals = list(ctx.get("withdrawals", []))
    running = start
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


def _email_not_null(ctx: Mapping[str, Any]) -> Mapping[str, Any] | None:
    rows = list(ctx.get("users_after_migration", []))
    for row in rows:
        if row.get("email") in (None, ""):
            return {
                "row_id": row.get("id"),
                "email": row.get("email"),
                "broken_law": "users.email remains NOT NULL",
            }
    return None


def _formula_always_holds(ctx: Mapping[str, Any]) -> Mapping[str, Any] | None:
    samples = ctx.get("samples", [0.5, 0.0, 1.0, 2.0, -1.0])
    for x in samples:
        x = float(x)
        if x * x < 2.0 * x:
            return {
                "x": x,
                "left": x * x,
                "right": 2.0 * x,
                "broken_law": "x^2 >= 2x for all real x",
            }
    return None


LAWS = {
    "balance": Law(
        id="balance",
        statement="Account balance is never negative.",
        check=_balance_never_negative,
        required_evidence=("opening_balance", "withdrawals"),
    ),
    "migration": Law(
        id="migration",
        statement="After migration, users.email remains NOT NULL.",
        check=_email_not_null,
        required_evidence=("users_after_migration",),
    ),
    "formula": Law(
        id="formula",
        statement="x^2 >= 2x for all real x.",
        check=_formula_always_holds,
        required_evidence=("samples",),
    ),
    "pii": Law(
        id="pii",
        statement="API responses never contain raw national IDs.",
        check=lambda ctx: None,
        required_evidence=("response_trace",),
    ),
}


def demo_cases() -> list[tuple[str, Law, Claim]]:
    return [
        (
            "1. Agent: withdraw is done. Law: balance never negative.",
            LAWS["balance"],
            Claim(
                producer="coding-agent",
                claim_success=True,
                change="withdraw() without a guard",
                evidence={"opening_balance": 40, "withdrawals": [100]},
            ),
        ),
        (
            "2. Agent: migration is safe. Law: email stays NOT NULL.",
            LAWS["migration"],
            Claim(
                producer="coding-agent",
                claim_success=True,
                change="DROP NOT NULL on users.email",
                evidence={"users_after_migration": [{"id": 7, "email": None}]},
            ),
        ),
        (
            "3. Agent: identity holds. Law: x^2 >= 2x for all real x.",
            LAWS["formula"],
            Claim(
                producer="coding-agent",
                claim_success=True,
                change="documented the inequality as always true",
                evidence={"samples": [0.5, 0.0, 1.0, 2.0]},
            ),
        ),
        (
            "4. Agent: no PII leaked. Law: traces required. None given.",
            LAWS["pii"],
            Claim(
                producer="coding-agent",
                claim_success=True,
                change="ship the endpoint",
                evidence={},
            ),
        ),
        (
            "5. Honest withdraw stays inside the law.",
            LAWS["balance"],
            Claim(
                producer="coding-agent",
                claim_success=True,
                change="withdraw() with guard",
                evidence={"opening_balance": 40, "withdrawals": [10, 20]},
            ),
        ),
    ]


def render(receipt: Receipt) -> str:
    lines = [
        f"  verdict : {receipt.verdict.value}",
        f"  reasons : {', '.join(receipt.reasons)}",
        f"  receipt : {receipt.receipt_sha256[:16]}…",
    ]
    if receipt.witness:
        lines.append(f"  witness : {json.dumps(receipt.witness, ensure_ascii=False)}")
    return "\n".join(lines)


def main() -> int:
    print("CLAIM GATE")
    print("Producer is untrusted. claim_success is not evidence.")
    print("Original Hamada/Famada repo was copied, not edited.\n")
    failed = 0
    expected = {
        1: Verdict.REJECT,
        2: Verdict.REJECT,
        3: Verdict.REJECT,
        4: Verdict.INCOMPLETE,
        5: Verdict.ADMIT,
    }
    for i, (title, law, claim) in enumerate(demo_cases(), start=1):
        receipt = gate(law, claim)
        print(f"{title}")
        print(f"  agent   : claim_success={claim.claim_success}")
        print(render(receipt))
        if receipt.verdict != expected[i]:
            print(f"  ERROR expected {expected[i].value}")
            failed += 1
        print()
    if failed:
        print(f"SELF-CHECK FAILED ({failed})")
        return 1
    print("SELF-CHECK PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
