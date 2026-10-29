- Every adapter sets `Verdict.error` only with no passed or failed ids, so a gate on
  `verdict.error` at baseline also catches projects that have no suite yet. `repo_multi`'s empty
  vitest `frontend` gets one wherever `npx vitest run` prints no JSON (no vitest on the host), and
  `tests/test_heartbeat.py::test_claim_records_projects_done_as_each_completes` then breaks. PRD
  R9.5a exempts a project with no tests and no collection errors; any new baseline refusal needs
  the same exemption, pinned before the refusal lands (#99).
