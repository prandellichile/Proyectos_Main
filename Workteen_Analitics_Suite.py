import streamlit as st
import pandas as pd
import sqlite3
import altair as alt

#configuracion general#

st.set_page_config(page_title="Analytics Suite", layout="wide")

LOGO_PATH = r"D:\Proyectos\Proyectos-main\Prandelli.png"

# HEADER CORPORATIVO

def header():
    col1, col2 = st.columns([1, 5])

    with col1:
        st.markdown(
            f"""
            <a href="https://prandelli.cl/" target="_blank">
                <img src="file:///{LOGO_PATH}" width="90">
            </a>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            """
            <h2 style='margin-bottom:0px;'>Analytics Suite</h2>
            <p style='color:#2c3e50; margin-top:0px;'>Inteligencia Comercial</p>
            """,
            unsafe_allow_html=True
        )


# UTILIDADES DE DATOS

@st.cache_data
def cargar_datos():
    conn = sqlite3.connect(r"D:\Proyectos\almacen_datos.db")
    df = pd.read_sql_query("SELECT * FROM ventas", conn)
    conn.close()
    df.columns = df.columns.str.strip()
    return df

def preparar_dataframe(df):
    df = df.copy()
    df["Fecha Docto"] = pd.to_datetime(df["Fecha Docto"], errors="coerce")
    df = df[df["Fecha Docto"].notna()]
    df["Año"] = df["Fecha Docto"].dt.year
    df["MesNum"] = df["Fecha Docto"].dt.month

    meses_es = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
                "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
    df["MesNombre"] = df["MesNum"].apply(lambda x: meses_es[x - 1])
    return df

def generar_pareto(df_filtrado):
    pareto = (
        df_filtrado.groupby("Razon Social")["Monto Neto"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    pareto["Porcentaje"] = pareto["Monto Neto"] / pareto["Monto Neto"].sum()
    pareto["Porcentaje Acumulado"] = pareto["Porcentaje"].cumsum() * 100

    def clasificar_abc(pct):
        if pct <= 79.9:
            return "A"
        elif pct <= 89.9:
            return "B"
        else:
            return "C"

    pareto["Cluster"] = pareto["Porcentaje Acumulado"].apply(clasificar_abc)
    return pareto

def unir_cluster(df_filtrado, pareto):
    return df_filtrado.merge(
        pareto[["Razon Social", "Cluster"]],
        on="Razon Social",
        how="left"
    )

# FILTROS GLOBALES (INCLUYE CLUSTER ABC)

def aplicar_filtros(df):
    st.sidebar.header("🔎 Filtros Globales")

    vendedores = df["Vendedor"].dropna().unique()
    clientes = df["Razon Social"].dropna().unique()
    anios = sorted(df["Año"].dropna().unique())
    meses = df["MesNombre"].dropna().unique()

    vendedor_sel = st.sidebar.multiselect("Vendedor", vendedores, default=list(vendedores))
    cliente_sel = st.sidebar.multiselect("Cliente", clientes, default=list(clientes))
    anio_sel = st.sidebar.multiselect("Año", anios, default=anios)
    mes_sel = st.sidebar.multiselect("Mes", meses, default=list(meses))

    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Cluster ABC")

    pareto = generar_pareto(df)
    df_cluster = unir_cluster(df, pareto)

    clusters = ["A", "B", "C"]
    cluster_sel = st.sidebar.multiselect("Cluster", clusters, default=clusters)

    df_filtrado = df_cluster[
        df_cluster["Vendedor"].isin(vendedor_sel) &
        df_cluster["Razon Social"].isin(cliente_sel) &
        df_cluster["Año"].isin(anio_sel) &
        df_cluster["MesNombre"].isin(mes_sel) &
        df_cluster["Cluster"].isin(cluster_sel)
    ]

    return df_filtrado, pareto, df_cluster

# PÁGINA: DASHBOARD COMERCIAL

def pagina_dashboard(df):
    st.title("📊 Dashboard Comercial")

    if df.empty:
        st.warning("No hay datos para los filtros seleccionados.")
        return

    meses_es = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
                "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

    años_ordenados = sorted(df["Año"].unique())

    if len(años_ordenados) >= 2:
        actual, anterior = años_ordenados[-1], años_ordenados[-2]
        df_actual = df[df["Año"] == actual]
        df_anterior = df[df["Año"] == anterior]

        ventas_actual = df_actual["Monto Neto"].sum()
        ventas_anterior = df_anterior["Monto Neto"].sum()
        delta_pct = round(((ventas_actual - ventas_anterior) / ventas_anterior * 100), 1) if ventas_anterior else 0

        clientes_actual = df_actual["Razon Social"].nunique()
        clientes_anterior = df_anterior["Razon Social"].nunique()
        delta_cli_pct = round(((clientes_actual - clientes_anterior) / clientes_anterior * 100), 1) if clientes_anterior else 0

        ticket_actual = ventas_actual / clientes_actual if clientes_actual else 0
        ticket_anterior = ventas_anterior / clientes_anterior if clientes_anterior else 0
        delta_ticket_pct = round(((ticket_actual - ticket_anterior) / ticket_anterior * 100), 1) if ticket_anterior else 0
    else:
        actual = años_ordenados[-1]
        ventas_actual = df["Monto Neto"].sum()
        clientes_actual = df["Razon Social"].nunique()
        ticket_actual = ventas_actual / clientes_actual if clientes_actual else 0
        delta_pct = delta_cli_pct = delta_ticket_pct = None

    col1, col2, col3 = st.columns(3)

    col1.metric(
        label=f"💰 Ventas {actual}",
        value=f"${ventas_actual:,.0f}",
        delta=f"{delta_pct:+.1f}%" if delta_pct is not None else "Sin comparación",
        delta_color="inverse" if delta_pct is not None and delta_pct < 0 else "normal"
    )

    col2.metric(
        label=f"👥 Clientes {actual}",
        value=clientes_actual,
        delta=f"{delta_cli_pct:+.1f}%" if delta_cli_pct is not None else "Sin comparación",
        delta_color="inverse" if delta_cli_pct is not None and delta_cli_pct < 0 else "normal"
    )

    col3.metric(
        label=f"🎟️ Ticket Promedio",
        value=f"${ticket_actual:,.0f}",
        delta=f"{delta_ticket_pct:+.1f}%" if delta_ticket_pct is not None else "Sin comparación",
        delta_color="inverse" if delta_ticket_pct is not None and delta_ticket_pct < 0 else "normal"
    )

    st.subheader("📈 Ventas por Vendedor (por Año)")
    ventas_vendedor = df.groupby(["Año", "Vendedor"])["Monto Neto"].sum().reset_index()
    pivot_ventas = (
        ventas_vendedor
        .pivot(index="Vendedor", columns="Año", values="Monto Neto")
        .fillna(0)
        .sort_values(by=actual, ascending=False)
    )
    st.dataframe(pivot_ventas.style.format("${:,.0f}"))

    st.subheader("🏢 Top Clientes")
    top_clientes = (
        df.groupby("Razon Social")["Monto Neto"]
        .sum()
        .sort_values(ascending=False)
        .head(20)
    )
    st.bar_chart(top_clientes.sort_values(ascending=False))

    st.subheader("📆 Evolución Mensual de Ventas")
    evolucion = df.groupby(["Año", "MesNum"])["Monto Neto"].sum().reset_index()
    evolucion["FechaEje"] = pd.to_datetime(evolucion["Año"].astype(str) + "-" + evolucion["MesNum"].astype(str) + "-01")
    evolucion = evolucion.sort_values("FechaEje")

    if len(años_ordenados) == 1:
        evolucion["Periodo"] = evolucion["MesNum"].apply(lambda x: meses_es[x - 1])
    else:
        evolucion["Periodo"] = evolucion["MesNum"].apply(lambda x: meses_es[x - 1]) + " " + evolucion["Año"].astype(str)

    st.line_chart(evolucion.set_index("FechaEje")["Monto Neto"])

    if not evolucion.empty:
        mes_pico = evolucion.loc[evolucion["Monto Neto"].idxmax()]
        st.success(f"📈 Mayor venta: {mes_pico['Periodo']} → ${mes_pico['Monto Neto']:,.0f}")

    st.subheader("📄 Detalle de Transacciones")
    st.dataframe(df)

    st.download_button(
        label="📥 Descargar datos filtrados",
        data=df.to_csv(index=False),
        file_name="reporte_filtrado.csv",
        mime="text/csv"
    )

# PÁGINA: PARETO ABC

def pagina_pareto(df, pareto):
    st.title("📊 Pareto de Clientes + Clustering ABC")

    if df.empty:
        st.warning("No hay datos para los filtros seleccionados.")
        return

    pareto = pareto.sort_values("Monto Neto", ascending=False)

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

# PÁGINA: EVOLUCIÓN ABC

def pagina_evolucion(df_cluster, pareto):
    st.title("📆 Evolución Mensual por Cluster ABC")

    if df_cluster.empty:
        st.warning("No hay datos para los filtros seleccionados.")
        return

    evol = (
        df_cluster.groupby(["Año", "MesNum", "Cluster"])["Monto Neto"]
        .sum()
        .reset_index()
    )

    evol["Fecha"] = pd.to_datetime(
        evol["Año"].astype(str) + "-" + evol["MesNum"].astype(str) + "-01"
    )
    evol = evol.sort_values("Fecha")

    chart = alt.Chart(evol).mark_line(point=True).encode(
        x="Fecha:T",
        y=alt.Y("Monto Neto:Q", axis=alt.Axis(format="~s")),
        color="Cluster:N",
        tooltip=["Año", "MesNum", "Cluster", "Monto Neto"]
    )

    st.altair_chart(chart, width="stretch")

# PÁGINA: COMPARATIVA ABC

def pagina_comparativa(df_cluster, pareto):
    st.title("📊 Comparativa Año vs Año Anterior por Cluster ABC")

    if df_cluster.empty:
        st.warning("No hay datos para los filtros seleccionados.")
        return

    anios = sorted(df_cluster["Año"].unique())
    anio_sel = st.multiselect("Años", anios, default=anios[-2:] if len(anios) >= 2 else anios)

    df_comp = df_cluster[df_cluster["Año"].isin(anio_sel)]

    if df_comp.empty:
        st.warning("No hay datos para los años seleccionados.")
        return

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

# PÁGINA: HEATMAP ABC

def pagina_heatmap(df_cluster, pareto):
    import pandas as pd

    st.title("🔥 Heatmap Vendedor × Cluster ABC")

    if df_cluster.empty:
        st.warning("No hay datos para los filtros seleccionados.")
        return

    heat = (
        df_cluster.groupby(["Vendedor", "Cluster"])["Monto Neto"]
        .sum()
        .reset_index()
    )

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
        color=alt.Color("Monto Neto:Q", scale=alt.Scale(scheme="reds")),
        tooltip=["Vendedor", "Cluster", "Monto Neto"]
    )

    st.altair_chart(chart, width="stretch")

# PÁGINA: RIESGO COMERCIAL

def pagina_riesgo(df_cluster, pareto):
    st.title("⚠️ Matriz de Riesgo Comercial")

    if df_cluster.empty:
        st.warning("No hay datos para los filtros seleccionados.")
        return

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

# MAIN

def main():
    header()

    df_raw = cargar_datos()
    df = preparar_dataframe(df_raw)

    df_filtrado, pareto, df_cluster = aplicar_filtros(df)

    tabs = st.tabs([
        "Dashboard Comercial",
        "Pareto ABC",
        "Evolución ABC",
        "Comparativa ABC",
        "Heatmap ABC",
        "Riesgo Comercial"
    ])

    with tabs[0]:
        pagina_dashboard(df_filtrado)

    with tabs[1]:
        pagina_pareto(df_filtrado, pareto)

    with tabs[2]:
        pagina_evolucion(df_cluster, pareto)

    with tabs[3]:
        pagina_comparativa(df_cluster, pareto)

    with tabs[4]:
        pagina_heatmap(df_cluster, pareto)

    with tabs[5]:
        pagina_riesgo(df_cluster, pareto)

if __name__ == "__main__":
    main()
