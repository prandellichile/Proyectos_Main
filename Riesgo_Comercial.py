import streamlit as st
from utils import generar_pareto, unir_cluster

def render(df):

    st.title("⚠️ Matriz de Riesgo Comercial")

    pareto = generar_pareto(df)
    df_cluster = unir_cluster(df, pareto)

    ventas_totales = df_cluster["Monto Neto"].sum()
    ventas_A = df_cluster[df_cluster["Cluster"] == "A"]["Monto Neto"].sum()

    dep_A_pct = ventas_A / ventas_totales * 100 if ventas_totales else 0

    st.metric("Dependencia en Clientes A", f"{dep_A_pct:.1f}%")

    st.markdown(
        f"""
        **Ventas por Cluster:**
        - A: ${ventas_A:,.0f}  
        - Total: ${ventas_totales:,.0f}
        """
    )

    if dep_A_pct >= 80:
        st.error("🔴 Riesgo Alto: Fuerte dependencia en clientes A.")
    elif dep_A_pct >= 60:
        st.warning("🟠 Riesgo Medio: Concentración elevada.")
    else:
        st.success("🟢 Riesgo Bajo: Distribución equilibrada.")
