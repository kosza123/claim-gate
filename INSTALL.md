# Install

Pin a full commit SHA. `@main` is not an install.

    - uses: actions/checkout@v4
      with:
        fetch-depth: 0
    - uses: kosza123/claim-gate@PIN_SHA

Need `LAW.md` on the **default branch** (base). PR copies of `LAW.md` are ignored.

Need `claim.json` on the PR. Missing claim → INCOMPLETE, not ADMIT.

`REJECT` / `INCOMPLETE` fail the job. Turn on a branch ruleset: required check `gate`, protect `main`.

CODEOWNERS must cover `.github/`, `LAW.md`.
