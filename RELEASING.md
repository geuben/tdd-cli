# Releasing

Publishing uses PyPI [trusted publishing](https://docs.pypi.org/trusted-publishers/):
`release.yml` publishes from the `pypi` GitHub environment; no tokens are stored.

Per release:

1. Update `__version__` in `src/tddcli/__init__.py` (the single source of
   truth — `pyproject.toml` reads it via hatch).
2. Move the `Unreleased` notes in `CHANGELOG.md` under the new version with
   today's date.
3. Commit, PR, merge to `main`; wait for CI to pass.
4. Tag: `git tag vX.Y.Z && git push origin vX.Y.Z`.
5. Create a GitHub Release from the tag (paste the changelog section). Its
   publication triggers `release.yml`, which builds and publishes to PyPI via
   trusted publishing.
6. Verify: `pip install tdd-cli==X.Y.Z && tdd --help`.
