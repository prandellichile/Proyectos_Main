import pandas as pd
import sqlite3

# ---------------------------
# CARGA DE DATOS
# ---------------------------
def cargar_datos():
    conn = sqlite3.connect(r"D:\Proyectos\almacen_datos.db")
    df = pd.read_sql_query("SELECT * FROM ventas", conn)
    conn.close()
    df.columns = df.columns.str.strip()
    return df

# ---------------------------
# PROCESAMIENTO BASE
# ---------------------------
def preparar_dataframe(df):
    df["Fecha Docto"] = pd.to_datetime(df["Fecha Docto"], errors="coerce")
    df = df[df["Fecha Docto"].notna()]
    df["Año"] = df["Fecha Docto"].dt.year
    df["MesNum"] = df["Fecha Docto"].dt.month

    meses_es = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
                "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
    df["MesNombre"] = df["MesNum"].apply(lambda x: meses_es[x - 1])
    return df

# ---------------------------
# PARETO + CLUSTER ABC
# ---------------------------
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

# ---------------------------
# UNIR CLUSTER AL DATAFRAME
# ---------------------------
def unir_cluster(df_filtrado, pareto):
    return df_filtrado.merge(
        pareto[["Razon Social", "Cluster"]],
        on="Razon Social",
        how="left"
    )