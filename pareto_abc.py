import streamlit as st
import altair as alt
from utils import generar_pareto

def render(df):

    st.title("📊 Pareto de Clientes + Clustering ABC")

    pareto = generar_pareto(df)

    # Ordenar de mayor a menor
    pareto = pareto.sort_values("Monto Neto", ascending=False)

    # Gráfico Pareto
    bars = alt.Chart(pareto).mark_bar().encode(
        x=alt.X("Razon Social:N", sort=None),
        y=alt.Y("Monto Neto:Q", axis=alt.Axis(format="~s")),
        color="Cluster:N"
    )

    line = alt.Chart(pareto).mark_line(color="#2980b9", strokeWidth=3).encode(
        x="Razon Social:N",
        y=alt.Y("Porcentaje Acumulado:Q", axis=alt.Axis(format="~s"))
    )

    st.altair_chart(alt.layer(bars, line), width="stretch")

    st.dataframe(
        pareto.style.format({
            "Monto Neto": "${:,.0f}",
            "Porcentaje": "{:.2%}",
            "Porcentaje Acumulado": "{:.1f}%"
        })
    )
