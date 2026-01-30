"""Make `tests` a package to allow stable imports from `tests.*` modules in tests.

This file intentionally left minimal to enable imports like
`from tests.common.fake_exifer import FakeExifer` inside test modules.
"""
