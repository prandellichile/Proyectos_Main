import streamlit as st
import altair as alt
import pandas as pd
from utils import generar_pareto, unir_cluster

def render(df):

    st.title("📆 Evolución Mensual por Cluster ABC")

    pareto = generar_pareto(df)
    df_cluster = unir_cluster(df, pareto)

    evol = (
        df_cluster.groupby(["Año", "MesNum", "Cluster"])["Monto Neto"]
        .sum()
        .reset_index()
    )

    evol["Fecha"] = pd.to_datetime(
        evol["Año"].astype(str) + "-" + evol["MesNum"].astype(str) + "-01"
    )

    evol = evol.sort_values("Fecha")  # SOLO orden temporal

    chart = alt.Chart(evol).mark_line(point=True).encode(
        x="Fecha:T",
        y=alt.Y("Monto Neto:Q", axis=alt.Axis(format="~s")),
        color="Cluster:N",
        tooltip=["Año", "MesNum", "Cluster", "Monto Neto"]
    )

    st.altair_chart(chart, width="stretch")
