# Claim Gate

Agent says done. The gate does not take that as evidence.

```bash
python3 claimgate.py --self-check
python3 claimgate.py --claim fixtures/reject-balance.json
```

On a pull request the Action comments the verdict and fails closed on REJECT or INCOMPLETE if claim.json is present.
