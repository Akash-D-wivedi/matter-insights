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
# ──────────────────────────────────────────────────────────────────────────────
#   MULTI-MATERIAL COMPARISON  (Radar · Parallel-coords · Heat-map)
# ──────────────────────────────────────────────────────────────────────────────
import plotly.graph_objects as go
import plotly.express as px

st.header("Compare materials")

###############################################################################
# ❶ pick samples & axes
###############################################################################
all_numeric = df.select_dtypes("number").columns.tolist()

samples = st.multiselect(
    "Pick 2 – 10 materials",
    df["formula_pretty"].unique(),
    key="cmp-samples",
)

axes = st.multiselect(
    "Pick 2 – 10 numeric properties",
    all_numeric,
    default=all_numeric[:6],
    key="cmp-axes",
)

if not (2 <= len(samples) <= 10 and 2 <= len(axes) <= 10):
    st.info("Select 2–10 materials **and** 2–10 numeric properties to compare.")
    st.stop()

# subset + drop rows with any NaN in the chosen axes
sub = df.loc[df.formula_pretty.isin(samples), ["formula_pretty", *axes]].dropna()
if sub.empty:
    st.error("All chosen properties contain missing values for these samples.")
    st.stop()

###############################################################################
# ❷ RADAR plot (keep for ≤ 6 materials & ≤ 6 axes)
###############################################################################
if len(samples) <= 6 and len(axes) <= 6:
    radar_df = sub.melt(id_vars="formula_pretty",
                        var_name="property", value_name="value")
    st.subheader("📈 Radar chart")
    st.plotly_chart(
        px.line_polar(
            radar_df,
            r="value",
            theta="property",
            color="formula_pretty",
            line_close=True,
            height=500,
        ),
        use_container_width=True,
    )

###############################################################################
# ❸ PARALLEL-COORDINATES  (robust → no NaN, no zero-range axes)
###############################################################################
st.subheader("🪢 Parallel coordinates")

# give every sample a numeric colour (required by Plotly)
sub = sub.copy()
sub["sample_id"] = sub["formula_pretty"].astype("category").cat.codes + 1

dimensions = []
for col in axes:
    vals = sub[col].astype(float)  # make sure it’s numeric
    vmin, vmax = vals.min(), vals.max()
    if vmin == vmax:               # widen a collapsed range
        pad = 1e-9 if vmax == 0 else abs(vmax) * 0.05
        vmin -= pad
        vmax += pad
    dimensions.append(
        dict(label=col.replace("_", " "),
             values=vals,
             range=[vmin, vmax])
    )

fig_pc = go.Figure(
    go.Parcoords(
        line = dict(color=sub["sample_id"],
                    colorscale="Turbo",
                    showscale=False),
        dimensions = dimensions,
    )
)
st.plotly_chart(fig_pc, use_container_width=True, height=550)

###############################################################################
# ❹ HEAT-MAP  (always works, handy for lots of data)
###############################################################################
st.subheader("🌡 Heat-map (values scaled 0-1 for visual comparison)")

# min-max normalise for colour only (does NOT affect original numbers)
hm = sub.set_index("formula_pretty")
norm = (hm - hm.min()) / (hm.max() - hm.min() + 1e-12)
st.plotly_chart(
    px.imshow(
        norm,
        labels=dict(x="property", y="material", color="scaled value"),
        x=hm.columns,
        y=hm.index,
        height=400 + 20 * len(hm),  # auto-grow with rows
    ),
    use_container_width=True,
)