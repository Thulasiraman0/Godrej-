"""Physics-grounded risk: impact energy × fragility × history."""

from __future__ import annotations

from .taxonomy import FRAGILITY, P_DAMAGE, REPLACEMENT_INR


def impact_energy_joules(height_m: float, mass_kg: float = 18.0) -> float:
    """½mv² with v² = 2gh for a free fall, plus a floor of 2 J."""
    g = 9.81
    v2 = 2 * g * max(height_m, 0.0)
    return max(0.5 * mass_kg * v2, 2.0)


def risk_score(
    behaviour: str,
    product_class: str,
    height_m: float = 0.4,
    repetition: int = 1,
    location_hot: bool = False,
) -> dict:
    energy = impact_energy_joules(height_m)
    fragility = FRAGILITY.get(product_class, 0.6)
    freq = 1.0 + 0.15 * max(repetition - 1, 0)
    loc = 1.2 if location_hot else 1.0
    raw = energy * fragility * freq * loc
    if raw < 12:
        band = "Low"
    elif raw < 28:
        band = "Medium"
    elif raw < 55:
        band = "High"
    else:
        band = "Critical"
    p = P_DAMAGE.get(behaviour, 0.2) * min(raw / 40.0, 1.4)
    p = min(max(p, 0.05), 0.85)
    value = REPLACEMENT_INR.get(product_class, 8000)
    exposure = round(p * value)
    return {
        "impact_j": round(energy, 1),
        "fragility": fragility,
        "raw": round(raw, 1),
        "band": band,
        "p_damage": round(p, 3),
        "exposure_inr": exposure,
        "height_m": round(height_m, 2),
    }


def honesty_state(behaviour: str, deformation: bool, spill: bool, motionless: bool) -> str:
    """Observed → Potential risk → Confirmed damage. Never skip a state."""
    if deformation or spill:
        return "confirmed_damage"
    if behaviour in {"drop_throw", "standing_on_cartons", "unstable_stack"} and motionless:
        return "potential_risk"
    return "observed_behaviour"
