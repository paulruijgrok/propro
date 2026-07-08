# Nanobody CDR annotation + property summary (Google Sheets)

`cdr_annotation.gs` annotates IMGT CDR1/CDR2/CDR3 loops for VHH (nanobody) sequences and computes a set of quick biophysical properties, directly inside a Google Sheet — no external tools, no Python required.

## What it does

On a sheet tab named `nanobodies`, in a single run of `annotateNanobodyCDRs`:

1. Reads each sequence from the `AA Sequences` column (tolerant to a few common header spellings, e.g. `Sequence`, `AA Seq`).
2. Extracts CDR1 / CDR2 / CDR3 and writes them into the `CDR1`, `CDR2`, `CDR3` columns. Below the residues of each CDR cell it adds a compact grey stats line: `q<±charge>  φ<n> · pol<n> · chg<n>` — the loop's net charge at pH 7.4, and the number of hydrophobic (φ), polar-uncharged (pol) and charged (chg) side chains.
3. Recolors the AA-sequence cell so each CDR is shown in its own font color (CDR1 red, CDR2 green, CDR3 blue; frameworks stay default).
4. Writes whole-sequence bulk properties to their own columns, creating any that don't exist yet at the end of the header row:
   - `pI` — isoelectric point
   - `MW (kDa)` — molecular weight
   - `Ext coeff (M-1 cm-1)` — molar extinction coefficient at 280 nm, given for both the oxidized (`ox:`, disulfides formed) and reduced (`red:`) state
   - `A280 (1 mg/mL)` — absorbance of a 1 mg/mL (0.1%) solution, again `ox:` / `red:`

### Residue classification (per-CDR counts)

- Hydrophobic (φ): A, V, L, I, M, F, W, Y, C
- Polar, uncharged (pol): S, T, N, Q, H, G
- Charged (chg): D, E, K, R

His is counted as polar but still contributes (partially) to the net charge. Net charge uses Henderson–Hasselbalch on the side chains only (a CDR is an internal fragment, so its ends are not treated as real termini).

## Method

### CDR boundaries — conserved-residue anchoring

No alignment or external numbering tool needed:

- CDR1 = between the 1st conserved Cys (Cys23) and the FR2 Trp (Trp41)
- CDR3 = between the 2nd conserved Cys (Cys104) and the WGxG / FR4 motif
- CDR2 = fixed offset after Trp41, ending at the conserved FR3 motif

CDR1 and CDR3 are anchored on both sides by conserved residues, so they're exact regardless of loop length. CDR2's downstream boundary is heuristic — spot-check a few rows if your CDR2 loops look unusual.

### Properties — ProtParam-equivalent

The property math mirrors ExPASy ProtParam and was verified numerically against BioPython (`Bio.SeqUtils` `IsoelectricPoint` and `molecular_weight`):

- **MW** = sum of average residue masses + one water.
- **pI** = Bjellqvist pKa set, terminus-aware, solved by bisection.
- **Extinction** = Tyr·1490 + Trp·5500 (reduced); + (Cys÷2)·125 for cystines (oxidized).
- **A280 (0.1%)** = extinction ÷ MW.

Non-standard residues (X, B, Z, etc.) are dropped before the numeric calculations, matching propro's core `properties` module.

## Install / run

1. Open the target Google Sheet.
2. Extensions > Apps Script.
3. Paste in `cdr_annotation.gs`, save.
4. Select `annotateNanobodyCDRs` in the function dropdown, click Run.
5. First run asks for authorization — approve it.

## Why this lives here, not under `propro/interfaces/`

This script is nanobody biology (IMGT anchor logic) wrapped in a Google Sheets front-end. propro organizes motif-specific interface code (whatever platform it targets) inside the motif's own directory, so all nanobody-related code — Python or otherwise — stays in one place as `propro.motifs.nanobodies` grows. `propro/interfaces/gscripts/` is reserved for Sheets glue that isn't tied to one motif; see `propro/interfaces/gscripts/REGISTRY.md` for a full index of every gscript in the repo regardless of where it physically lives.
