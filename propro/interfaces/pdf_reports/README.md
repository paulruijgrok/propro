# pdf_reports

PDF report generators — they turn propro calculations into a standalone PDF document. A PDF is treated as an output platform, parallel to `interfaces/gscripts` (Google Sheets) and `interfaces/pymol`. These reports apply to any protein sequence and depend only on `propro.core`.

Unlike the motif-specific interface code (which lives inside each motif under `propro/motifs/<motif>/...`), everything here is sequence-agnostic, so it lives directly under `interfaces`.

## Tools

| Tool | Input | Output | What it does |
|---|---|---|---|
| `sequence_overview_pdf.py` | a sequence (string or FASTA) | one-page PDF | Key properties (position, summary, MW, pI, extinction coefficient, instability index), a net-charge-vs-pH chart, and an amino acid frequency table, all on a single page. |

Add a row here whenever a new PDF report tool is added.

## Usage

As a library:

```python
from propro.core.properties import compute_overview
from propro.core.sequence import ProteinSequence
from propro.interfaces.pdf_reports.sequence_overview_pdf import generate_sequence_overview_pdf

overview = compute_overview(ProteinSequence("MKTVWCC...", id="my_protein"))
generate_sequence_overview_pdf(overview, "my_protein_overview.pdf")
```

From the command line (runnable as a module — no need to know the file path):

```bash
python -m propro.interfaces.pdf_reports.sequence_overview_pdf --sequence MKTVWCC... --id my_protein
python -m propro.interfaces.pdf_reports.sequence_overview_pdf --fasta sequences.fasta --outdir reports/
```

Requires `propro` to be importable (`pip install -e .` from the repo root, or run from a checkout with the repo root on `PYTHONPATH`).

## History

This tool previously lived under `bench tools/reports/`. It moved into the library so it sits next to the other output interfaces and is importable/discoverable as `propro.interfaces.pdf_reports`.
