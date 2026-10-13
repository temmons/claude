"""Which zoning districts allow apartments, by town.

Categories
  MF_APT     multi-family residential district that permits apartment/condo buildings
  MF_ATT     residential district whose multi-unit housing is townhouse/attached/
             "general residence" (3+ unit attached buildings allowed, apartments limited)
  MIXED_USE  commercial / downtown / mixed-use district that allows dwelling units
             (usually above the ground floor; some by special use)
Anything not listed is treated as not allowing apartments (single-family,
two-family-only, office, industrial, institutional, and planned-development
districts whose allowed uses depend on an individual ordinance).

`basis` notes where the call comes from: "code" = read in the municipal zoning
code text; "layer" = the district name/description published in the town's own
GIS layer; "inferred" = district naming convention, not confirmed in code text.
"""

CLASSES = {
    "Uninc": {
        "R-5": ("MF_ATT", "layer", "County GIS metadata lists R-5 as a multiple-family district (general residence)"),
        "R-6": ("MF_APT", "layer", "County GIS metadata: multiple-family district"),
        "R-7": ("MF_APT", "layer", "County GIS metadata: multiple-family district"),
    },
    "Aurora": {
        "R5": ("MF_APT", "code", "R-5 Multiple-family dwelling district"),
        "R5A": ("MF_APT", "code", "R-5A Midrise multiple-family district"),
    },
    "Bartlett": {
        "SR-5": ("MF_ATT", "layer", "Suburban Residence (Low Density Multi-Family)"),
        "SR-6": ("MF_APT", "layer", "Suburban Residence (Medium Density Multi-Family)"),
        "B-1": ("MIXED_USE", "inferred", "Village Center district (downtown)"),
    },
    "Bensenville": {
        "R-5": ("MF_APT", "code", "Multiple-Unit Dwelling District; multiple-unit dwelling permitted"),
        "R-6": ("MF_APT", "code", "Multiple-Unit Dwelling District; multiple-unit dwelling permitted"),
        "C-1": ("MIXED_USE", "code", "Downtown Mixed-Use; multiple-unit dwelling by special use"),
        "C-2": ("MIXED_USE", "code", "Commercial; multiple-unit dwelling by special use"),
    },
    "Bloomingdale": {
        "R-3": ("MF_ATT", "code", "General Residence District"),
        "R-4": ("MF_APT", "code", "Multiple-Family Dwelling Residence District"),
        "R-5": ("MF_APT", "code", "Multiple-Family Dwelling High Rise District"),
        "OT": ("MIXED_USE", "inferred", "Old Town district (downtown mixed use per Old Town plan)"),
    },
    "Burr Ridge": {
        "R-5": ("MF_ATT", "code", "R-5 Planned Residence District"),
        "R-6": ("MF_APT", "code", "R-6 Residential and Congregate Care District"),
    },
    "Carol Stream": {
        "R-4": ("MF_APT", "code", "Multiunit Residence District: condominiums, apartments, senior housing"),
        "B-1": ("MIXED_USE", "code", "Town Center district: retail, office, residential"),
    },
    "Clarendon Hills": {
        "MULTI-FAMILYRESIDENTIAL": ("MF_APT", "code", "R-3 Multiple-Family Residential District (layer shows generalized class names)"),
        "GENERALBUSINESSDISTRICT": ("MIXED_USE", "code", "Downtown B-2: residential appropriate for upper-story space"),
        "GERNRALBUSINESSDISTRICT": ("MIXED_USE", "code", "Downtown B-2 (misspelled in layer)"),
        "GENERALSALE": ("MIXED_USE", "inferred", "Layer class 'General Sale' read as downtown B-1 Retail Business (upper-story residential)"),
    },
    "Darien": {
        "R-3": ("MF_ATT", "code", "Multi-Family Residence District: attached, two-family and limited apartments"),
    },
    "Downers Grove": {
        "R5": ("MF_ATT", "code", "Attached houses allowed (R-5)"),
        "R5A": ("MF_ATT", "code", "Attached houses allowed (R-5A)"),
        "R6": ("MF_APT", "inferred", "Multi-unit residential district"),
        "DB": ("MIXED_USE", "inferred", "Downtown Business"),
        "DC": ("MIXED_USE", "inferred", "Downtown Core"),
        "DT": ("MIXED_USE", "inferred", "Downtown Transition"),
        "FB": ("MIXED_USE", "inferred", "Fairview Business"),
        "FC": ("MIXED_USE", "inferred", "Fairview Concentrated Business"),
        "FT": ("MIXED_USE", "inferred", "Fairview Transition"),
    },
    "Elmhurst": {
        "R4": ("MF_APT", "layer", "Limited General Residence"),
        "R5": ("MF_APT", "layer", "Specialty Residence"),
        "CBC": ("MIXED_USE", "layer", "Central Business Core"),
        "CBOC": ("MIXED_USE", "layer", "Central Business Outer Core"),
        "CBOCR": ("MIXED_USE", "layer", "Central Business Outer Core Residential"),
    },
    "Glen Ellyn": {
        "R3": ("MF_APT", "layer", "Multi-Family Residential District"),
        "R4": ("MF_APT", "layer", "Multi-Family Residential District"),
        "R5": ("MF_ATT", "code", "Planned Residential District"),
        "C5A": ("MIXED_USE", "layer", "Central Business District (Retail Core)"),
        "C5B": ("MIXED_USE", "layer", "Central Business District (Service)"),
        "C6": ("MIXED_USE", "layer", "Commercial/Multi-Use Planned Development"),
    },
    "Glendale Heights": {
        "R-4": ("MF_ATT", "layer", "Attached Residential District"),
        "R-5": ("MF_APT", "layer", "Multi-Family Residential District"),
    },
    "Hanover Park": {
        "R-4": ("MF_APT", "code", "Multifamily Residence District"),
        "VC-R": ("MF_ATT", "layer", "Village Center Mixed Residential"),
        "VC-C": ("MIXED_USE", "layer", "Village Center Mixed-Use Core"),
        "VC-N": ("MIXED_USE", "layer", "Village Center Neighborhood Mix"),
    },
    "Lisle": {
        "R-3": ("MF_ATT", "code", "Single and Two Family district; duplexes and townhouses permitted"),
        "R-4": ("MF_APT", "code", "Multi Family Residential: apartment and condominium buildings"),
        "B-3A": ("MIXED_USE", "code", "Central Business; multi-unit by special use"),
        "B-3B": ("MIXED_USE", "code", "Central Perimeter Business; multi-unit by special use"),
    },
    "Lombard": {
        "R3": ("MF_ATT", "layer", "Multiple Family Residential (attached)"),
        "R4": ("MF_APT", "code", "Multiple Family Residential"),
        "R5": ("MF_APT", "code", "Multiple Family Residential"),
        "R6": ("MF_APT", "code", "Multiple Family Residential"),
        "B5": ("MIXED_USE", "inferred", "Central Business (downtown)"),
        "B5A": ("MIXED_USE", "inferred", "Downtown Perimeter"),
    },
    "Naperville": {
        "R2": ("MF_ATT", "layer", "Single-family & low density multi-family"),
        "R3": ("MF_APT", "layer", "Medium density multi-family"),
        "R3A": ("MF_APT", "layer", "Medium density multi-family"),
        "R4": ("MF_APT", "layer", "High density multi-family"),
        "B4": ("MIXED_USE", "code", "Downtown Core: dwelling units listed"),
        "B5": ("MIXED_USE", "code", "Secondary Downtown: dwelling units above the ground floor"),
        "TU": ("MIXED_USE", "code", "Transitional Use: dwelling units listed"),
    },
    "Oak Brook": {
        "R-5": ("MF_ATT", "inferred", "R-5 Residence (attached/townhouse) district"),
    },
    "Roselle": {
        "R-3": ("MF_ATT", "code", "General Residence: single family to multiple family"),
        "R-4": ("MF_APT", "code", "Multiple-Family Residence: multiple-family dwellings and townhomes"),
        "B-3": ("MIXED_USE", "code", "Town Center: multifamily, townhouses, mixed-use development"),
    },
    "Villa Park": {
        "RM-9": ("MF_APT", "code", "Residential Multi-Unit District; multi-unit building permitted"),
        "MX-R1": ("MF_ATT", "layer", "Mixed Residential District 1"),
        "MX-R2": ("MF_ATT", "layer", "Mixed Residential District 2"),
        "MX-1": ("MIXED_USE", "layer", "Mixed-Use TOD"),
        "MX-2": ("MIXED_USE", "layer", "Mixed-Use Main Street"),
        "MX-3": ("MIXED_USE", "layer", "Mixed-Use Corridor"),
        "MX-T": ("MIXED_USE", "layer", "Mixed Transitional (Office-Residential)"),
    },
    "Warrenville": {
        "R-6": ("MF_APT", "code", "Multi-Family Residential: single-, two-, and multiple-family dwellings"),
    },
    "West Chicago": {
        "R-6": ("MF_APT", "code", "R-6 Residential District (multi-family)"),
        "B-1": ("MIXED_USE", "inferred", "Central Business District (downtown)"),
    },
    "Westmont": {
        "R-4": ("MF_APT", "code", "General Residential; multi-unit building permitted"),
        "R-5": ("MF_APT", "code", "General Residential; multi-unit building permitted"),
        "R-7": ("MF_APT", "code", "Downtown Residential; multi-unit building permitted"),
        "B-1": ("MIXED_USE", "code", "Downtown Edge; multi-unit building permitted"),
        "B-1(A)": ("MIXED_USE", "code", "Downtown Core; mixed-use residential"),
    },
    "Wheaton": {
        "R5": ("MF_ATT", "code", "Single-family and multiple-family dwellings"),
        "R6": ("MF_APT", "code", "Single- and multiple-family dwellings, limited business"),
        "R7": ("MF_APT", "code", "Multiple-family dwellings, limited business"),
        "C2": ("MIXED_USE", "inferred", "Retail Core Business (downtown)"),
        "C4": ("MIXED_USE", "code", "CBD Perimeter Commercial: residential structures"),
        "RR1": ("MIXED_USE", "code", "Roosevelt Road Corridor: commercial, office, residential"),
        "RR2": ("MIXED_USE", "code", "Roosevelt Road Corridor"),
        "RR3": ("MIXED_USE", "code", "Roosevelt Road Corridor"),
        "RR4": ("MIXED_USE", "code", "Roosevelt Road Corridor"),
    },
    "Willowbrook": {
        "R4": ("MF_ATT", "layer", "Single Family Attached District"),
        "R5": ("MF_APT", "layer", "Multiple Family District"),
    },
    "Wood Dale": {
        "R-G": ("MF_APT", "code", "General Residential: attached and multiple-family buildings"),
        "TCB": ("MIXED_USE", "code", "Town Center Business: commercial, residential, mixed-use"),
    },
    "Woodridge": {
        "A-1": ("MF_ATT", "code", "Attached residential district"),
        "A-2": ("MF_APT", "code", "Multiple-unit dwellings permitted"),
    },
}

LABELS = {
    "MF_APT": "Multi-family (apartments)",
    "MF_ATT": "Multi-family (townhouse/attached)",
    "MIXED_USE": "Commercial/mixed-use allowing apartments",
}


def norm(code):
    """Normalize a raw zoning value to a base district code (strip PUD/PD/SP/(S)/(C) suffixes)."""
    if code is None:
        return ""
    c = str(code).upper().strip()
    for suf in (" SP PD", " PD SP", " SP", " PD", " PUD", " PA", " EDA PUD", " EDA"):
        if c.endswith(suf):
            c = c[: -len(suf)]
    if c.endswith("PD") and len(c) > 3 and c[:-2] not in ("", "O"):
        c = c[:-2]  # Lombard style "R3PD"
    c = c.replace("(S)", "").replace("(C)", "")
    return c.replace(" ", "")


def classify(town, raw):
    code = norm(raw)
    hit = CLASSES.get(town, {}).get(code)
    return (code,) + (hit if hit else (None, None, None))
