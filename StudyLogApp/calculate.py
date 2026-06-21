"""Zentrale Regeln fuer die Notenberechnung."""

from math import isfinite
from typing import Optional, Tuple


PASSING_GRADE = 3.75
MIN_GRADE = 1.0
MAX_GRADE = 6.0
VALID_CALC_TYPES = {0, 1, 2, 3}


def _is_finite_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(value)


def _is_valid_grade(value: Optional[float]) -> bool:
    return value is None or (
        _is_finite_number(value) and MIN_GRADE <= value <= MAX_GRADE
    )


def normalise_msp_weight(weight: Optional[float]) -> Optional[float]:
    """Konvertiert 50 (%) zu 0.5 und lehnt ungueltige Gewichte ab."""
    if weight is None:
        return None
    if not _is_finite_number(weight) or weight < 0:
        return None
    if weight <= 1:
        return float(weight)
    if weight <= 100:
        return float(weight) / 100
    return None


def validate_grade_input(
    k1: Optional[float],
    k2: Optional[float],
    k1_weight: Optional[float],
    k2_weight: Optional[float],
    msp: Optional[float],
    msp_weight: Optional[float],
    calc_type: Optional[int],
) -> Optional[str]:
    """Liefert eine Fehlermeldung oder ``None`` fuer gueltige Eingaben."""
    if calc_type not in VALID_CALC_TYPES:
        return "Bitte einen gueltigen Berechnungstyp waehlen."

    if all(value is None for value in (k1, k2, msp)):
        return "Mindestens eine Note muss eingegeben werden."

    if not all(_is_valid_grade(value) for value in (k1, k2, msp)):
        return f"Noten muessen endliche Werte zwischen {MIN_GRADE:g} und {MAX_GRADE:g} sein."

    if calc_type != 3:
        return None

    for grade, weight, label in ((k1, k1_weight, "K1"), (k2, k2_weight, "K2")):
        if grade is None and weight is not None:
            return f"{label}-Gewicht ist ohne {label}-Note nicht zulaessig."
        if grade is not None:
            if not _is_finite_number(weight) or weight <= 0:
                return f"Fuer {label} ist ein positives Gewicht erforderlich."

    if msp is None and msp_weight is not None:
        return "MSP-Gewicht ist ohne MSP-Note nicht zulaessig."
    if msp is not None and msp_weight is not None:
        if normalise_msp_weight(msp_weight) is None:
            return "MSP-Gewicht muss zwischen 0 und 1 oder zwischen 0 und 100 % liegen."
    if msp is not None and (k1 is not None or k2 is not None) and msp_weight is None:
        return "Fuer die Kombination von EN und MSP ist ein MSP-Gewicht erforderlich."

    return None


def _entry_grade(k1: Optional[float], k2: Optional[float], calc_type: int) -> Optional[float]:
    """Berechnet die Eingangsnote aus den vorhandenen Klausurnoten."""
    if k1 is not None and k2 is not None:
        if calc_type == 1:
            return (k1 / 3) + (2 * k2 / 3)
        return (k1 + k2) / 2
    return k1 if k1 is not None else k2


def compute_final_grade(
    k1: Optional[float],
    k2: Optional[float],
    k1_weight: Optional[float],
    k2_weight: Optional[float],
    msp: Optional[float],
    msp_weight: Optional[float],
    calc_type: Optional[int],
    requires_msp: bool = False,
) -> Tuple[Optional[float], Optional[float]]:
    """Berechnet EN und eine endgueltige Gesamtnote.

    Eine fehlende, fuer das Modul erforderliche MSP ergibt absichtlich keine
    Gesamtnote. Damit werden aus Zwischennoten keine bestandenen Module oder
    ECTS-Punkte abgeleitet.
    """
    # Bestehende Datensaetze vor der Auswahl des Berechnungstyps verwenden
    # denselben bisherigen Standard wie die Eingabemaske.
    if calc_type is None:
        calc_type = 0
    if calc_type not in VALID_CALC_TYPES:
        return None, None
    if not all(_is_valid_grade(value) for value in (k1, k2, msp)):
        return None, None

    if calc_type == 3:
        for grade, weight in ((k1, k1_weight), (k2, k2_weight)):
            if grade is None and weight is not None:
                return None, None
            if grade is not None and (not _is_finite_number(weight) or weight <= 0):
                return None, None
        if msp is not None and msp_weight is not None and normalise_msp_weight(msp_weight) is None:
            return None, None

        numerator = 0.0
        total_weight = 0.0
        for grade, weight in ((k1, k1_weight), (k2, k2_weight)):
            if grade is not None:
                numerator += grade * float(weight)
                total_weight += float(weight)
        en = numerator / total_weight if total_weight > 0 else None

        if msp is None:
            return en, None if requires_msp else en
        if en is None:
            return None, msp

        weight = normalise_msp_weight(msp_weight)
        if weight is None:
            return en, None
        return en, en * (1 - weight) + msp * weight

    en = _entry_grade(k1, k2, calc_type)
    if msp is None:
        return en, None if requires_msp else en
    if en is None:
        return None, msp

    if calc_type == 2:
        return en, (en + msp) / 2 if en > msp else msp
    return en, (en + msp) / 2


def required_msp_for_passing(
    en: Optional[float],
    msp_weight: Optional[float],
    calc_type: Optional[int],
) -> Optional[float]:
    """Berechnet die MSP, die fuer ``PASSING_GRADE`` mindestens noetig ist."""
    if calc_type is None:
        calc_type = 0
    if en is None or calc_type not in VALID_CALC_TYPES:
        return None
    if calc_type in (0, 1):
        return 2 * PASSING_GRADE - en
    if calc_type == 2:
        return PASSING_GRADE if en < PASSING_GRADE else 2 * PASSING_GRADE - en

    weight = normalise_msp_weight(msp_weight)
    if weight is None or weight == 0:
        return None
    return (PASSING_GRADE - (1 - weight) * en) / weight
