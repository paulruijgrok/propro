# gscripts registry

Every Google Apps Script in propro, regardless of which directory it physically lives in. Motif-specific scripts live inside their motif (see `propro/motifs/<motif>/gscripts/`); this file is the single place to find all of them.

| Script | Location | Sheet tab / columns | What it does |
|---|---|---|---|
| `cdr_annotation.gs` | `propro/motifs/nanobodies/gscripts/` | tab `nanobodies`; reads `AA Sequences`, writes `CDR1`/`CDR2`/`CDR3` + auto-creates `pI`, `MW (kDa)`, `Ext coeff (M-1 cm-1)`, `A280 (1 mg/mL)` | Annotates IMGT CDR1/2/3 loops for VHH sequences via conserved-residue anchoring; color-codes CDRs in the sequence cell; adds a per-CDR grey stats line (net charge @ pH 7.4 + hydrophobic/polar/charged counts); computes ProtParam-equivalent bulk properties (pI, MW, extinction & A280 for reduced + oxidized states). |

Add a row here whenever a new gscript is added anywhere in the repo (in a motif's `gscripts/` folder or in `propro/interfaces/gscripts/` itself).
