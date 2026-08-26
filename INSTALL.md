# Install Claim Gate in another repo

## Preferred

```yaml
- uses: actions/checkout@v4
- uses: kosza123/claim-gate@main
```

If both repos are private, this fails until you open access:

`claim-gate` → Settings → Actions → General → Access →
**Accessible from repositories owned by kosza123**

## Fallback (what claim-gate-demo uses today)

Copy `gate.py` into the consumer and run:

```yaml
- uses: actions/checkout@v4
- uses: actions/setup-python@v5
  with:
    python-version: "3.12"
- run: python3 gate.py --claim claim.json --law LAW.md --out out || true
- uses: marocchino/sticky-pull-request-comment@v2
  with:
    header: claim-gate
    path: out/comment.md
- run: test "$(tr -d '\n' < out/verdict.txt)" = "ADMIT"
```

Need `LAW.md` + `claim.json` on the PR.
`REJECT` / `INCOMPLETE` blocks merge.
