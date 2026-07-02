"""Class-specific protein tooling, built on top of ``propro.core``.

Each submodule targets a specific class of protein with its own relevant
properties and visualizations beyond the general-purpose ones in
``propro.core``. A motif submodule can include interface-facing code (e.g.
a Google Sheets script) alongside its Python code — see
``propro.motifs.nanobodies`` for the pattern, and
``propro/interfaces/gscripts/REGISTRY.md`` for an index of every such
script regardless of which motif it lives under.

- ``propro.motifs.nanobodies``  — VHH-specific tooling. Implemented:
  IMGT CDR1/2/3 annotation as a Google Sheets script
  (``gscripts/cdr_annotation.gs``). Planned: the same CDR/framework logic
  as a Python function on ``ProteinSequence``, VHH hallmark-residue checks.
- ``propro.motifs.antibodies``  — *(not yet implemented)* Fab/IgG-specific
  properties (CDR identification, Kabat/IMGT numbering, heavy/light chain
  pairing, ...).
- ``propro.motifs.enzymes``     — *(not yet implemented)* active-site/
  catalytic-residue aware properties.
- ``propro.motifs.complexes``   — *(not yet implemented)* multimeric
  assembly properties (chain interfaces, stoichiometry, ...).
"""
