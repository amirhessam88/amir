"""Package metadata smoke tests."""

from assertpy import assert_that

from papers_ingest import __version__


def test_version__is_semver_like() -> None:
    assert_that(__version__).matches(r"^\d+\.\d+\.\d+$")
