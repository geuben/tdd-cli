- The friction log's text and `tdd metrics`' keys have readers outside this repo. The
  user-level `implement-issue` skill reads the header (`Outcome:`, the intervention list), and
  `raise-pr` fills its Interventions section from the friction log. geuben/dispatch reads
  metrics. A plan that renames a line or a key names these consumers in its PR body for their
  owners (#186). The run that implements it renders its own log with the released referee, so
  the old wording holds until the next release.
