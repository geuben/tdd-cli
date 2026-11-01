- A cycle commits only in the phases its kind has, so declare only those `commit_*` keys:
  standard and contract `commit_red`/`commit_green`/`commit_refactor`; pin `commit_pin` and
  `commit_refactor` (a pin does commit in its refactor phase); refactor `commit_refactor`.
  Fifteen pin cycles in `tasks/` declared `commit_red`, which the run never read: they committed
  as `test: pin <title>`. Once #231 lands (`tasks/issue-231-commit-keys-per-cycle-kind.md`),
  `plan register` refuses any other key as a malformed contract. The released referee may not
  refuse it yet, so check by hand. A test plan template formatted as more than one kind
  (`tests/test_suite_scope.py`'s `PLAN`) must carry no commit keys, or only those every kind it
  becomes accepts.
