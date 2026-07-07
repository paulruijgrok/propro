# bench tools

Curated, ready-to-run scripts for quick, practical outputs you'd actually reach for at the bench — built on top of the `propro` library, but not part of the installable package itself (see `pyproject.toml`: only `propro*` is packaged). Run these directly from a clone of this repo after `pip install -e .` so `propro` is importable.

This is a different axis from `propro/motifs` and `propro/interfaces`: those organize the *library* (reusable Python code, optionally with motif-specific interface glue). `bench tools/` organizes *turnkey scripts* — the thing you'd run once to get an answer, not import into other code. A tool in here can freely use anything from `propro.core`, `propro.motifs`, or `propro.interfaces`.

## Categories

- **`reports/`** — generate a standalone document (PDF, etc.) summarizing a protein or set of proteins. See `reports/README.md` for the index.

Future categories will get their own subfolder here as they show up (e.g. quick structure checks, batch sequence triage).
