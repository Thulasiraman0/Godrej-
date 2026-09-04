"""The 10 handling behaviours Sahaayak is graded on."""

from __future__ import annotations

BEHAVIOURS = [
    {
        "id": "drop_throw",
        "name": "Drop / throw",
        "good": "Lower the load onto the pallet; keep contact until it is seated.",
        "detection": "Free-fall vertical acceleration + sudden stop + no hand contact at impact.",
    },
    {
        "id": "dragging",
        "name": "Dragging on floor",
        "good": "Lift fully or use a pallet truck / trolley.",
        "detection": "Bottom edge stays on floor plane while centroid translates; no lift phase.",
    },
    {
        "id": "rolling",
        "name": "Rolling a carton / mattress",
        "good": "Carry or trolley; never roll finished goods on the dock.",
        "detection": "Oriented bbox rotation about floor contact + translation.",
    },
    {
        "id": "improper_stack",
        "name": "Improper stack (small under large)",
        "good": "Heavy / large at bottom, light / small on top.",
        "detection": "Bbox area/width comparison of vertically adjacent items.",
    },
    {
        "id": "unstable_stack",
        "name": "Unstable stack / overhang",
        "good": "Load footprint inside pallet; stack axis vertical.",
        "detection": "Load vs pallet IoU; tilt of stack axis.",
    },
    {
        "id": "oversize_pallet",
        "name": "Product larger than pallet",
        "good": "Match pallet size to SKU; no overhang.",
        "detection": "Single-frame geometry: product footprint vs pallet.",
    },
    {
        "id": "standing_on_cartons",
        "name": "Stepping / standing on cartons",
        "good": "Use a step stool or dock plate — never the product.",
        "detection": "Ankle keypoints inside a product bbox top surface.",
    },
    {
        "id": "wrong_orientation",
        "name": "Wrong orientation (vertical kept flat)",
        "good": "Keep 'this way up' marks vertical.",
        "detection": "Aspect ratio vs class orientation prior.",
    },
    {
        "id": "manual_vs_equipment",
        "name": "Manual handling where equipment required",
        "good": "Use trolley / pallet truck for heavy or bulky SKUs.",
        "detection": "Heavy class moving with person contact and no equipment in frame.",
    },
    {
        "id": "strap_lift",
        "name": "Lifting by packaging straps",
        "good": "Lift from base / handles, never straps or tape.",
        "detection": "Hand keypoint at strap region + product lifted.",
    },
]

FRAGILITY = {
    "mattress": 0.35,
    "carton": 0.55,
    "kd_flatpack": 0.75,
    "appliance": 0.9,
    "refrigerator": 1.0,
    "glass_top": 1.0,
}

REPLACEMENT_INR = {
    "mattress": 18000,
    "carton": 4200,
    "kd_flatpack": 12500,
    "appliance": 28000,
    "refrigerator": 42000,
    "glass_top": 35000,
}

P_DAMAGE = {
    "drop_throw": 0.42,
    "dragging": 0.18,
    "rolling": 0.22,
    "improper_stack": 0.28,
    "unstable_stack": 0.35,
    "oversize_pallet": 0.2,
    "standing_on_cartons": 0.48,
    "wrong_orientation": 0.16,
    "manual_vs_equipment": 0.25,
    "strap_lift": 0.31,
}
