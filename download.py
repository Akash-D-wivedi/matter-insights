# download.py   – pull 500 Fe materials and store them in materials.duckdb
from mp_api.client import MPRester
import pandas as pd, duckdb

FIELDS    = ["material_id", "formula_pretty", "density",
             "formation_energy_per_atom"]
MAX_ROWS  = 500
rows      = []

with MPRester() as mpr:
    for doc in mpr.materials.summary.search(
            elements=["Fe"], fields=FIELDS, chunk_size=250):
        rows.append(doc.dict())
        if len(rows) >= MAX_ROWS:
            break           # stop the local loop at 500

df = pd.DataFrame(rows)

con = duckdb.connect("materials.duckdb")
con.register("tmp", df)                   # ← make DataFrame visible to SQL
con.execute("DROP TABLE IF EXISTS materials")
con.execute("CREATE TABLE materials AS SELECT * FROM tmp")
con.close()

print(f"✅  Saved {len(df)} rows into materials.duckdb")