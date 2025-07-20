"""
download.py
Pull 500 Fe-based materials from Materials Project and store them in materials.duckdb
"""
from mp_api.client import MPRester
import pandas as pd, duckdb

# ---------------------------------------------------------------------------
# Pick ONLY the columns you want researchers to see later in the dashboard
# ---------------------------------------------------------------------------
FIELDS = [
    # identifiers
    "material_id", "formula_pretty",

    # basic structure / composition
    "nsites", "volume", "density",
    "spacegroup", "crystal_system",

    # thermodynamics
    "formation_energy_per_atom",     # eV/atom
    "energy_above_hull",             # eV/atom
    "equilibrium_reaction_energy_per_atom",

    # electronic
    "band_gap",                      # eV

    # mechanical (elastic tensor pre-digested by MP)
    "elasticity.anisotropy",         # unit-less
    "elasticity.G_Voigt",            # GPa
    "elasticity.K_Voigt",            # GPa

    # magnetic
    "magnetism.total_magnetization", # µB
    "magnetism.ordering",            # FM / AFM / NM …

    # convenience
    "is_stable"
]

MAX_ROWS = 500
rows     = []

with MPRester() as mpr:
    for doc in mpr.materials.summary.search(
            elements=["Fe"], fields=FIELDS, chunk_size=250):

        rows.append(doc.dict())
        if len(rows) >= MAX_ROWS:
            break

df = pd.DataFrame(rows)[FIELDS]      # ← keep only approved columns

# ---------------------------------------------------------------------------
# Save as a DuckDB table
# ---------------------------------------------------------------------------
con = duckdb.connect("materials.duckdb")
con.register("tmp", df)
con.execute("DROP TABLE IF EXISTS materials")
con.execute("CREATE TABLE materials AS SELECT * FROM tmp")
con.close()

print(f"✅  Saved {len(df)} rows into materials.duckdb")
