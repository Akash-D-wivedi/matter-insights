###############################################################################
#  app.py  –  Matter Insights dashboard
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

# ──────────────────────────────────────────────────────────────────────────────
#  Page settings
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Matter Insights", layout="wide")
st.title("Matter Insights – Material Explorer")

# ──────────────────────────────────────────────────────────────────────────────
#  Sidebar quick filter by formula
# ──────────────────────────────────────────────────────────────────────────────
formula = st.sidebar.text_input("Search formula (e.g. Fe2O3)").strip()
if formula:
    df = df[df.formula_pretty.str.contains(formula, case=False)]

# ──────────────────────────────────────────────────────────────────────────────
#  Scatter plot
# ──────────────────────────────────────────────────────────────────────────────
x = st.selectbox("X-axis", df.columns, index=df.columns.get_loc("density"))
y = st.selectbox(
    "Y-axis", df.columns,
    index=df.columns.get_loc("formation_energy_per_atom")
)

st.plotly_chart(
    px.scatter(df, x=x, y=y, hover_name="formula_pretty", height=600),
    use_container_width=True,
)

# ──────────────────────────────────────────────────────────────────────────────
#  Numeric columns utility
# ──────────────────────────────────────────────────────────────────────────────
numeric_cols = df.select_dtypes("number").columns.tolist()

###############################################################################
# ❶ RADAR  – compare up to 8×8
###############################################################################
st.subheader("Compare materials – radar")

choices_radar = st.multiselect(
    "Pick 2 – 8 materials", df["formula_pretty"].unique(), key="radar-samples"
)
axes_radar = st.multiselect(
    "Pick 3 – 8 numeric properties", numeric_cols, default=numeric_cols[:5],
    key="radar-axes"
)

if 2 <= len(choices_radar) <= 8 and 3 <= len(axes_radar) <= 8:
    melt = (
        df.loc[df.formula_pretty.isin(choices_radar),
               ["formula_pretty", *axes_radar]]
          .melt(id_vars="formula_pretty", var_name="property", value_name="value")
    )
    # 0-1 scale per property
    melt["value_norm"] = (
        melt.groupby("property")["value"]
            .transform(lambda s: (s - s.min()) / (s.max() - s.min() + 1e-12))
    )

    st.plotly_chart(
        px.line_polar(
            melt, r="value_norm", theta="property",
            color="formula_pretty", line_close=True, height=550,
        ),
        use_container_width=True,
    )

###############################################################################
# ❷ HEAT-MAP  – any size, any number of axes
###############################################################################
st.subheader("Compare materials – heat-map")

samples_hm = st.multiselect(
    "Pick 2 + materials", df["formula_pretty"].unique(), key="hm-samples"
)
axes_hm = st.multiselect(
    "Pick 2 + numeric properties", numeric_cols, default=numeric_cols[:8],
    key="hm-axes"
)

if len(samples_hm) >= 2 and len(axes_hm) >= 2:
    sub = (
        df.loc[df.formula_pretty.isin(samples_hm),
               ["formula_pretty", *axes_hm]]
          .set_index("formula_pretty")
          .dropna(how="all")            # drop rows that are all-NaN
          .dropna(axis=1, how="all")     # drop cols that are all-NaN
    )

    if not sub.empty:
        norm = (sub - sub.min()) / (sub.max() - sub.min() + 1e-12)
        st.plotly_chart(
            px.imshow(
                norm,
                labels=dict(x="property", y="material", color="scaled value"),
                x=sub.columns, y=sub.index,
                height=400 + 20 * len(sub),
                aspect="auto",
            ),
            use_container_width=True,
        )
    else:
        st.info("Nothing left to plot after drop-na filtering.")
###############################################################################
#  End of app
###############################################################################
