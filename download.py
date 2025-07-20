"""
download.py
Pull 500 Fe-based materials from Materials Project and store them in materials.duckdb
"""
from mp_api.client import MPRester
import pandas as pd, duckdb

API_KEY = "jowrtF1dAxnFGHZrc4sh1Mj1HmKQvCjD"   # ← your key

FIELDS = [
    # identifiers
    "material_id", "formula_pretty",

    # basic structure / composition
    "nsites", "volume", "density",
    "symmetry.space_group_symbol", "symmetry.crystal_system",

    # thermodynamics
    "formation_energy_per_atom",
    "energy_above_hull",
    "equilibrium_reaction_energy_per_atom",

    # electronic
    "band_gap",

    # mechanical (elastic summary)
    "bulk_modulus", "shear_modulus", "universal_anisotropy",

    # magnetic
    "total_magnetization", "ordering",

    # convenience
    "is_stable",
]

MAX_ROWS = 500
rows = []

with MPRester(API_KEY) as mpr:
    for doc in mpr.materials.summary.search(
        elements=["Fe"], fields=FIELDS, chunk_size=250
    ):
        rows.append(doc.dict())
        if len(rows) >= MAX_ROWS:
            break

df = pd.DataFrame(rows)[FIELDS]

con = duckdb.connect("materials.duckdb")
con.register("tmp", df)
con.execute("DROP TABLE IF EXISTS materials")
con.execute("CREATE TABLE materials AS SELECT * FROM tmp")
con.close()

print(f"✅  Saved {len(df)} rows into materials.duckdb")