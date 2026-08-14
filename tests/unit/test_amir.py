"""Unit tests for the amir product-suite meta-package."""

from __future__ import annotations

from assertpy import assert_that

from amir import __version__


def test_version__is_semver_like() -> None:
    assert_that(__version__).matches(r"^\d+\.\d+\.\d+$")
