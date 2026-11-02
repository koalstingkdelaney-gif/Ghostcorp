# CI

Intended GitHub Actions workflow (add as `.github/workflows/ci.yml` once the
repo token has the `workflow` scope — see PROVIDER_SETUP.md):

```yaml
name: ci
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt
      - run: pytest -q
```

Until then, CI is run locally before every push: `pytest -q` must be green.
