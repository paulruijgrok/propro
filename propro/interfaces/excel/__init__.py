"""Microsoft Excel interface — generic, cross-motif glue only.

Motif-specific Excel tooling (e.g. nanobody CDR annotation) lives inside
its motif's own directory (e.g. ``propro.motifs.nanobodies.excel``), not
here — mirroring the layout of ``propro.interfaces.gscripts``. This package
is reserved for Excel glue that isn't tied to one protein class, e.g. a
future "write a ProteinOverview (or batch of them) out to a workbook" helper,
or "read a sheet of sequences in as input."

For a full index of every Excel macro in the repo, regardless of where it
physically lives, see ``REGISTRY.md`` in this directory.
"""
