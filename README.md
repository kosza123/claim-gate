# Claim Gate

Agent says *done*. The gate does not take that as evidence.

`ADMIT` / `REJECT` / `INCOMPLETE` + witness + receipt.

## Run locally

```bash
python3 claimgate.py --self-check
python3 gate.py --claim fixtures/reject-balance.json
```

`gate.py` is the judge. `claimgate.py --self-check` is the fixture demo.

## Live proofs (do not merge REJECT / INCOMPLETE)

- Product REJECT: https://github.com/kosza123/claim-gate/pull/1
- Product INCOMPLETE: https://github.com/kosza123/claim-gate/pull/3
- Consumer REJECT (vendored): https://github.com/kosza123/claim-gate-demo/pull/1
- Consumer ADMIT: https://github.com/kosza123/claim-gate-demo/pull/2
- Consumer REJECT via `uses: kosza123/claim-gate@main`: https://github.com/kosza123/claim-gate-demo/pull/3

## Install in another repo

```yaml
- uses: actions/checkout@v4
- uses: kosza123/claim-gate@main
```

Hamada / `kosza123-semantic-language-2045` was copied, not edited.
