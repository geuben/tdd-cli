from tddcli.adapters.base import Verdict
from tddcli import advance


def test_outcome_lookup_returns_none_for_unexecuted_id():
    verdicts = [
        Verdict("p1", "pytest", passed=["p1::tests/test_x.py::test_a"], failed=[]),
        Verdict("p2", "pytest", passed=[], failed=["p2::tests/test_y.py::test_b"]),
    ]
    assert advance._outcome_from_verdicts(verdicts, "backend::tests/test_x.py::test_y") is None
