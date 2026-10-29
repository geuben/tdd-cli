- A new guest-visible `Ledger` method must take `run_id`, `cycle_id` or `contract_id`
  (`test_every_ledger_method_is_classified_and_scoped`), because those are the only parameters
  `service._Session._foreign` checks. A method keyed by any other id (#105: `invocation_id`)
  needs a new owner in `_foreign` *and* the name in that test's `OWNERSHIP` set, in the same
  cycle, with a service test proving the refusal. Until that cycle, classify the method
  `HOST_ONLY`: adding the name to `OWNERSHIP` without the service check is a guard that claims
  enforcement nothing performs. Reads are refused for unknown ids the same way as for foreign ones,
  so ids cannot be probed. New keyword arguments on an existing guest write break a socket-mode
  host on the previous release (`inspect.signature(fn).bind`): say so in the CHANGELOG.
