- `render.py` must read `plan_contract.declared_cycles` as raw dicts (`json.loads` plus `.get`),
  never through `contract.cycles_from_json`: `tests/test_time_report.py`'s fixture ledger stores
  bare `[{"n": 1}, {"n": 2}]`, and `DeclaredCycle.from_dict` raises `KeyError` on the missing
  `kind`/`projects`. A new per-cycle field read at render time needs a `None` default for the
  same reason, and for contracts registered by an older tool (#76).
- Nothing tested the `annotate_cycle` close gate end to end before #76. A refactor cycle is the
  cheapest way to reach it: it opens in `AWAITING_REFACTOR`, and `_handle_refactor` checks
  missing annotations before it stages anything.
