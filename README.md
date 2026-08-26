# Claim Gate

**Label: DEMO_ONLY — NOT_TEAM_READY**

Agent says *done*. That is not evidence.

`ADMIT` / `REJECT` / `INCOMPLETE`. Fail closed.

Trusted: `gate.py`, `action.yml`, `LAW.md` from the **base** ref.
Untrusted: `claim.json` from the PR.

## Run locally

    python3 gate.py --self-check
    python3 gate.py --claim fixtures/reject-balance.json --law fixtures/laws-demo.md

## Live proofs (do not merge REJECT / INCOMPLETE)

- REJECT: https://github.com/kosza123/claim-gate/pull/1
- INCOMPLETE: https://github.com/kosza123/claim-gate/pull/3
- Consumer Action: https://github.com/kosza123/claim-gate-demo/pull/3

## Install

See `INSTALL.md`. Pin a commit SHA. Do not use `@main`.

Hamada / kosza123-semantic-language-2045 was copied, not edited.
