# Reviewer brief

**DEMO_ONLY — NOT_TEAM_READY**

External review (2026-08-26) was right: v1 moved trust from `claim_success` into the same JSON the agent writes. This tree rebuilds the trust boundary. It does not make domain evidence CI-generated.

## Fixed here

- Policy is `LAW.md` from the **base ref**, not the PR.
- Producer cannot pick a subset of laws.
- `check: none` is INCOMPLETE, not ADMIT.
- Missing claim.json is INCOMPLETE, not ADMIT.
- Empty policy is INCOMPLETE.
- Judge crash / bad JSON is INCOMPLETE.
- Verdicts go to `$RUNNER_TEMP`. Repo `out/verdict.txt` is ignored. No `|| true`.
- Consistency floor comes from LAW.md, not from evidence.
- Formula always injects adversarial `x` values.
- PII actually scans the trace.
- Receipts hash engine + law + claim + SHAs, not just verdict/witness.
- Production `--self-check` is an attack matrix on `gate.py`.
- MIT license. CODEOWNERS on policy/engine/workflow.

## Still not team-ready

- Domain evidence (balances, traces, outbound calls) is still a JSON blob from the producer. CI does not yet extract it from the head SHA.
- `uses: ./` on this repo can be edited in a PR; protection depends on required check name `gate` + CODEOWNERS + humans.
- Branch rulesets must be on; the files cannot flip `protected: true` by themselves if the API rejects it.
- No marketplace release, no signed provenance.

## What to keep

Three verdicts. UNKNOWN ≠ SUCCESS. Fail closed.
