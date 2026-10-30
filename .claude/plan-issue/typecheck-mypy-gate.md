- Once #210 lands (`tasks/issue-210-mypy-typecheck.md`), `uv run mypy` is `tddcli`'s `typecheck`
  gate and a CI `lint`-job step. It runs in default mode over `src` and `tests`, configured by
  `[tool.mypy]` in `pyproject.toml`. Every cycle's stub and GREEN must type-check, or the close
  sweep replies `fix_regression`. A new third-party import without inline types needs its stub
  package (`types-*`) in the dev group and `uv.lock`, in the same cycle: `import yaml` without
  `types-PyYAML` is an `import-untyped` error. `Ledger.one`, `Ledger.run` and `Ledger.contract`
  return `Row | None`, so a test or a module that indexes the result narrows it first.
