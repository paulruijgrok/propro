"""PDF report interface — turn propro calculations into standalone PDF documents.

A PDF is treated as an output platform here, parallel to
``propro.interfaces.gscripts`` (Google Sheets) and ``propro.interfaces.pymol``.
These reports apply to any protein sequence and build only on ``propro.core``,
so they live in ``interfaces`` rather than under a specific ``motifs`` class.

Tools
-----
- ``sequence_overview_pdf`` — one-page overview of a single sequence
  (key properties, net-charge-vs-pH chart, amino acid frequency table).
  Importable, or runnable as
  ``python -m propro.interfaces.pdf_reports.sequence_overview_pdf``.

See ``README.md`` in this directory for the full index.
"""
