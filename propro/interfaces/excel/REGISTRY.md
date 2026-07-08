# Excel macro registry

Every Excel VBA macro in propro, regardless of which directory it physically lives in. Motif-specific macros live inside their motif (see `propro/motifs/<motif>/excel/`); this file is the single place to find all of them. Parallel to `propro/interfaces/gscripts/REGISTRY.md` for the Google Sheets scripts.

| Macro | Entry point | Location | Worksheet / columns | What it does |
|---|---|---|---|---|
| `cdr_annotation.bas` | `AnnotateNanobodyCDRs` | `propro/motifs/nanobodies/excel/` | sheet `nanobodies`; reads `AA Sequences`, writes `CDR1`/`CDR2`/`CDR3` + auto-creates `pI`, `MW (kDa)`, `Ext coeff (M-1 cm-1)`, `A280 (1 mg/mL)` | Excel/VBA equivalent of `cdr_annotation.gs`. Annotates IMGT CDR1/2/3 loops for VHH sequences via conserved-residue anchoring (regex-free, Mac + Windows safe); color-codes CDRs in the sequence cell; adds a per-CDR grey stats line (net charge @ pH 7.4 + hydrophobic/polar/charged counts); computes ProtParam-equivalent bulk properties (pI, MW, extinction & A280 for reduced + oxidized states). |

Add a row here whenever a new Excel macro is added anywhere in the repo (in a motif's `excel/` folder or in `propro/interfaces/excel/` itself).
