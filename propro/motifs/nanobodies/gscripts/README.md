# Nanobody CDR annotation (Google Sheets)

`cdr_annotation.gs` annotates IMGT CDR1/CDR2/CDR3 loops for VHH (nanobody) sequences directly inside a Google Sheet — no external tools, no Python required.

## What it does

On a sheet tab named `nanobodies`:

1. Reads each sequence from the `AA Sequences` column (tolerant to a few common header spellings, e.g. `Sequence`, `AA Seq`).
2. Extracts CDR1 / CDR2 / CDR3 and writes them into the `CDR1`, `CDR2`, `CDR3` columns.
3. Recolors the AA-sequence cell so each CDR is shown in its own font color (CDR1 red, CDR2 green, CDR3 blue; frameworks stay default).

## Method

Conserved-residue anchoring — no alignment or external numbering tool needed:

- CDR1 = between the 1st conserved Cys (Cys23) and the FR2 Trp (Trp41)
- CDR3 = between the 2nd conserved Cys (Cys104) and the WGxG / FR4 motif
- CDR2 = fixed offset after Trp41, ending at the conserved FR3 motif

CDR1 and CDR3 are anchored on both sides by conserved residues, so they're exact regardless of loop length. CDR2's downstream boundary is heuristic — spot-check a few rows if your CDR2 loops look unusual.

## Install / run

1. Open the target Google Sheet.
2. Extensions > Apps Script.
3. Paste in `cdr_annotation.gs`, save.
4. Select `annotateNanobodyCDRs` in the function dropdown, click Run.
5. First run asks for authorization — approve it.

## Why this lives here, not under `propro/interfaces/`

This script is nanobody biology (IMGT anchor logic) wrapped in a Google Sheets front-end. propro organizes motif-specific interface code (whatever platform it targets) inside the motif's own directory, so all nanobody-related code — Python or otherwise — stays in one place as `propro.motifs.nanobodies` grows. `propro/interfaces/gscripts/` is reserved for Sheets glue that isn't tied to one motif; see `propro/interfaces/gscripts/REGISTRY.md` for a full index of every gscript in the repo regardless of where it physically lives.
