import streamlit as st
import pandas as pd
import sqlite3
import altair as alt

# ---------------------------------------------------------
# CONFIGURACIÓN GENERAL
# ---------------------------------------------------------
st.set_page_config(page_title="Dashboard Comercial", layout="wide")
st.title("📊 Dashboard Comercial con Comparativas, Pareto y Clustering ABC")

# ---------------------------------------------------------
# CARGA DE DATOS
# ---------------------------------------------------------
@st.cache_data
def cargar_datos():
    conn = sqlite3.connect(r"D:\Proyectos\almacen_datos.db")
    df = pd.read_sql_query("SELECT * FROM ventas", conn)
    conn.close()
    return df

df = cargar_datos()
df.columns = df.columns.str.strip()

# Validaciones
required_cols = ["Monto Neto", "Razon Social", "Fecha Docto"]
if not all(col in df.columns for col in required_cols):
    st.error(f"❌ Faltan columnas requeridas: {', '.join([c for c in required_cols if c not in df.columns])}")
    st.stop()

# Procesar fecha
df["Fecha Docto"] = pd.to_datetime(df["Fecha Docto"], errors="coerce")
df = df[df["Fecha Docto"].notna()]
df["Año"] = df["Fecha Docto"].dt.year
df["MesNum"] = df["Fecha Docto"].dt.month

meses_es = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
            "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
df["MesNombre"] = df["MesNum"].apply(lambda x: meses_es[x - 1])

# ---------------------------------------------------------
# SIDEBAR — FILTROS
# ---------------------------------------------------------
st.sidebar.header("🔎 Filtros")

vendedores = df["Vendedor"].dropna().unique()
clientes = df["Razon Social"].dropna().unique()
anios = sorted(df["Año"].dropna().unique())
meses_unicos = df["MesNombre"].dropna().unique()

vendedor_sel = st.sidebar.multiselect("Vendedor", vendedores, default=list(vendedores))
cliente_sel = st.sidebar.multiselect("Razon Social", clientes, default=list(clientes))
anio_sel = st.sidebar.multiselect("Año", anios, default=anios)
mes_sel = st.sidebar.multiselect("Mes", meses_unicos, default=list(meses_unicos))

# Filtro cluster (se activa luego del Pareto)
clusters_disponibles = ["A", "B", "C"]
cluster_sel = st.sidebar.multiselect("Cluster ABC", clusters_disponibles, default=clusters_disponibles)

top_n = st.sidebar.slider("📌 Mostrar Top N Clientes", min_value=3, max_value=30, value=10)

# ---------------------------------------------------------
# APLICAR FILTROS
# ---------------------------------------------------------
df_filtrado = df[
    df["Vendedor"].isin(vendedor_sel) &
    df["Razon Social"].isin(cliente_sel) &
    df["Año"].isin(anio_sel) &
    df["MesNombre"].isin(mes_sel)
]

# ---------------------------------------------------------
# COMPARATIVAS AÑO VS AÑO ANTERIOR
# ---------------------------------------------------------
st.markdown("### 📊 Comparativas Año Actual vs Año Anterior")

años_ordenados = sorted(anio_sel)
if len(años_ordenados) >= 2:
    actual, anterior = años_ordenados[-1], años_ordenados[-2]
    df_actual = df_filtrado[df_filtrado["Año"] == actual]
    df_anterior = df_filtrado[df_filtrado["Año"] == anterior]

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
    ventas_actual = df_filtrado["Monto Neto"].sum()
    clientes_actual = df_filtrado["Razon Social"].nunique()
    ticket_actual = ventas_actual / clientes_actual if clientes_actual else 0
    delta_pct = delta_cli_pct = delta_ticket_pct = None

# KPIs
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

# ---------------------------------------------------------
# PARETO + CLUSTER ABC
# ---------------------------------------------------------
st.subheader("📊 Análisis Pareto de Clientes (ABC)")

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

# Gráfico Pareto
bars = alt.Chart(pareto).mark_bar().encode(
    x=alt.X("Razon Social:N", sort=None),
    y="Monto Neto:Q",
    color=alt.Color("Cluster:N", scale=alt.Scale(domain=["A","B","C"], range=["#2ecc71","#f1c40f","#e74c3c"]))
)

line = alt.Chart(pareto).mark_line(color="#3498db", strokeWidth=3).encode(
    x="Razon Social:N",
    y="Porcentaje Acumulado:Q"
)

points = alt.Chart(pareto).mark_circle(size=60, color="#2980b9").encode(
    x="Razon Social:N",
    y="Porcentaje Acumulado:Q"
)

st.altair_chart(alt.layer(bars, line, points).resolve_scale(y="independent"), use_container_width=True)

# Tabla Pareto
st.dataframe(
    pareto.style.format({
        "Monto Neto": "${:,.0f}",
        "Porcentaje": "{:.2%}",
        "Porcentaje Acumulado": "{:.1f}%"
    })
)

# ---------------------------------------------------------
# INTEGRAR CLUSTER AL DATAFRAME FILTRADO
# ---------------------------------------------------------
df_cluster = df_filtrado.merge(
    pareto[["Razon Social", "Cluster"]],
    on="Razon Social",
    how="left"
)

df_cluster = df_cluster[df_cluster["Cluster"].isin(cluster_sel)]

# ---------------------------------------------------------
# EVOLUCIÓN MENSUAL POR CLUSTER
# ---------------------------------------------------------
st.subheader("📆 Evolución Mensual por Cluster ABC")

evol_cluster = (
    df_cluster.groupby(["Año", "MesNum", "Cluster"])["Monto Neto"]
    .sum()
    .reset_index()
)

evol_cluster["FechaEje"] = pd.to_datetime(
    evol_cluster["Año"].astype(str) + "-" + evol_cluster["MesNum"].astype(str) + "-01"
)

evol_cluster = evol_cluster.sort_values("FechaEje")

evol_chart = alt.Chart(evol_cluster).mark_line(point=True).encode(
    x=alt.X("FechaEje:T", title="Periodo"),
    y=alt.Y("Monto Neto:Q", title="Ventas"),
    color=alt.Color("Cluster:N", scale=alt.Scale(domain=["A","B","C"], range=["#2ecc71","#f1c40f","#e74c3c"])),
    tooltip=["Año", "MesNum", "Cluster", "Monto Neto"]
)

st.altair_chart(evol_chart, use_container_width=True)

# ---------------------------------------------------------
# COMPARATIVA AÑO VS AÑO ANTERIOR POR CLUSTER
# ---------------------------------------------------------
st.subheader("📊 Comparativa Año Actual vs Anterior por Cluster ABC")

if len(años_ordenados) >= 2:
    df_comp_cluster = df_cluster[df_cluster["Año"].isin([anterior, actual])]

    comp_cluster = (
        df_comp_cluster.groupby(["Año", "Cluster"])["Monto Neto"]
        .sum()
        .reset_index()
    )

    comp_chart = alt.Chart(comp_cluster).mark_bar().encode(
        x="Cluster:N",
        y="Monto Neto:Q",
        color="Año:N",
        column="Año:N"
    )

    st.altair_chart(comp_chart, use_container_width=True)

# ---------------------------------------------------------
# HEATMAP VENDEDOR × CLUSTER
# ---------------------------------------------------------
st.subheader("🔥 Heatmap Vendedor × Cluster ABC")

heat = (
    df_cluster.groupby(["Vendedor", "Cluster"])["Monto Neto"]
    .sum()
    .reset_index()
)

heat_chart = alt.Chart(heat).mark_rect().encode(
    x="Cluster:N",
    y="Vendedor:N",
    color=alt.Color("Monto Neto:Q", scale=alt.Scale(scheme="reds")),
    tooltip=["Vendedor", "Cluster", "Monto Neto"]
)

st.altair_chart(heat_chart, use_container_width=True)

# ---------------------------------------------------------
# MATRIZ DE RIESGO COMERCIAL
# ---------------------------------------------------------
st.subheader("⚠️ Matriz de Riesgo Comercial por Dependencia en Clientes A")

ventas_totales = df_cluster["Monto Neto"].sum()
ventas_A = df_cluster[df_cluster["Cluster"] == "A"]["Monto Neto"].sum()
ventas_B = df_cluster[df_cluster["Cluster"] == "B"]["Monto Neto"].sum()
ventas_C = df_cluster[df_cluster["Cluster"] == "C"]["Monto Neto"].sum()

dep_A_pct = (ventas_A / ventas_totales * 100) if ventas_totales else 0

col_r1, col_r2 = st.columns(2)

col_r1.metric("Dependencia en Clientes A", f"{dep_A_pct:.1f}%")
col_r2.markdown(
    f"- Ventas A: ${ventas_A:,.0f}\n"
    f"- Ventas B: ${ventas_B:,.0f}\n"
    f"- Ventas C: ${ventas_C:,.0f}"
)

if dep_A_pct >= 80:
    st.error("🔴 Riesgo Alto: Fuerte dependencia en pocos clientes A.")
elif dep_A_pct >= 60:
    st.warning("🟠 Riesgo Medio: Alta concentración en clientes A.")
else:
    st.success("🟢 Riesgo Bajo: Distribución equilibrada entre clusters.")

# ---------------------------------------------------------
# DETALLE Y DESCARGA
# ---------------------------------------------------------
st.subheader("📄 Detalle de Transacciones")
st.dataframe(df_filtrado)

st.download_button(
    label="📥 Descargar datos filtrados",
    data=df_filtrado.to_csv(index=False),
    file_name="reporte_filtrado.csv",
    mime="text/csv"
)