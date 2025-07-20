import duckdb, streamlit as st, plotly.express as px

con = duckdb.connect("materials.duckdb")
df  = con.execute("SELECT * FROM materials").fetch_df()

# ── keep only the columns you exposed in download.py ─────────────────────────
ALLOWED = set(df.columns)            # already limited above – defensive line
numeric = [c for c in df.columns if df[c].dtype.kind in "if" and c in ALLOWED]

# ── Streamlit UI ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="Matter Insights", layout="wide")
st.title("Matter Insights – Material Explorer (alpha)")

# --- sidebar search ---
formula = st.sidebar.text_input("Search formula (e.g. Fe₂O₃)").strip()
if formula:
    df = df[df.formula_pretty.str.contains(formula, case=False)]

# --- scatter plot ---
x = st.selectbox("X-axis", numeric, index=numeric.index("density"))
y = st.selectbox("Y-axis", numeric, index=numeric.index("formation_energy_per_atom"))
st.plotly_chart(
    px.scatter(df, x=x, y=y, hover_name="formula_pretty", height=600),
    use_container_width=True)

# --- radar / polar compare ---
st.subheader("Compare materials")
choices = st.multiselect("Pick 2 – 5 samples", df["formula_pretty"].unique())
if 2 <= len(choices) <= 5:
    sub  = df[df.formula_pretty.isin(choices)][["formula_pretty", x, y]]
    melt = sub.melt(id_vars="formula_pretty",
                    var_name="property", value_name="value")
    st.plotly_chart(
        px.line_polar(melt, r="value", theta="property",
                      color="formula_pretty", line_close=True, height=500),
        use_container_width=True)
