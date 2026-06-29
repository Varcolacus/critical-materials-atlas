"""Lookup HS6 earliest revision from official correlation sources."""
import re
import pandas as pd
import pdfplumber
from pathlib import Path

ROOT = Path(r"C:\Toma\critical-materials-atlas")
CODES = [
    "850511", "810411", "811292", "250490", "810194", "282200", "720293", "252800",
    "283691", "811010", "711011", "711021", "252922", "810820", "280469", "252910",
    "720292", "260200", "260600", "251010", "251110", "280480", "811212", "811231",
    "283692", "280470", "810320", "270112", "280429", "740311", "750210",
]
LABELS = {
    "850511": "magnets", "810411": "magnesium", "811292": "germanium/gallium",
    "250490": "graphite", "810194": "tungsten", "282200": "cobalt", "720293": "niobium",
    "252800": "boron", "283691": "lithium", "811010": "antimony", "711011": "platinum",
    "711021": "palladium", "252922": "fluorspar", "810820": "titanium", "280469": "silicon",
    "252910": "feldspar", "720292": "vanadium", "260200": "manganese", "260600": "bauxite",
    "251010": "phosphate", "251110": "baryte", "280480": "arsenic", "811212": "beryllium",
    "811231": "hafnium", "283692": "strontium", "280470": "phosphorus", "810320": "tantalum",
    "270112": "cokingcoal", "280429": "helium", "740311": "copper", "750210": "nickel",
}
BACI = {"HS1992": 1995, "HS1996": 1995, "HS2002": 2002, "HS2007": 2007,
        "HS2012": 2012, "HS2017": 2017, "HS2022": 2022}

# HS1996 presence (UNSD CPC concordance + correlation xls)
hs96_xls = pd.read_excel(ROOT / "tmp_hs96_92.xls", sheet_name="Correlation Table")
hs96_set = set(hs96_xls["HS 1996"].astype(str).str.replace(".0", "", regex=False))

# HS1992: 1:1 from hs96_92 table
hs92_map = {}
for c in CODES:
    row = hs96_xls[hs96_xls["HS 1996"].astype(str).str.replace(".0", "", regex=False) == c]
    if not row.empty and row.iloc[0]["Relationship"] == "'1:1":
        hs92_map[c] = True

# Parse W26 (96->02) Table II: new HS2002 code -> old HS1996 predecessor
w26 = "\n".join(p.extract_text() or "" for p in pdfplumber.open(ROOT / "tmp_W26_0202.pdf").pages)
created_2002 = {}
for m in re.finditer(
    r"(\d{2}\.\d{2}(?:\.\d{2})?)\s+(?:ex)?(\d{2}\.\d{2}(?:\.\d{2})?)",
    w26,
):
    new = re.sub(r"\D", "", m.group(1))[:6]
    old = re.sub(r"\D", "", m.group(2))[:6]
    if "Creation" in w26[m.start(): m.start() + 800] or "Subheading" in w26[m.start(): m.start() + 800]:
        created_2002.setdefault(new, set()).add(old)

# Manual verified from W26 narrative blocks
CREATED = {
    "811292": ("HS2002", "811291", "Creation of 8112.92 from ex8112.91 (G/MA/W/26)"),
    "811010": ("HS2002", "811000", "Subdivision of 8110.00 → 8110.10 (G/MA/W/26)"),
    "811212": ("HS2002", "811211", "Creation of 8112.12 from ex8112.11 (G/MA/W/26)"),
    "810820": ("HS2002", "810810", "8108.20 carved from ex8108.10 subdivision (G/MA/W/26)"),
    "810320": ("HS2002", "810310", "8103.20 carved from ex8103.10 subdivision (G/MA/W/26)"),
    "810194": ("HS2002", "810191", "8101.94 in HS2002; predecessors ex8101.91–93 (G/MA/W/26)"),
    "252800": ("HS2012", "252810+252890", "Merge 2528.10/2528.90 → 2528.00 (G/MA/W/105)"),
    "811231": ("HS2022", "811292", "New 8112.31 from ex8112.92 (G/MA/W/164)"),
}

BROAD = {
    "850511": "Broad: all permanent magnets of metal (not RE-specific)",
    "250490": "Broad/residual: other natural graphite",
    "811292": "Broad/pooled: Ga/Ge/Hf (until 2022) — other unwrought base metals basket",
    "270112": "Broad: all bituminous coal (coking is CN8-only distinction)",
    "280429": "Broad/residual: other rare gases (helium usually CN8 28042910)",
}

CHANGED_2022 = {
    "811292": "Yes — hafnium split to 8112.31 narrows 8112.92 scope (G/MA/W/164)",
    "811231": "Yes — newly created from ex8112.92 (G/MA/W/164)",
}

print("label|HS6|earliest_rev|baci|2017/2022_flag|note")
for c in CODES:
    if c in CREATED:
        rev, pred, note = CREATED[c]
    elif c in hs92_map:
        rev = "HS1992"
        pred, note = "—", "1:1 in HS1996↔HS1992 (UNSD); unchanged in later WCO tables"
    elif c in hs96_set:
        rev = "HS1996"
        pred, note = "—", "In HS1996; no HS1992 1:1 (chapter 81 / post-1992 structure)"
    else:
        rev, pred, note = "?", "?", "needs review"

    ch = "no"
    if c in CHANGED_2022:
        ch = CHANGED_2022[c]
    elif c == "252800":
        ch = "no (but HS2012 merge breaks 252810/252890 series)"

    broad = BROAD.get(c, "")
    print(f"{LABELS[c]}|{c}|{rev}|{BACI[rev]}|{ch}|{note}{'; '+broad if broad else ''}")