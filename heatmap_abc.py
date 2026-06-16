import streamlit as st
import altair as alt
from utils import generar_pareto, unir_cluster
import pandas as pd

def render(df):

    st.title("🔥 Heatmap Vendedor × Cluster ABC")

    pareto = generar_pareto(df)
    df_cluster = unir_cluster(df, pareto)

    heat = (
        df_cluster.groupby(["Vendedor", "Cluster"])["Monto Neto"]
        .sum()
        .reset_index()
    )

    # Ordenar vendedores por ventas totales
    orden_vendedores = (
        df_cluster.groupby("Vendedor")["Monto Neto"]
        .sum()
        .sort_values(ascending=False)
        .index
    )

    heat["Vendedor"] = pd.Categorical(heat["Vendedor"], categories=orden_vendedores, ordered=True)

    chart = alt.Chart(heat).mark_rect().encode(
        x="Cluster:N",
        y=alt.Y("Vendedor:N", sort=orden_vendedores),
        color=alt.Color("Monto Neto:Q", scale=alt.Scale(scheme="reds"), legend=None),
        tooltip=["Vendedor", "Cluster", "Monto Neto"]
    )

    st.altair_chart(chart, width="stretch")
