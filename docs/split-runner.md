# Split mode: a ledger the agent cannot reach

On a single-user machine the ledger is a SQLite file owned by the account that runs
`tdd`, which is the account the agent runs as. The agent cannot reach it by editing its
worktree, but it can reach it by looking: `sqlite3 ~/.local/share/tdd-cli/*.sqlite3`
opens it, and nothing in the file says afterwards that anyone did. `tdd doctor` reports
this as `mode: single` and says so in its `ledger isolation` check.

Split mode moves the ledger, and the process that observes the tests, to a second
account:

- A **runner** account owns the ledger, in a directory only it can open (mode 700).
- The agent's `tdd` does nothing itself except `docs` and `init`. For every other verb
  it asks the runner, through `sudo`.
- The runner runs every suite, gate, artifact hook and git command **as the agent**,
  in the agent's worktree, and reads the results from outside. The agent's code never
  runs as the account that owns the ledger.

The command surface is unchanged. No verb accepts a phase, a cycle number or an
identity on either side of the boundary.

This is one machine's arrangement. Each machine has its own runner and its own ledger.

## What it does and does not protect

It stops the agent's account from reading or writing the ledger, and from running code
as the account that can.

It does not stop:

- **A forged test report.** The suite runs as the agent, so a test can write whatever
  report it likes. The runner parses reports as data and never executes them, but it
  cannot know a passing report is honest. This is the same on a single-user machine.
- **A client-side downgrade.** An agent can point its own `tdd` at a config of its own
  (`TDD_RUNNER_CONFIG`), or install a second copy of tdd-cli, and record a run in a
  ledger it owns. Nothing is forged by that: the run is simply absent from the runner's
  ledger, which is the only one to trust. Read runs from the runner's ledger.

## Setup

You need root for this. Examples use `tdd-runner` for the runner account and `agent1`
for the agent's.

### 1. The runner account

Create a system account with a home directory and no login shell you hand out.
On Linux: `useradd --system --create-home --shell /usr/sbin/nologin tdd-runner`.
On macOS: `sysadminctl -addUser tdd-runner -home /var/tdd-runner` (then hide it if you
wish).

### 2. Install tdd-cli where the agent cannot write

A runner whose code the agent can edit is the agent. Install for the runner as root:

    python3 -m venv /opt/tdd-cli
    /opt/tdd-cli/bin/pip install tdd-cli

It must be readable and executable by the agent's account: the runner runs small
helpers from this install *as the agent* (`python -m tddcli.agentfs`,
`python -m tddcli.identity`). It must not be writable by it.

The agent's own `tdd` can be this same binary or a separate install; both read the same
config and become a client.

### 3. sudoers

Two lines, in a file under `/etc/sudoers.d/` (edit with `visudo -f`):

    agent1      ALL=(tdd-runner) NOPASSWD: /opt/tdd-cli/bin/tdd
    tdd-runner  ALL=(agent1)     NOPASSWD:SETENV: ALL

The first lets the agent ask the runner, and only through that one binary. The second
lets the runner act as the agent. Add one pair per agent account.

Four things to get right:

- **`SETENV:` is required** on the second line. The runner passes the agent's own
  environment to the agent's commands with `sudo -E`; without the tag sudo answers
  "sorry, you are not allowed to preserve the environment" and `tdd doctor` fails its
  `runs as the agent` check.
- **`NOPASSWD` is required on both.** `tdd` always passes `-n`, so a rule that would
  prompt fails at once instead of hanging an unattended agent.
- **Leave `env_reset` on** (it is sudo's default). It is what strips the agent's
  `TDD_LEDGER_HOME`, `TDD_RUNNER_CONFIG` and `PYTHONPATH` on the way to the runner.
- **Nothing to configure for `HOME` or the working directory.** The client passes `-H`,
  because macOS sudo would otherwise leave `HOME` pointing at the agent's and the
  runner's ledger home would follow it. sudo keeps the caller's working directory, which
  is how the runner knows which worktree it was asked about.

### 4. The config file

`/etc/tdd-cli/runner.toml`, owned by root, mode 644:

    [runner]
    user        = "tdd-runner"
    command     = "/opt/tdd-cli/bin/tdd"   # the path the first sudoers line names
    # sudo      = "/usr/bin/sudo"          # the default
    # ledger_home = "/var/lib/tdd-cli"     # default: ~tdd-runner/.local/share/tdd-cli

    [executor]                             # optional, see "Executor identity"
    agent1 = "claude-fable-5-1"

A process whose account is `user` is the runner. Every other process on the machine is
a client. With no file, the machine is single-user and nothing changes.

**The file is trusted only if it is owned by root or by the account reading it, and is
not group- or world-writable.** Anything else is refused. That is what stops an agent
handing the runner a config of its own: even if a sudoers rule let `TDD_RUNNER_CONFIG`
through, the file it named would belong to the agent, and the runner refuses it.

### 5. Let the runner read the worktree

The runner reads the worktree as itself: `tdd.toml`, the test files it globs for, JUnit
XML under `build/`. The agent's worktree, and the directories above it, must be readable
and traversable by the runner account (`chmod -R go+rX`, or a shared group). On macOS
that rules out `~/Desktop`, `~/Documents` and `~/Downloads`, which are mode 700.

The runner never writes there as itself. Commits, the friction log, sensitivity-check
restores and temporary probe worktrees are all made as the agent.

If a file is unreadable the runner says which, with `reason: "worktree_unreadable"`.

## Verify it

Run these as the agent's account, in a worktree:

1. `tdd doctor` reports `mode: "split"`, `healthy: true`, and these three checks `ok`:
   - `runs as the agent`: `id -u`, asked through sudo, answered with the agent's uid.
   - `ledger out of the agent's reach`: `test -r <ledger>`, as the agent, was refused.
   - `install not writable by the agent`: `test -w <install>`, as the agent, was refused.
2. `cat ~tdd-runner/.local/share/tdd-cli/*.sqlite3` (or your `ledger_home`) is denied.
3. Start a run and close a cycle. `git log -1 --format='%an %cn'` shows the agent as
   author and committer, and `ls -l` on the committed files shows the agent as owner.
4. `sudo -u tdd-runner /opt/tdd-cli/bin/tdd status`, run by hand from the agent's
   account, works; the same command naming any other binary is denied.

The project's own test suite cannot do this for you. It runs without root, so it uses a
stand-in for sudo that does everything except change uid. The three doctor checks are
the only place the uid change itself is verified, and they run against your real sudo.

## Executor identity

`tdd run start` records which model did the work. Everything it reads on a single-user
machine (the session id, the transcript, `TDD_EXECUTOR_MODEL`) is the agent's to write,
so in split mode the runner trusts none of it:

- If the calling account is in `[executor]`, the run records that model with
  `executor_source: "operator"`. One account per agent slot makes this exact.
- Otherwise the ordinary resolution runs on the agent's side and the run records what
  it found with `executor_source: "claimed"`. Leave `claimed` runs out of any comparison
  between models that has to be defended.

`--executor`, the human label, is a claim like any other in split mode.

## Existing ledgers

A ledger written before the split was reachable by the agent the whole time. The runner
can keep it, marked as such. From a root shell (so that sudo reports uid 0), or logged
in as the runner with no sudo at all:

    sudo -u tdd-runner /opt/tdd-cli/bin/tdd runner import /home/agent1/.local/share/tdd-cli/<repo>.sqlite3

The runner must be able to read that file. It copies the ledger into the
runner's home under the same name, migrates it to the current schema, and records
`pre_split_import` with the source path, the time, and `last_run_id`. `tdd metrics`
reports that marker, so anyone comparing runs can see which predate the split.

It refuses when:

- the machine is not split, or the caller is not the runner (`not_split`);
- an agent's account is the caller (`operator_only`): an agent that could import could
  hand the runner a history it wrote itself;
- the runner already holds a ledger of that name (`ledger_exists`). There is no merge.
  The runner's copy may hold runs recorded out of the agent's reach, and a second import
  would trade them for ones that were not.

Afterwards, remove the agent's copy so that nothing reads it by mistake.

## Fleet, leases and other details

- Worker leases move with the runner: they live under the runner's `~/.cache/tdd-cli`,
  so one budget covers every agent account on the machine.
- `tdd fleet`, `tdd metrics` and `tdd log render` are forwarded like everything else
  and read the runner's ledger.
- A runner invoked directly, with no sudo in between, acts for nobody: every verb
  except `runner import` and `ledger` is refused with `reason: "no_agent"`. It never
  falls back to running suites as itself.

## Across a VM boundary

Everything above is one machine. Once agents run in disposable VMs or containers, the
runner has to be in the guest, because that is where the suites run. Its ledger must not
be: it would be deleted with the guest, two guests' files could never be merged, and an
agent with root in the guest (a `docker` group membership is enough) could rewrite it
whatever the file modes say.

So the runner in the guest keeps **no ledger**. It reads and writes the host's through a
unix socket, served by a **ledger service** on the host. The service owns the SQLite
files and is their only writer. The runner still runs every suite, gate and git command
as the agent, in the agent's worktree, exactly as above.

    host                                         guest (one per run)
    ┌──────────────────────────────┐             ┌──────────────────────────────┐
    │ tdd ledger serve             │             │ agent ─sudo─▶ runner          │
    │   admin.sock   (operator)    │             │                ledger_socket │
    │   vm-1.sock ───forwarded──────────────────▶│ /run/tdd-cli/ledger.sock     │
    │   <home>/<repo>.sqlite3      │             │ (no ledger file here)        │
    └──────────────────────────────┘             └──────────────────────────────┘

A run's **source** is the socket it arrived on. The operator names it when they create
the socket, and the protocol has no field in which a guest could name it instead.

### The service

`/etc/tdd-cli/ledger.toml` (or `TDD_LEDGER_SERVICE_CONFIG`), owned by root or the
service account and not group- or world-writable, the same trust rule as `runner.toml`:

    [service]
    admin_socket = "/run/tdd-cli/admin.sock"
    # home       = "/var/lib/tdd-cli"     # default: the service account's ~/.local/share/tdd-cli

Run `tdd ledger serve` under a dedicated account that owns `home`. It runs until SIGTERM
and exits 0. A systemd unit:

    [Unit]
    Description=tdd-cli ledger service

    [Service]
    User=tdd-ledger
    Group=tdd-guests
    RuntimeDirectory=tdd-cli
    ExecStart=/opt/tdd-cli/bin/tdd ledger serve
    KillSignal=SIGTERM

    [Install]
    WantedBy=multi-user.target

Host ledgers are `<home>/<slug>.sqlite3`, one per repository, where the slug is the
guest's repository path with `/` replaced by `-`, as on a single machine. Every guest
that checks a repository out at the same path shares that file, kept apart by source.

### One source per guest

The operator adds a source for each guest, from the host:

    tdd ledger add-source vm-1 --socket /run/tdd-cli/vm-1.sock --executor claude-fable-5-1
    tdd ledger bind vm-1 --executor claude-opus-5-5     # the model for its next runs
    tdd ledger sources                                   # every source, socket and binding
    tdd ledger remove-source vm-1                        # closes the socket; its runs stay

Sources are kept in `<home>/sources.json`, so a restarted service listens on all of them
again. The admin socket is mode 600, the service account's alone. A guest's socket is
mode 660: give its group to whatever forwards it into the guest, and nothing else.

`tdd ledger` verbs are always answered on the machine you run them on, never forwarded to
a runner. With no service config they fail with `reason: "no_service"`.

### Forwarding the socket into the guest

The forwarding itself is the operator's, and tdd-cli does not set it up:

- **ssh**: `ssh -R /run/tdd-cli/ledger.sock:/run/tdd-cli/vm-1.sock guest`, with
  `StreamLocalBindUnlink yes` in the guest's `sshd_config` so a reconnect can replace a
  stale socket, and `StreamLocalBindMask 0117` so the forwarded socket is not world-open.
- **containers**: bind-mount the source's socket, `-v /run/tdd-cli/vm-1.sock:/run/tdd-cli/ledger.sock`.
  Mount the one socket, never the host's ledger directory.
- **vsock**: forward the source's socket to a vsock port with a relay such as `socat`,
  and relay it back to a unix socket in the guest.

### The guest

The guest's `runner.toml` names the forwarded socket instead of a ledger home:

    [runner]
    user          = "tdd-runner"
    command       = "/opt/tdd-cli/bin/tdd"
    ledger_socket = "/run/tdd-cli/ledger.sock"   # instead of ledger_home

Naming both `ledger_socket` and `ledger_home` is refused. In the guest, `tdd doctor`'s
`ledger reachable` check pings the service and names the source it reached:
`socket /run/tdd-cli/ledger.sock (source vm-1)`.

**It fails closed.** If the socket is missing or the service hangs up, every verb that
needs the ledger fails with `reason: "ledger_unreachable"`. Nothing in the guest ever
falls back to a ledger of its own.

### What it does and does not protect

The service enforces this for every request, so a modified client cannot get around it:

- **A guest reads and writes only its own source's runs.** A run, cycle or plan contract
  of another source is refused with `refusal: "foreign_run"`, and so is one that does not
  exist, so a guest cannot probe for other sources' ids. Claims and the baseline cache
  are per source: one guest can neither block another's `run start` at the same path nor
  hand it a forged cached baseline.
- **A closed run stays closed.** Writes to a `complete` or `abandoned` run are refused with
  `refusal: "run_closed"`. `tdd note` is the one exception, so a closing narrative can still
  be added. A `blocked` run is not closed: `resume --unblock` still works.
- **A guest reaches only named domain methods.** The wire carries a method name and its
  arguments, never SQL. Methods meant for the host alone (`set_meta`, the generic row
  helpers) are refused with `refusal: "method_not_allowed"`, and a repository path that is
  not absolute is refused with `refusal: "bad_repo"`.

Refusals reach the guest's envelope as `reason: "ledger_refused"` with the `refusal` code.

What a compromised guest can still do is record runs under its own source, and lie in
them, which is no worse than a forged test report on a single machine.

**Executor identity is set on the host.** A guest's `[executor]` table is guest root's to
edit, so it is a claim. When the operator binds an executor to a source, the service
records that model with `executor_source: "operator"` on every run the source starts or
abandons, whatever the guest sent. With no binding, a guest that says `operator` is
recorded as `claimed`.

### One history per host

On the host, the operator reads every source together through the admin socket:

    tdd ledger metrics [--repo <slug>]              # `tdd metrics` over every source, per repository
    tdd ledger fleet                                # active runs of every source, and the host's suites
    tdd ledger log --repo <slug> --run <id> [--out FILE]

Every run in them carries its `source`. Inside a guest, `tdd metrics`, `tdd fleet` and
`tdd log render` still work, and see only that guest's source.

**Worker leases are the host's.** A socket-mode runner takes each suite's worker lease
from the service, which splits the host's cores across every guest's running suites. A
lease ends when its connection closes, which is also what a dead VM does, and one older
than the stale limit is not counted. Named leases stay in the guest: they guard
resources the guest's suites run against.

### Existing ledgers

`tdd runner import` is refused on a socket-mode runner (`reason: "ledger_remote"`): it has
no ledger to import into. Bring an existing ledger in on the host instead, as one source:

    tdd ledger import /home/agent1/.local/share/tdd-cli/<repo>.sqlite3 --source legacy

It copies the file into the service's home under the same name, migrates it, retags every
run and plan contract it recorded to the named source, drops its claims, and marks it as
`pre_split_import`, which `tdd ledger metrics` reports. It refuses a file the host already
holds (`reason: "ledger_exists"`). There is no merge.

Ledgers from before schema v13 gain a source on their first open: every existing run,
contract, claim and cached baseline becomes `local`, the source of single-user mode and of
a split runner on one machine.
