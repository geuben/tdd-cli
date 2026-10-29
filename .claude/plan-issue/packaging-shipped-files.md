- Only `src/tddcli` is packaged. Anything else the installed binary reads (docs, skills, hook
  scripts) needs a `force-include` line to `tddcli/_docs/<path>` *and* its top directory in the
  sdist `include`, and is read through `docs._PACKAGED` then `docs._SOURCE`. CI's wheel smoke test
  only runs `tdd --help`, so a missing force-include passes CI. Pair a static guard test over
  `pyproject.toml` (like `test_every_topic_is_carried_into_the_wheel`) with a local wheel check
  in Done-criteria: `uv build -o /tmp/x && uv venv /tmp/v && VIRTUAL_ENV=/tmp/v uv pip install
  /tmp/x/*.whl` works offline here. Before #114 the hook `.py` files were not in the wheel at all.
