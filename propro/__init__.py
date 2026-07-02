"""
propro — a toolkit for quickly calculating and visualizing biochemical and
biophysical properties of proteins.

The package is organized as:

- ``propro.core``       — sequence/structure containers and the general-purpose
                           property calculators and visualizers that apply to
                           any protein.
- ``propro.motifs``     — extensions focused on specific protein classes
                           (antibodies, nanobodies, enzymes, multimeric
                           complexes) with their own property/visualization
                           needs.
- ``propro.interfaces`` — glue code to external platforms (Google Sheets,
                           PyMOL, ...).

Scope note: propro favors properties that are cheap and fast to compute from
a sequence and/or structure. It intentionally does not host long-running or
computationally heavy analyses.
"""

from propro.core.sequence import ProteinSequence
from propro.core.properties import ProteinOverview, compute_overview
from propro.core.report import print_report, overview_to_dataframe, overview_to_markdown

__all__ = [
    "ProteinSequence",
    "ProteinOverview",
    "compute_overview",
    "print_report",
    "overview_to_dataframe",
    "overview_to_markdown",
]

__version__ = "0.1.0"
