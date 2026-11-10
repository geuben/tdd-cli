- A flag that only restores today's output (`doctor --all`, #253) cannot be its own cycle: stub
  it and the test passes on arrival; don't stub it and the RED dies in `json.JSONDecodeError`.
  Stub the flag in the RED of the cycle that narrows the default (`stub_expected: cli.py`),
  and in that same RED move every test that reads the narrowed-away output onto the flag.
  They keep passing on the stub, and once GREEN filters they are what demands the flag.
  Find those tests by simulating the narrowing in a scratch worktree (#253: 22 ids, all fixed
  by adding the flag alone).
