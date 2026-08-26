# Brief for an external reviewer

Claim Gate judges an agent claim against durable laws.

Verdicts: ADMIT / REJECT / INCOMPLETE.
`claim_success` from the producer is not evidence.
Fail-closed: REJECT and INCOMPLETE block merge.

## What to open

1. https://github.com/kosza123/claim-gate
2. Judge: `gate.py`
3. Laws: `LAW.md`
4. Action: `action.yml`
5. Live REJECT: https://github.com/kosza123/claim-gate/pull/1
6. Live INCOMPLETE: https://github.com/kosza123/claim-gate/pull/3
7. Consumer using `uses: kosza123/claim-gate@main` (no local engine): https://github.com/kosza123/claim-gate-demo/pull/3
8. Consumer ADMIT: https://github.com/kosza123/claim-gate-demo/pull/2

## What it is not

- Not a new programming language.
- Not a 1000x math plugin.
- Not formal verification (Lean/Coq).
- Checks are small, explicit Python predicates.
- Hamada / semantic-language-2045 was copied, not edited.

## Ask

Is this a real, honest fail-closed gate for lying coding agents, or a toy?
What is missing before it is worth using on a real team?
