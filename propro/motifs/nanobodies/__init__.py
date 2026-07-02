"""Nanobody (VHH) motif.

Scope: single-domain antibody (VHH) specific properties and tooling, on top
of the general-purpose calculators in ``propro.core``.

Currently implemented:

- ``gscripts/cdr_annotation.gs`` — Google Apps Script that annotates IMGT
  CDR1/CDR2/CDR3 loops directly in a Google Sheet (conserved-residue
  anchoring, no external tools required). See ``gscripts/README.md`` for
  sheet layout and install instructions. It's a standalone Apps Script file
  rather than a Python module — see the note in that README on why
  interface-facing code for a motif lives inside the motif's own directory
  rather than under ``propro.interfaces``.

Planned (not yet implemented):

- Python CDR/framework extraction (``findCDRs``-equivalent) usable from
  ``propro.core.sequence.ProteinSequence``, so CDR boundaries are available
  outside of Google Sheets (e.g. for reports or PyMOL coloring).
- Heavy/light-chain-free VHH-specific property adjustments (e.g. hallmark
  framework-2 residue checks).
"""
