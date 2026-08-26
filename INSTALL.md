# Install Claim Gate in another repo

Do not copy the engine. Point at this repository.

## 1. Add a law

Create `LAW.md` in the consumer repo.

## 2. Add the Action

`.github/workflows/claim-gate.yml`:

```yaml
name: Claim Gate
on: pull_request
permissions:
  contents: read
  pull-requests: write
jobs:
  gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: kosza123/claim-gate@main
```

## 3. Attach claim.json when an agent claims success

`REJECT` or `INCOMPLETE` fails the check. Merge stays blocked.
