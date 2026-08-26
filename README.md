# Claim Gate

Agent says *done*. The gate does not take that as evidence.

ADMIT / REJECT / INCOMPLETE + witness + receipt.

## Run locally

    python3 claimgate.py --self-check
    python3 gate.py --claim fixtures/reject-balance.json

## Live proofs (do not merge REJECT / INCOMPLETE)

- Product REJECT: https://github.com/kosza123/claim-gate/pull/1
- Product INCOMPLETE: https://github.com/kosza123/claim-gate/pull/3
- Consumer via Action: https://github.com/kosza123/claim-gate-demo/pull/3
- Famada false SUCCESS: https://github.com/kosza123/Famada-AI-progress-Agents/pull/1
- Famada install (merged): https://github.com/kosza123/Famada-AI-progress-Agents/pull/2
- VOLT exfil REJECT: https://github.com/kosza123/VOLT/pull/1

## Install in another repo

    - uses: actions/checkout@v4
    - uses: kosza123/claim-gate@main

Hamada / kosza123-semantic-language-2045 was copied, not edited.
