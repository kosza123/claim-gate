# Install Claim Gate in another repo

```yaml
- uses: actions/checkout@v4
- uses: kosza123/claim-gate@main
```

Need `LAW.md` + `claim.json` on the PR.
`REJECT` / `INCOMPLETE` blocks merge.

Access is already set: Actions in other private repos owned by kosza123 can pull this Action.
Proof: https://github.com/kosza123/claim-gate-demo/pull/3 (no local `gate.py`).
