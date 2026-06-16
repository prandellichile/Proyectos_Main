import streamlit as st
from utils import cargar_datos, preparar_dataframe

st.set_page_config(page_title="Workteen Analytics", layout="wide")

# -----------------------------
# MENÚ CORPORATIVO
# -----------------------------
st.sidebar.image("https://i.imgur.com/8QZQZ4R.png", width=180)  # Logo Workteen (puedo generar uno si quieres)

st.sidebar.markdown("## 📊 Workteen Analytics Suite")

menu = st.sidebar.radio(
    "Navegación",
    [
        "Dashboard Comercial",
        "Pareto ABC",
        "Evolución ABC",
        "Comparativa ABC",
        "Heatmap ABC",
        "Riesgo Comercial"
    ]
)

# -----------------------------
# CARGA DE DATOS GLOBAL
# -----------------------------
df = preparar_dataframe(cargar_datos())

# -----------------------------
# RUTEO A PÁGINAS
# -----------------------------
if menu == "Dashboard Comercial":
    import dashboard_comercial as page
    page.render(df)

elif menu == "Pareto ABC":
    import pareto_abc as page
    page.render(df)

elif menu == "Evolución ABC":
    import evolucion_abc as page
    page.render(df)

elif menu == "Comparativa ABC":
    import comparativa_abc as page
    page.render(df)

elif menu == "Heatmap ABC":
    import heatmap_abc as page
    page.render(df)

elif menu == "Riesgo Comercial":
    import Riesgo_Comercial as page
    page.render(df)