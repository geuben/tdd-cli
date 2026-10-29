- Once #97 lands (`tasks/issue-97-delivered-plan-refusal.md`), `run start` refuses a plan path any
  completed run of this source has delivered (`plan_already_delivered`), whatever its blob. A test
  that completes a run (`cycle skip` on the last cycle, or a full run) and then starts another
  must register the second run's plan under a new path (`write_plan(repo, PLAN,
  "tasks/plan-again.md")`), or its second `start` is refused. Blocked, abandoned and refused runs
  do not count. Before #97, one test did this (`test_abandon_refuses_a_run_that_already_ended`).
