# Claim Gate

Agent says *done*. The gate does not take that as evidence.

`ADMIT` / `REJECT` / `INCOMPLETE` + witness + receipt.

## Run locally

```bash
python3 claimgate.py --self-check
python3 gate.py --claim fixtures/reject-balance.json
```

`gate.py` is the judge. `claimgate.py --self-check` is the fixture demo.

## Live proofs (do not merge the REJECT ones)

- Product demo REJECT: https://github.com/kosza123/claim-gate/pull/1
- Consumer REJECT: https://github.com/kosza123/claim-gate-demo/pull/1
- Consumer ADMIT: https://github.com/kosza123/claim-gate-demo/pull/2

## Install in another repo

See `INSTALL.md`. Both repos are private, so `uses: kosza123/claim-gate@main` needs:
Settings → Actions → General → Access → accessible from repos owned by kosza123.
Until then, copy `gate.py` (what the demo repo does).

Hamada / `kosza123-semantic-language-2045` was copied, not edited.
