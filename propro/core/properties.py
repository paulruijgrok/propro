"""Quick-overview biochemical/biophysical property calculator.

This is the entry point for propro's "give me a fast rundown of this
protein" functionality. Everything here is intentionally cheap to compute
from sequence alone (BioPython's ``Bio.SeqUtils.ProtParam.ProteinAnalysis``
does the underlying math, mirroring the classic ExPASy ProtParam tool) —
consistent with propro's scope of quick, general-purpose properties rather
than deep or slow analyses.

Ambiguous / non-standard residues (X, B, Z, J, U, O) are excluded from the
numeric calculations (MW, pI, instability index, extinction coefficient, net
charge) since those are only defined for the standard 20 amino acids; how
many were excluded is recorded on the returned ``ProteinOverview`` so callers
know if a result is approximate.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from propro.core.sequence import STANDARD_AA, ProteinSequence

INSTABILITY_THRESHOLD = 40.0  # Guruprasad et al. 1990: II > 40 => predicted unstable


def _get_protein_analysis(sequence: str):
    try:
        from Bio.SeqUtils.ProtParam import ProteinAnalysis
    except ImportError as exc:  # pragma: no cover - exercised only without BioPython
        raise ImportError(
            "propro.core.properties requires BioPython. Install it with "
            "'pip install biopython'."
        ) from exc
    return ProteinAnalysis(sequence)


@dataclass
class ProteinOverview:
    """Result container for :func:`compute_overview`. All numeric properties
    are ``None`` when they could not be computed (e.g. sequence is entirely
    ambiguous residues)."""

    id: str
    description: str

    # --- Position / summary -------------------------------------------------
    length: int
    n_ambiguous_residues: int
    position_start: int
    position_end: int
    is_contiguous: bool
    n_flank: int
    first_residues: List[Tuple[int, str]]
    last_residues: List[Tuple[int, str]]

    # --- Bulk properties ------------------------------------------------------
    molecular_weight: Optional[float]  # Da
    isoelectric_point: Optional[float]
    instability_index: Optional[float]
    instability_class: Optional[str]

    # --- Extinction coefficient (280 nm) --------------------------------------
    extinction_coefficient_reduced: Optional[float]  # M-1 cm-1, all Cys reduced
    extinction_coefficient_oxidized: Optional[float]  # M-1 cm-1, all Cys as cystines
    absorbance_1mgml_reduced: Optional[float]  # A(280nm, 1 mg/mL, 1 cm path)
    absorbance_1mgml_oxidized: Optional[float]

    # --- Composition ------------------------------------------------------
    aa_counts: Dict[str, int]
    aa_percent: Dict[str, float]  # percentage, 0-100, of full length

    # --- Charge ------------------------------------------------------------
    net_charge_by_ph: List[Tuple[float, float]]
    net_charge_ph7: Optional[float]

    notes: List[str] = field(default_factory=list)

    @property
    def sequence_summary(self) -> str:
        first = "".join(aa for _, aa in self.first_residues)
        last = "".join(aa for _, aa in self.last_residues)
        if self.length <= 2 * self.n_flank:
            return f"{self.length} residues total"
        return f"{first}...{last} ({self.length} residues total)"


def compute_overview(
    protein: ProteinSequence,
    n_flank: int = 10,
    ph_min: float = 0.0,
    ph_max: float = 14.0,
    ph_step: float = 0.5,
) -> ProteinOverview:
    """Compute a quick biochemical/biophysical overview of a protein sequence.

    Parameters
    ----------
    protein:
        The sequence to analyze.
    n_flank:
        How many residues to show at the start and end of the sequence in the
        summary (``first_residues`` / ``last_residues``).
    ph_min, ph_max, ph_step:
        Range and resolution of the net-charge-vs-pH curve.

    Returns
    -------
    ProteinOverview
    """
    notes: List[str] = []
    full_seq = protein.sequence
    clean_seq = "".join(c for c in full_seq if c in STANDARD_AA)
    n_ambiguous = len(full_seq) - len(clean_seq)
    if n_ambiguous:
        notes.append(
            f"{n_ambiguous} ambiguous/non-standard residue(s) excluded from "
            "MW, pI, instability index, extinction coefficient, and charge "
            "calculations."
        )

    n_flank = max(0, min(n_flank, len(protein)))
    first_residues = list(zip(protein.positions[:n_flank], full_seq[:n_flank]))
    last_residues = list(zip(protein.positions[-n_flank:], full_seq[-n_flank:])) if n_flank else []

    aa_counts = dict(Counter(full_seq))
    aa_percent = {aa: 100.0 * n / len(full_seq) for aa, n in aa_counts.items()}

    mw = pi = instability = ext_red = ext_ox = abs_red = abs_ox = None
    instability_class = None
    charge_curve: List[Tuple[float, float]] = []
    charge_ph7 = None

    if clean_seq:
        pa = _get_protein_analysis(clean_seq)
        mw = pa.molecular_weight()
        pi = pa.isoelectric_point()
        instability = pa.instability_index()
        instability_class = "stable" if instability <= INSTABILITY_THRESHOLD else "unstable"
        ext_red, ext_ox = pa.molar_extinction_coefficient()
        abs_red = ext_red / mw
        abs_ox = ext_ox / mw

        n_steps = int(round((ph_max - ph_min) / ph_step))
        for i in range(n_steps + 1):
            ph = round(ph_min + i * ph_step, 6)
            charge_curve.append((ph, pa.charge_at_pH(ph)))
        charge_ph7 = pa.charge_at_pH(7.0)
    else:
        notes.append("No standard-residue content; numeric properties could not be computed.")

    return ProteinOverview(
        id=protein.id,
        description=protein.description,
        length=len(protein),
        n_ambiguous_residues=n_ambiguous,
        position_start=protein.position_range[0],
        position_end=protein.position_range[1],
        is_contiguous=protein.is_contiguous,
        n_flank=n_flank,
        first_residues=first_residues,
        last_residues=last_residues,
        molecular_weight=mw,
        isoelectric_point=pi,
        instability_index=instability,
        instability_class=instability_class,
        extinction_coefficient_reduced=ext_red,
        extinction_coefficient_oxidized=ext_ox,
        absorbance_1mgml_reduced=abs_red,
        absorbance_1mgml_oxidized=abs_ox,
        aa_counts=aa_counts,
        aa_percent=aa_percent,
        net_charge_by_ph=charge_curve,
        net_charge_ph7=charge_ph7,
        notes=notes,
    )
