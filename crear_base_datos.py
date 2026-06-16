import pandas as pd
import sqlite3

# Ruta del archivo Excel
ruta_excel = r"D:\Proyectos\Proyectos-main\Facturacion.xlsx"

# Cargar el archivo (ajusta el nombre de la hoja si es necesario)
df = pd.read_excel(ruta_excel, sheet_name=0)

# Crear conexión a la base de datos
ruta_db = r"D:\Proyectos\almacen_datos.db"
conn = sqlite3.connect(ruta_db)

# Guardar los datos en una tabla llamada 'ventas'
df.to_sql("ventas", conn, if_exists="replace", index=False)

conn.close()
print("✅ Base de datos creada exitosamente.")