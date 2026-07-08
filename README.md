# propro

Quick calculation and visualization of biochemical/biophysical properties of proteins — built for fast, "do I know what I'm working with" checks before or during wet-lab work, not for deep or slow computational analyses.

## Quick start

```bash
pip install -r requirements.txt

python examples/quick_overview_example.py
```

```python
from propro.core.sequence import ProteinSequence
from propro.core.properties import compute_overview
from propro.core.report import print_report
from propro.core.visualize import plot_net_charge_vs_ph

protein = ProteinSequence("MKTVWCCYHDEK...", id="my_protein")
overview = compute_overview(protein)

print_report(overview)                  # bench-sheet-style text report
plot_net_charge_vs_ph(overview, save_path="charge_vs_ph.png")
```

## Installation

- Python >= 3.9
- Dependencies: `biopython`, `pandas`, `matplotlib`, `tabulate` (see `requirements.txt` / `pyproject.toml`)
- `pip install -e .` for an editable install, or `pip install -r requirements.txt` to just install dependencies and run from the repo.

## Modules

- **`propro.core`** — general-purpose, sequence-first property calculators and visualizers that apply to any protein.
  - `sequence.py` — `ProteinSequence`: sequence container with optional per-residue numbering (supports non-standard numbering schemes, e.g. from a structure or antibody numbering).
  - `properties.py` — `compute_overview()`: the quick-overview calculator (see below). Wraps `Bio.SeqUtils.ProtParam.ProteinAnalysis`.
  - `report.py` — text report, pandas DataFrame, and Markdown renderings of an overview.
  - `visualize.py` — net-charge-vs-pH and amino-acid-composition plots.
- **`propro.motifs`** — protein-class-specific tooling.
  - `nanobodies/` — VHH-specific tooling. Implemented: IMGT CDR1/2/3 annotation + property summary, as a Google Sheets script (`gscripts/cdr_annotation.gs`) and an Excel/VBA macro (`excel/cdr_annotation.bas`); see each folder's README for layout and install steps.
  - `antibodies/`, `enzymes/`, `complexes/` — *(not yet implemented)*.
- **`propro.interfaces`** — interfaces to external platforms/output formats that aren't tied to one motif.
  - `pdf_reports/` — render results as standalone PDFs. Implemented: `sequence_overview_pdf.py`, a one-page overview for any sequence (`python -m propro.interfaces.pdf_reports.sequence_overview_pdf`).
  - `gscripts/` (Google Sheets), `excel/`, `pymol/` — generic platform glue; *(scaffolded)*.

### Where motif + interface code lives

Some tooling is specific to both a protein class *and* an external platform (e.g. the nanobody CDR annotator is nanobody biology wrapped in a Google Sheets script). propro resolves this by organizing **by motif first**: a motif's interface-facing code lives inside that motif's own directory (`propro/motifs/<motif>/gscripts/`, `.../excel/`, `.../pymol/`, ...), alongside its Python code. `propro/interfaces/` is reserved for platform glue that is genuinely generic across motifs (like `pdf_reports/`, which works on any sequence). Per-platform registries index every script of that kind regardless of where it physically lives: `interfaces/gscripts/REGISTRY.md` (Google Sheets scripts), `interfaces/excel/REGISTRY.md` (Excel macros).

## `bench tools/`

Turnkey scripts you run directly to get a practical output — not part of the installable `propro` package (only `propro*` is packaged; see `pyproject.toml`), but built on top of it. See `bench tools/README.md` for how this differs from `propro.motifs`/`propro.interfaces`. Currently a placeholder: the one-page PDF report that used to live here now ships in the library as [`propro.interfaces.pdf_reports`](propro/interfaces/pdf_reports/).

## Quick overview: what `compute_overview()` returns

Given a sequence, `compute_overview()` returns a `ProteinOverview` with:

| Property | Notes |
|---|---|
| Position | Residue numbering range covered (1-based by default, or custom numbering if supplied) |
| Summary | First/last N residues shown, plus total residue count |
| Molecular weight | Da |
| Isoelectric point (pI) | |
| Extinction coefficient (280 nm) | Both Cys-fully-reduced and Cys-fully-oxidized (all Cys as cystines), in M⁻¹cm⁻¹, plus the corresponding A(280 nm) for a 1 mg/mL solution |
| Instability index | Guruprasad et al. classification: ≤ 40 "stable", > 40 "unstable" |
| Amino acid frequencies | Count and percentage of each of the 20 standard residues (plus any ambiguous residues present) |
| Net charge vs. pH | Titration-style curve across a configurable pH range |

Ambiguous/non-standard residues (X, B, Z, J, U, O) are excluded from the numeric calculations (they aren't defined for the standard formulas) — how many were excluded is recorded on the result and surfaced in reports.

## Tests

```bash
pytest tests/
```

Property-engine tests (`tests/test_properties.py`) require BioPython and skip automatically if it isn't installed. Sequence/report/visualization tests have no BioPython dependency and always run.

## Status

Early / actively developed. `propro.core` (quick-overview functionality) is implemented. `propro.motifs.nanobodies` has its first tool (CDR annotation + property summary, for Google Sheets and Excel); `propro.interfaces.pdf_reports` has its first tool (one-page sequence overview PDF). Other motifs and the remaining `propro.interfaces` platforms (generic `gscripts`/`excel`/`pymol` glue) are scaffolded placeholders for planned work.
