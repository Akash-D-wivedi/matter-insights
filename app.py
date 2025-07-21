###############################################################################
#  app.py  –  Matter Insights dashboard (+ Help tab)
###############################################################################
import duckdb
import streamlit as st
import pandas as pd
import plotly.express as px

# ──────────────────────────────────────────────────────────────────────────────
#  DB → DataFrame
# ──────────────────────────────────────────────────────────────────────────────
con = duckdb.connect("materials.duckdb")
df  = con.execute("SELECT * FROM materials").fetch_df()
numeric_cols = df.select_dtypes("number").columns.tolist()

# ──────────────────────────────────────────────────────────────────────────────
#  Page settings + Tabs
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Matter Insights", layout="wide")

tab_dash, tab_help = st.tabs(["📊 Dashboard", "ℹ️ Help & Methodology"])

###############################################################################
#  DASHBOARD  TAB  ─────────────────────────────────────────────────────────────
###############################################################################
with tab_dash:
    st.title("Matter Insights – Material Explorer")

    # sidebar quick filter
    formula = st.sidebar.text_input("Search formula (e.g. Fe2O3)").strip()
    df_vis  = df if not formula else df[df.formula_pretty.str.contains(formula,
                                                                       case=False)]

    # --------------------- Scatter ------------------------------------------------
    x = st.selectbox("X-axis", df_vis.columns,
                     index=df_vis.columns.get_loc("density"))
    y = st.selectbox("Y-axis", df_vis.columns,
                     index=df_vis.columns.get_loc("formation_energy_per_atom"))

    st.plotly_chart(
        px.scatter(df_vis, x=x, y=y, hover_name="formula_pretty", height=600),
        use_container_width=True,
    )

    # --------------------- Radar --------------------------------------------------
    st.subheader("Compare materials – radar")

    choices_radar = st.multiselect("Pick 2 – 8 materials",
                                   df_vis["formula_pretty"].unique(),
                                   key="radar-samples")
    axes_radar = st.multiselect("Pick 3 – 8 numeric properties",
                                numeric_cols, default=numeric_cols[:5],
                                key="radar-axes")

    if 2 <= len(choices_radar) <= 8 and 3 <= len(axes_radar) <= 8:
        melt = (
            df_vis.loc[df_vis.formula_pretty.isin(choices_radar),
                       ["formula_pretty", *axes_radar]]
              .melt(id_vars="formula_pretty",
                    var_name="property", value_name="value")
        )
        # 0-1 scale per property
        melt["value_norm"] = (
            melt.groupby("property")["value"]
                .transform(lambda s: (s - s.min()) / (s.max() - s.min() + 1e-12))
        )

        st.plotly_chart(
            px.line_polar(melt, r="value_norm", theta="property",
                          color="formula_pretty", line_close=True, height=550),
            use_container_width=True,
        )

    # --------------------- Heat-map ----------------------------------------------
    st.subheader("Compare materials – heat-map")

    samples_hm = st.multiselect("Pick 2 + materials", df_vis["formula_pretty"].unique(),
                                key="hm-samples")
    axes_hm = st.multiselect("Pick 2 + numeric properties", numeric_cols,
                             default=numeric_cols[:8], key="hm-axes")

    if len(samples_hm) >= 2 and len(axes_hm) >= 2:
        sub = (
            df_vis.loc[df_vis.formula_pretty.isin(samples_hm),
                       ["formula_pretty", *axes_hm]]
              .set_index("formula_pretty")
              .dropna(how="all")
              .dropna(axis=1, how="all")
        )
        if not sub.empty:
            norm = (sub - sub.min()) / (sub.max() - sub.min() + 1e-12)
            st.plotly_chart(
                px.imshow(norm,
                          labels=dict(x="property", y="material", color="scaled value"),
                          x=sub.columns, y=sub.index,
                          height=400 + 22*len(sub), aspect="auto"),
                use_container_width=True,
            )
        else:
            st.info("Nothing left to plot after removing empty rows/columns.")

###############################################################################
#  HELP / METHODOLOGY TAB  ────────────────────────────────────────────────────
###############################################################################
with tab_help:
    st.header("How to read the dashboard")

    st.markdown("""
### 1 · Column glossary

| Column | Unit | Meaning |
|--------|------|---------|
| **material_id** | –  | identifier used by Materials Project |
| **formula_pretty** | – | conventional chemical formula |
| **nsites** | atoms | number of atomic sites in the reported unit-cell |
| **volume** | Å³ | unit-cell volume |
| **density** | g cm⁻³ | mass / volume of the unit-cell |
| **formation_energy_per_atom** | eV atom⁻¹ | relative to elemental ground states |
| **energy_above_hull** | eV atom⁻¹ | stability above convex hull |
| **equilibrium_reaction_energy_per_atom** | eV atom⁻¹ | reaction energy w.r.t. competing phases |
| **band_gap** | eV | computed electronic band gap |
| **bulk_modulus** | GPa | K<sub>Voigt</sub> (compressibility) |
| **shear_modulus** | GPa | G<sub>Voigt</sub> (rigidity) |
| **universal_anisotropy** | – | elastic anisotropy index |
| **total_magnetization** | µ<sub>B</sub> | cell-integrated magnetic moment |
| **ordering** | – | FM / AFM / NM … |
| **is_stable** | 0/1 | 1 = on MP stability hull |

*(Only columns present in `materials.duckdb` are listed.)*

---

### 2 · Scaling used for visual comparisons

| Plot | Scaling | Why |
|------|---------|-----|
| **Scatter** | raw values (no scaling) | lets you judge absolute magnitudes |
| **Radar** | **min–max 0 – 1 per axis** | overlays different units on a single polar chart; shape shows *relative* performance |
| **Heat-map** | min–max 0 – 1 inside each selected column | bright = high within this subset; easy pattern spotting |

$$\\text{scaled} = \\frac{x - x_{\\min}}{x_{\\max} - x_{\\min} + \\varepsilon}$$  
with a tiny \\(\\varepsilon = 10^{-12}\\) to avoid divide-by-zero.

---

### 3 · Interpreting the visuals

* **Radar**—Ideal materials bulge outward on desirable axes; inward on undesirable (e.g. low energy above hull).  
  Compare *shapes*, not absolute radii.
* **Heat-map**—Rows = materials, Columns = properties.  
  Use the colour gradient to spot extremes; hover to read exact numbers.
* **Scatter**—Hover gives precise x/y; use the sidebar search to narrow down.

Happy exploring — and feel free to open issues on GitHub for new properties or plots!
""")