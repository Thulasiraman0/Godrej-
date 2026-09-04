from __future__ import annotations

from core.schemas import EvidenceState, RiskLevel

from .tables import FRAGILITY, MASS_KG, P_DAMAGE, REPLACEMENT_INR, SEVERITY


def impact_energy_j(height_m: float, mass_kg: float) -> float:
    g = 9.81
    v2 = 2 * g * max(height_m, 0.0)
    return max(0.5 * mass_kg * v2, 2.0)


def score_event(
    behaviour: str,
    product_class: str,
    height_m: float = 0.4,
    repetition: int = 1,
    location_hot: bool = False,
    post_impact_still: bool = False,
    deformation: bool = False,
) -> dict:
    mass = MASS_KG.get(product_class, 18.0)
    energy = impact_energy_j(height_m, mass)
    base = SEVERITY.get(behaviour, 0.4)
    frag = FRAGILITY.get(product_class, 0.6)
    freq = 1.0 + 0.12 * max(repetition - 1, 0)
    loc = 1.2 if location_hot else 1.0
    impact_mult = 1.0 + min(energy / 80.0, 1.5)
    raw = 100.0 * base * frag * freq * loc * min(impact_mult / 2.0, 1.4)
    raw = max(5.0, min(raw, 99.0))
    if raw < 25:
        level = RiskLevel.LOW
    elif raw < 45:
        level = RiskLevel.MEDIUM
    elif raw < 70:
        level = RiskLevel.HIGH
    else:
        level = RiskLevel.CRITICAL

    if deformation:
        state = EvidenceState.CONFIRMED_DAMAGE
    elif behaviour in {"DROP", "STANDING_ON_CARTON", "UNSTABLE_STACK"} and post_impact_still:
        state = EvidenceState.POTENTIAL_RISK
    else:
        state = EvidenceState.OBSERVED

    p = min(max(P_DAMAGE.get(behaviour, 0.2) * (raw / 55.0), 0.05), 0.85)
    value = REPLACEMENT_INR.get(product_class, 8000)
    return {
        "risk_score": round(raw, 1),
        "risk_level": level,
        "state": state,
        "impact_j": round(energy, 1),
        "height_m": round(height_m, 2),
        "p_damage": round(p, 3),
        "exposure_inr": int(round(p * value)),
        "mass_kg": mass,
    }
