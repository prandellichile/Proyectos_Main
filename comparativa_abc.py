import streamlit as st
import altair as alt
from utils import generar_pareto, unir_cluster

def render(df):

    st.title("📊 Comparativa Año vs Año Anterior por Cluster ABC")

    pareto = generar_pareto(df)
    df_cluster = unir_cluster(df, pareto)

    anios = sorted(df["Año"].unique())
    anio_sel = st.multiselect("Años", anios, default=anios[-2:])

    df_comp = df_cluster[df_cluster["Año"].isin(anio_sel)]

    comp = (
        df_comp.groupby(["Año", "Cluster"])["Monto Neto"]
        .sum()
        .reset_index()
        .sort_values("Monto Neto", ascending=False)
    )

    chart = alt.Chart(comp).mark_bar().encode(
        x="Cluster:N",
        y=alt.Y("Monto Neto:Q", axis=alt.Axis(format="~s")),
        color="Año:N",
        column="Año:N"
    )

    st.altair_chart(chart, width="stretch")

    