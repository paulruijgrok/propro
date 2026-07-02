"""Google Sheets interface — generic, cross-motif glue only.

Motif-specific Sheets tooling (e.g. nanobody CDR annotation) lives inside
its motif's own directory (e.g. ``propro.motifs.nanobodies.gscripts``), not
here — see the "Why this lives here" note in that motif's gscripts README.
This package is reserved for Sheets glue that isn't tied to one protein
class, e.g. a future "write a ProteinOverview (or batch of them) out to a
Sheet" helper, or "read a sheet of sequences in as input."

For a full index of every gscript in the repo, regardless of where it
physically lives, see ``REGISTRY.md`` in this directory.
"""
