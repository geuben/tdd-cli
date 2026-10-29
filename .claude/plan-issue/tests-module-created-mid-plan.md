- When several cycles share one new test file and a *later* cycle's GREEN creates a module some
  of its tests use, import that module inside those test functions, never at module top. A
  top-level import breaks collection of the whole file, so every earlier cycle's RED dies
  `not_collected` instead of failing on its assertion (#114: `tddcli.harness`).
