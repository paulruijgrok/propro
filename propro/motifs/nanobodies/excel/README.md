# Nanobody CDR annotation + property summary (Excel / VBA)

`cdr_annotation.bas` is the Microsoft Excel equivalent of the Google Sheets script in [`../gscripts/cdr_annotation.gs`](../gscripts/cdr_annotation.gs). It annotates IMGT CDR1/CDR2/CDR3 loops for VHH (nanobody) sequences and computes a set of quick biophysical properties, directly inside a workbook — no external tools, no Python required.

It runs in **Excel for Windows and Excel for Mac**. The CDR anchor logic is implemented with plain string scans rather than `VBScript.RegExp`, which is unavailable on Mac.

> Excel-on-the-web (Office Scripts) can't color individual characters within a cell, so it can't reproduce the per-residue CDR coloring. Use the desktop app for this macro.

## What it does

On a worksheet named `nanobodies`, in a single run of `AnnotateNanobodyCDRs`:

1. Reads each sequence from the `AA Sequences` column (tolerant to common header spellings, e.g. `Sequence`, `AA Seq`).
2. Extracts CDR1 / CDR2 / CDR3 into the `CDR1`, `CDR2`, `CDR3` columns, each colored (CDR1 red, CDR2 green, CDR3 blue). Below the residues of each CDR cell it adds a compact grey stats line — `q<±charge>  φ<n> · pol<n> · chg<n>` — the loop's net charge at pH 7.4 and the number of hydrophobic (φ), polar-uncharged (pol) and charged (chg) side chains.
3. Recolors the AA-sequence cell so each CDR shows in its own font color (frameworks stay default). Note: the sequence cell is rewritten as the cleaned, uppercased sequence so the coloring lines up.
4. Writes whole-sequence bulk properties to their own columns, creating any that don't exist yet at the end of the header row:
   - `pI` — isoelectric point
   - `MW (kDa)` — molecular weight
   - `Ext coeff (M-1 cm-1)` — molar extinction coefficient at 280 nm, given for both the oxidized (`ox:`, disulfides formed) and reduced (`red:`) state
   - `A280 (1 mg/mL)` — absorbance of a 1 mg/mL (0.1%) solution, again `ox:` / `red:`

### Residue classification (per-CDR counts)

- Hydrophobic (φ): A, V, L, I, M, F, W, Y, C
- Polar, uncharged (pol): S, T, N, Q, H, G
- Charged (chg): D, E, K, R

His is counted as polar but still contributes (partially) to net charge, which uses Henderson–Hasselbalch on the side chains only (a CDR is an internal fragment, so its ends are not treated as real termini).

## Method

Identical to the Sheets version:

- **CDR boundaries** — conserved-residue anchoring: CDR1 between Cys23 and the FR2 Trp41; CDR3 between Cys104 and the WGxG/FR4 motif; CDR2 a fixed offset after Trp41 ending at the conserved FR3 motif. CDR1/CDR3 are exact; CDR2's downstream boundary is heuristic — spot-check unusual loops.
- **Properties** — ProtParam-equivalent, verified numerically against BioPython (`Bio.SeqUtils` `IsoelectricPoint` and `molecular_weight`): MW = Σ average residue masses + water; pI = Bjellqvist pKa set, terminus-aware, by bisection; extinction = Tyr·1490 + Trp·5500 (reduced), + (Cys÷2)·125 for cystines (oxidized); A280(0.1%) = extinction ÷ MW. Non-standard residues (X, B, Z, …) are dropped before the numeric calculations.

The regex-free CDR finder was validated to produce identical CDR1/2/3 output to the Sheets regex version across a panel of VHH sequences (including varied loop lengths and a missing CDR3).

## Install / run

1. Open the target workbook and make sure the sequence tab is named `nanobodies`.
2. Open the VBA editor:
   - **Windows:** press `Alt`+`F11`.
   - **Mac:** `Tools > Macro > Visual Basic Editor`.
3. `Insert > Module`, then paste in the contents of `cdr_annotation.bas`.
4. Run `AnnotateNanobodyCDRs` (press `F5`, or `Developer > Macros > AnnotateNanobodyCDRs > Run`).
5. Save the workbook as **`.xlsm`** (macro-enabled) if you want to keep the macro.

## Relationship to the Sheets version

Same biology, same math, same output layout — just a different spreadsheet host. Settings (colors, stats font size, net-charge pH, classification sets) live in the `Const` block at the top of the module, mirroring the `var` settings block in `cdr_annotation.gs`. Keep the two in sync when changing behavior. Both are indexed centrally: gscripts in [`propro/interfaces/gscripts/REGISTRY.md`](../../../interfaces/gscripts/REGISTRY.md), Excel macros in [`propro/interfaces/excel/REGISTRY.md`](../../../interfaces/excel/REGISTRY.md).
