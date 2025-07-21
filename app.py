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

# 〈START – REPLACE THE WHOLE PARALLEL-COORDINATES BLOCK〉
# ── PARALLEL-COORDINATES PLOT ───────────────────────────────────────────────
st.subheader("Compare materials – parallel coordinates")

# --- pick the materials -----------------------------------------------------
samples = st.multiselect(
    "Pick 2 – 10 materials (numeric properties only)",
    df["formula_pretty"].unique(),
    key="pc-samples"
)

# --- pick the numeric axes --------------------------------------------------
all_numeric = df.select_dtypes("number").columns.tolist()
axes = st.multiselect(
    "Choose 2 – 10 numeric properties to draw as axes",
    all_numeric,
    default=all_numeric[:6],
    key="pc-axes"
)

# --- build the plot ---------------------------------------------------------
if 2 <= len(samples) <= 10 and 2 <= len(axes) <= 10:

    # subset to the chosen materials & axes
    sub = df.loc[df.formula_pretty.isin(samples), ["formula_pretty", *axes]].copy()

    # give every sample a numeric ID for the colour scale
    sub["sample_id"] = sub["formula_pretty"].astype("category").cat.codes + 1

    # add original ranges (no 0-1 normalising)
    dims = [
        dict(
            label     = a.replace("_", " "),
            values    = sub[a],
            range     = [sub[a].min(), sub[a].max()],
            tickfont  = dict(size=11),
        )
        for a in axes
    ]

    fig_pc = px.parallel_coordinates(
        sub,
        dimensions=dims,
        color="sample_id",
        color_continuous_scale="Turbo",
        labels={"sample_id": "sample"},
    ).update_coloraxes(showscale=False)

    # wider container gives a horizontal scroll bar when many axes
    st.plotly_chart(
        fig_pc,
        use_container_width=False,
        height=550,
        scrolling=True,
    )

elif len(samples) < 2:
    st.info("Pick at least two materials.")
elif len(axes) < 2:
    st.info("Pick at least two numeric properties.")
else:
    st.info("You can compare up to 10 materials and 10 axes at once.")