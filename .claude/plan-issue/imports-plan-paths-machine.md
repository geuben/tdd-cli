- `plan_paths.py` imports `Engine` from `machine.py` at module level, so anything in `machine.py`
  that uses `plan_paths` must import it inside the function (`from . import plan_paths`). A
  module-level import is a circular import at CLI start (#73).
