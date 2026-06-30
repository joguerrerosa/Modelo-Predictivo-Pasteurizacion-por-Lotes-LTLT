import sqlite3
import pandas as pd
import os

DB_FILE = "pasteurizadora.db"

# --- EL TRUCO ESTÁ AQUÍ ---
# Detecta la carpeta donde está guardado este archivo .py
DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
# Une esa carpeta con el nombre del archivo CSV para crear una ruta absoluta
CSV_FILE = os.path.join(DIRECTORIO_ACTUAL, "reporte_historico.csv")
# ---------------------------

def exportar_base_datos_a_csv():
    if not os.path.exists(DB_FILE):
        print(f"❌ No se encontró la base de datos '{DB_FILE}'.")
        print("Asegúrate de que 'servidor_ia.py' haya corrido y guardado datos primero.")
        return

    try:
        print("🔌 Conectando a la base de datos para la extracción...")
        conexion = sqlite3.connect(DB_FILE)
        
        # Leemos todo el histórico usando Pandas desde la tabla de telemetría
        df = pd.read_sql_query("SELECT * FROM telemetria", conexion)
        conexion.close()
        
        if df.empty:
            print("⚠ La base de datos está vacía. No hay nada que exportar.")
            return
            
        # Si la base de datos se leyó con la columna 'id', la formateamos de forma segura
        if len(df.columns) == 8:
            df.columns = ["ID", "Timestamp (Unix)", "Temp (°C)", "Presión (kPa)", "Caudal (L/h)", "Estado Sensor", "Predicción IA", "Riesgo (%)"]
        
        # Convertimos a CSV usando utf-8-sig para compatibilidad nativa con Excel
        df.to_csv(CSV_FILE, index=False, encoding="utf-8-sig")
        
        print(f"|---------------------------------------------------------|")
        print(f"| 🎉 ¡EXPORTACIÓN EXITOSA!                                |")
        print(f"| Archivo generado en: '{CSV_FILE}'                       |")
        print(f"| Total de filas exportadas: {len(df)} registros.          |")
        print(f"| Ya puedes abrir este archivo directamente en Excel.     |")
        print(f"|---------------------------------------------------------|")

    except Exception as e:
        print(f"❌ Ocurrió un error al error al exportar: {e}")

if __name__ == "__main__":
    exportar_base_datos_a_csv()