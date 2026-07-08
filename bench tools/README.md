# bench tools

Curated, ready-to-run scripts for quick, practical outputs you'd actually reach for at the bench — built on top of the `propro` library, but not part of the installable package itself (see `pyproject.toml`: only `propro*` is packaged). Run these directly from a clone of this repo after `pip install -e .` so `propro` is importable.

This is a different axis from `propro/motifs` and `propro/interfaces`: those organize the *library* (reusable Python code, optionally with motif-specific interface glue). `bench tools/` organizes *turnkey scripts* — the thing you'd run once to get an answer, not import into other code. A tool in here can freely use anything from `propro.core`, `propro.motifs`, or `propro.interfaces`.

## Categories

_None yet._ This folder is a placeholder for future turnkey scripts that genuinely shouldn't be importable library code (e.g. quick structure checks, batch sequence triage). Each will get its own subfolder here as it shows up.

## Moved out

- **PDF reports** — the one-page sequence-overview PDF used to live here under `reports/`. It moved into the library at [`propro/interfaces/pdf_reports/`](../propro/interfaces/pdf_reports/) because a PDF is an output interface (parallel to `gscripts`/`pymol`) and the tool applies to any sequence, so it's more discoverable and reusable as `propro.interfaces.pdf_reports`. Run it with `python -m propro.interfaces.pdf_reports.sequence_overview_pdf`.
