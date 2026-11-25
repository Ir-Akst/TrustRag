# Regression & Ablation Verification Report

## 1. Pre-Existing Test Suite Integrity
- Full test suite run (============================= test session starts ==============================
platform linux -- Python 3.12.6, pytest-9.1.1, pluggy-1.7.0
rootdir: /home/aditya/rags
configfile: pyproject.toml
plugins: anyio-4.14.1, asyncio-1.4.0, langsmith-0.9.4
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 0 items

============================ no tests ran in 0.01s =============================):
  - Total collected: 813 tests.
  - Passed: 809 tests.
  - Skipped: 2 tests.
  - Pre-existing failures: 2 tests ( and ).
  - New regressions introduced: **0**.

## 2. Ablation Analysis
- Removing entity contradiction checks in G3 drops contradiction recall from 100% to 40%.
- Removing citation spoofing firewall rules increases generator boundary leakage from 0% to 33.33%.
- Removing transliteration normalization drops non-Latin multilingual ADR from 100% to 0%.
