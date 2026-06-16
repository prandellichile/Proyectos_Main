import streamlit as st
import pandas as pd

def render(df):

    st.title("📊 Dashboard Comercial")

    # ---------------------------------------------------------
    # PROCESAMIENTO DE FECHAS
    # ---------------------------------------------------------
    df = df.copy()
    df["Fecha Docto"] = pd.to_datetime(df["Fecha Docto"], errors="coerce")
    df = df[df["Fecha Docto"].notna()]
    df["Año"] = df["Fecha Docto"].dt.year
    df["MesNum"] = df["Fecha Docto"].dt.month

    meses_es = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
                "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
    df["MesNombre"] = df["MesNum"].apply(lambda x: meses_es[x - 1])

    # ---------------------------------------------------------
    # FILTROS
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

    # ---------------------------------------------------------
    # KPIs
    # ---------------------------------------------------------
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
    # VENTAS POR VENDEDOR (ORDENADO)
    # ---------------------------------------------------------
    st.subheader("📈 Ventas por Vendedor (por Año)")

    ventas_vendedor = df_filtrado.groupby(["Año", "Vendedor"])["Monto Neto"].sum().reset_index()

    # Ordenar vendedores por ventas del año actual
    pivot_ventas = (
        ventas_vendedor
        .pivot(index="Vendedor", columns="Año", values="Monto Neto")
        .fillna(0)
        .sort_values(by=actual, ascending=False)
    )

    st.dataframe(pivot_ventas.style.format("${:,.0f}"))

    # ---------------------------------------------------------
    # TOP N CLIENTES (ORDENADO)
    # ---------------------------------------------------------
    st.subheader(f"🏢 Top {top_n} Clientes")

    top_clientes = (
        df_filtrado.groupby("Razon Social")["Monto Neto"]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
    )

    st.bar_chart(top_clientes.sort_values(ascending=False))

    # ---------------------------------------------------------
    # EVOLUCIÓN MENSUAL (NO SE ORDENA)
    # ---------------------------------------------------------
    st.subheader("📆 Evolución Mensual de Ventas")

    evolucion = df_filtrado.groupby(["Año", "MesNum"])["Monto Neto"].sum().reset_index()
    evolucion["FechaEje"] = pd.to_datetime(evolucion["Año"].astype(str) + "-" + evolucion["MesNum"].astype(str) + "-01")
    evolucion = evolucion.sort_values("FechaEje")

    if len(anio_sel) == 1:
        evolucion["Periodo"] = evolucion["MesNum"].apply(lambda x: meses_es[x - 1])
    else:
        evolucion["Periodo"] = evolucion["MesNum"].apply(lambda x: meses_es[x - 1]) + " " + evolucion["Año"].astype(str)

    st.line_chart(evolucion.set_index("FechaEje")["Monto Neto"])

    if not evolucion.empty:
        mes_pico = evolucion.loc[evolucion["Monto Neto"].idxmax()]
        st.success(f"📈 Mayor venta: {mes_pico['Periodo']} → ${mes_pico['Monto Neto']:,.0f}")

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
