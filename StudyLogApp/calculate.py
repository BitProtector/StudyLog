from typing import Optional, Tuple

def compute_final_grade(
    k1: Optional[float],
    k2: Optional[float],
    k1_weight: Optional[float],
    k2_weight: Optional[float],
    msp: Optional[float],
    msp_weight: Optional[float],
    calc_type: Optional[int]
) -> Tuple[Optional[float], Optional[float]]:
    """
    Berechnet EN (Eingangsnote) und Gesamtnote (final_average) anhand 
    der uebergebenen Werte.

    Rueckgabe:
        en, final_average
    """
    en = None
    final_average = None
    
    if calc_type is None:
        calc_type = 0

    if calc_type == 0:
        # Typ 0: EN = (k1 + k2) / 2, Gesamtnote = (EN + MSP) / 2
        if k1 is not None and k2 is not None:
            en = (k1 + k2) / 2
        elif k1 is not None:
            en = k1
        elif k2 is not None:
            en = k2

        if en is not None and msp is not None:
            final_average = (en + msp) / 2
        else:
            final_average = en if en is not None else msp

    elif calc_type == 1:
        # Typ 1: EN = 1/3 * k1 + 2/3 * k2, Gesamtnote = (EN + MSP) / 2
        if k1 is not None and k2 is not None:
            en = (k1 / 3) + (2 * k2 / 3)
        elif k1 is not None:
            en = k1
        elif k2 is not None:
            en = k2

        if en is not None and msp is not None:
            final_average = (en + msp) / 2
        else:
            final_average = en if en is not None else msp

    elif calc_type == 2:
        # Typ 2: EN = (k1 + k2) / 2. 
        # Wenn EN > MSP => Gesamtnote = (EN + MSP) / 2, sonst MSP
        if k1 is not None and k2 is not None:
            en = (k1 + k2) / 2
        elif k1 is not None:
            en = k1
        elif k2 is not None:
            en = k2

        if en is not None and msp is not None:
            if en > msp:
                final_average = (en + msp) / 2
            else:
                final_average = msp
        else:
            final_average = en if en is not None else msp

    elif calc_type == 3:
        # Typ 3: Gewichtsbasierte Berechnung 
        # EN = (k1 * k1_weight + k2 * k2_weight) / (k1_weight + k2_weight), 
        # final = EN * (1 - msp_weight) + MSP * msp_weight
        numerator = 0.0
        total_weight = 0.0
        if k1 is not None and k1_weight is not None:
            numerator += k1 * k1_weight
            total_weight += k1_weight
        if k2 is not None and k2_weight is not None:
            numerator += k2 * k2_weight
            total_weight += k2_weight

        if total_weight > 0:
            en = numerator / total_weight

        if en is not None and msp is not None and msp_weight is not None:
            final_average = en * (1 - msp_weight) + msp * msp_weight
        else:
            final_average = en if en is not None else msp

    return en, final_average
