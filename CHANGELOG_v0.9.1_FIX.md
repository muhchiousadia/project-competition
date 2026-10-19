# v0.9.1 Fixes

- Fixed Finance Chat authorization: it now requests the existing read-only `view_agent` permission instead of the undefined `view` action. This resolves `Permission denied: Tier 2 cannot perform view` while preserving role policy.
- Added a regression test confirming Viewer, Analyst, and Owner can open read-only Finance Chat.
- Verification in build environment: `python -m pytest -q` -> 44 passed.

## Notes
- Ollama must be installed separately and the selected model must be downloaded locally.
- Live Ollama inference has not been verified on the user's Windows laptop.
- Use a stable Python version supported by dependencies (recommend Python 3.12 or 3.13 rather than an experimental/newer interpreter).
