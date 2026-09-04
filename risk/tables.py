MASS_KG = {
    "carton": 12.0,
    "mattress": 25.0,
    "kd_pack": 30.0,
    "kd_flatpack": 30.0,
    "appliance": 60.0,
    "refrigerator": 70.0,
    "glass_top": 28.0,
    "pallet": 25.0,
}

FRAGILITY = {
    "carton": 0.55,
    "mattress": 0.35,
    "kd_pack": 0.75,
    "kd_flatpack": 0.75,
    "appliance": 0.9,
    "refrigerator": 1.0,
    "glass_top": 1.0,
}

REPLACEMENT_INR = {
    "carton": 4200,
    "mattress": 18000,
    "kd_pack": 12500,
    "kd_flatpack": 12500,
    "appliance": 28000,
    "refrigerator": 42000,
    "glass_top": 35000,
}

SEVERITY = {
    "DROP": 0.85,
    "DRAG": 0.45,
    "ROLL": 0.50,
    "IMPROPER_STACK": 0.60,
    "OVERHANG": 0.48,
    "UNSTABLE_STACK": 0.70,
    "STANDING_ON_CARTON": 0.88,
    "WRONG_ORIENTATION": 0.40,
    "NO_EQUIPMENT": 0.55,
    "STRAP_LIFT": 0.62,
}

HEAVY_SET = {"appliance", "refrigerator", "kd_pack", "kd_flatpack", "mattress"}
UPRIGHT_SET = {"refrigerator", "appliance"}
PRODUCTS = {
    "carton",
    "mattress",
    "kd_pack",
    "kd_flatpack",
    "appliance",
    "refrigerator",
    "glass_top",
}
EQUIPMENT = {"trolley", "pallet_truck", "forklift"}

PRACTICE = {
    "DROP": "Lower the load onto the pallet; keep contact until it is seated.",
    "DRAG": "Lift fully or use a pallet truck / trolley. Never drag finished goods.",
    "ROLL": "Carry or trolley; never roll cartons or mattresses on the dock.",
    "IMPROPER_STACK": "Heavy / large at the bottom, light / small on top.",
    "OVERHANG": "Match pallet size to SKU; keep the load inside the pallet footprint.",
    "UNSTABLE_STACK": "Keep stack axis vertical; no overhang beyond 15% of pallet area.",
    "STANDING_ON_CARTON": "Use a step stool or dock plate — never stand on product.",
    "WRONG_ORIENTATION": "Keep 'this way up' marks vertical for the full dwell.",
    "NO_EQUIPMENT": "Use trolley / pallet truck for heavy or bulky SKUs.",
    "STRAP_LIFT": "Lift from the base or handles, never straps or tape.",
}

P_DAMAGE = {
    "DROP": 0.42,
    "DRAG": 0.18,
    "ROLL": 0.22,
    "IMPROPER_STACK": 0.28,
    "OVERHANG": 0.20,
    "UNSTABLE_STACK": 0.35,
    "STANDING_ON_CARTON": 0.48,
    "WRONG_ORIENTATION": 0.16,
    "NO_EQUIPMENT": 0.25,
    "STRAP_LIFT": 0.31,
}
