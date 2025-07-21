import duckdb, streamlit as st, plotly.express as px

con = duckdb.connect("materials.duckdb")
df  = con.execute("SELECT * FROM materials").fetch_df()

st.set_page_config(page_title="Matter Insights", layout="wide")
st.title("Matter Insights – Material Explorer (alpha)")

# ── sidebar search ─────────────────────────────────────────────────────────
formula = st.sidebar.text_input("Search formula (e.g. Fe2O3)").strip()
if formula:
    df = df[df.formula_pretty.str.contains(formula, case=False)]

# --- scatter plot ----------------------------------------------------------
x = st.selectbox("X-axis", df.columns, index=df.columns.get_loc("density"))
y = st.selectbox("Y-axis", df.columns, index=df.columns.get_loc("formation_energy_per_atom"))
st.plotly_chart(
    px.scatter(df, x=x, y=y, hover_name="formula_pretty", height=600),
    use_container_width=True,
)

# ---------------------------------------------------------------------------
# 1) RADAR PLOT (kept, but limited to numeric columns + 0-1 scaling)
# ---------------------------------------------------------------------------
st.subheader("Compare materials – radar")

choices = st.multiselect(
    "Pick 2 – 5 samples", df["formula_pretty"].unique(), key="radar_pick"
)

if 2 <= len(choices) <= 5:
    numeric_cols = df.select_dtypes("number").columns.tolist()
    sub = df[df.formula_pretty.isin(choices)][["formula_pretty", *numeric_cols]]

    # min-max normalise for fair radial display
    norm = sub.copy()
    norm[numeric_cols] = (norm[numeric_cols] - norm[numeric_cols].min()) / (
        norm[numeric_cols].max() - norm[numeric_cols].min()
    )

    melt = norm.melt(
        id_vars="formula_pretty",
        var_name="property",
        value_name="value",
    )

    fig_radar = px.line_polar(
        melt,
        r="value",
        theta="property",
        color="formula_pretty",
        line_close=True,
        height=500,
    )
    st.plotly_chart(fig_radar, use_container_width=True)

# ---------------------------------------------------------------------------
# 2) PARALLEL-COORDINATES (new)
# ---------------------------------------------------------------------------
st.subheader("Compare materials – parallel coordinates")

choices_pc = st.multiselect(
    "Pick 2 – 10 samples", df["formula_pretty"].unique(), key="pc_pick"
)

if 2 <= len(choices_pc) <= 10:
    numeric_cols = df.select_dtypes("number").columns.tolist()
    sub = df[df.formula_pretty.isin(choices_pc)][["formula_pretty", *numeric_cols]]

    # min-max normalise per column
    norm = sub.copy()
    norm[numeric_cols] = (norm[numeric_cols] - norm[numeric_cols].min()) / (
        norm[numeric_cols].max() - norm[numeric_cols].min()
    )

    fig_pc = px.parallel_coordinates(
        norm,
        dimensions=numeric_cols,
        color="formula_pretty",
        labels={c: c.replace("_", " ") for c in numeric_cols},
    )
    st.plotly_chart(fig_pc, use_container_width=True)