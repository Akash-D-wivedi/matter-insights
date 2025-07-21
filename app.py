import duckdb, streamlit as st, plotly.express as px

con = duckdb.connect("materials.duckdb")
df  = con.execute("SELECT * FROM materials").fetch_df()

st.set_page_config(page_title="Matter Insights", layout="wide")
st.title("Matter Insights – Material Explorer (alpha)")

# ── sidebar search ─────────────────────────────────────────────────────────
formula = st.sidebar.text_input("Search formula (e.g. Fe2O3)").strip()
if formula:
    df = df[df.formula_pretty.str.contains(formula, case=False)]

# --- scatter plot -----------------------------------------------------------
x = st.selectbox("X-axis", df.columns, index=df.columns.get_loc("density"))
y = st.selectbox("Y-axis", df.columns, index=df.columns.get_loc("formation_energy_per_atom"))

st.plotly_chart(
    px.scatter(df, x=x, y=y, hover_name="formula_pretty", height=600),
    use_container_width=True,
)

# Decide which columns are numeric only --------------------------------------
numeric_cols = df.select_dtypes("number").columns.tolist()

# --- radar plot -------------------------------------------------------------
st.subheader("Compare materials – radar")
choices_radar = st.multiselect("Pick 2 – 5 samples", df["formula_pretty"].unique())
if 2 <= len(choices_radar) <= 5 and len(numeric_cols) >= 3:
    melt = (
        df.loc[df.formula_pretty.isin(choices_radar), ["formula_pretty", *numeric_cols]]
          .melt(id_vars="formula_pretty", var_name="property", value_name="value")
    )

    # normalise 0-1 per property so shapes are comparable
    melt["value_norm"] = (
        melt.groupby("property")["value"].transform(
            lambda s: (s - s.min()) / (s.max() - s.min() + 1e-9)
        )
    )

    st.plotly_chart(
        px.line_polar(
            melt,
            r="value_norm",
            theta="property",
            color="formula_pretty",
            line_close=True,
            height=500,
        ),
        use_container_width=True,
    )

# --- parallel coordinates plot ----------------------------------------------
st.subheader("Compare materials – parallel coordinates")
choices_pc = st.multiselect(
    "Pick 2 – 10 samples (numeric properties only)",
    df["formula_pretty"].unique(),
    key="pc",
)
if 2 <= len(choices_pc) <= 10 and len(numeric_cols) >= 2:
    norm = df.loc[df.formula_pretty.isin(choices_pc), ["formula_pretty", *numeric_cols]].copy()

    # normalise numeric columns 0-1
    for col in numeric_cols:
        col_min, col_max = norm[col].min(), norm[col].max()
        norm[col] = (norm[col] - col_min) / (col_max - col_min + 1e-9)

    fig_pc = px.parallel_coordinates(
        norm,
        color="formula_pretty",
        dimensions=numeric_cols,
        labels={c: c.replace("_", " ") for c in numeric_cols},
    )
    st.plotly_chart(fig_pc, use_container_width=True)

elif len(numeric_cols) < 2:
    st.info("Not enough numeric columns to draw a parallel-coordinates plot.")