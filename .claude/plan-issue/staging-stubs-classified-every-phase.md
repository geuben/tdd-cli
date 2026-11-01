- `staging.classify` puts a declared `stub_expected` file in `stubs` in **every** phase, not only
  RED. So at GREEN a stub-then-fill cycle has `classification.implementation == []`, and so does
  an ancillary-only GREEN. A GREEN-side check written as "no implementation" fires on ordinary
  correct cycles; "every staged path is in `classification.tests`" does not (#235, probed).
