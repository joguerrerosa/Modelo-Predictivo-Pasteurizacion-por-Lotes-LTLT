import os
import pickle
import json
import sqlite3
import time
import numpy as np
import pandas as pd
import paho.mqtt.client as mqtt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

# --- CONFIGURACIÓN GENERAL ---
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC_ENTRADA = "industria/pasteurizadora/sensores"
MQTT_TOPIC_PROCESADO = "industria/pasteurizadora/dashboard" # <-- CORREGIDO: Añadido canal de salida
MODELO_FILE = "modelo_predictivo.pkl"
DB_FILE = "pasteurizadora.db"

MAPA_ESTADOS = {
    0: "Operación Estable (Verde)", 
    1: "Estado de Alerta Detectado (Amarillo)", 
    2: "Parada de Emergencia: ¡Falla Crítica! (Rojo)"
}

def inicializar_base_datos():
    conexion = sqlite3.connect(DB_FILE)
    cursor = conexion.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS telemetria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL,
            temperatura REAL,
            presion_diferencial REAL,
            caudal REAL,
            estado_sensor TEXT,
            diagnostico_ia TEXT,
            riesgo_falla REAL
        )
    ''')
    conexion.commit()
    conexion.close()
    print(f"[BD] Base de datos '{DB_FILE}' lista.")

def guardar_en_base_datos(datos_tupla):
    try:
        conexion = sqlite3.connect(DB_FILE)
        cursor = conexion.cursor()
        query = '''
            INSERT INTO telemetria 
            (timestamp, temperatura, presion_diferencial, caudal, estado_sensor, diagnostico_ia, riesgo_falla)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        cursor.execute(query, datos_tupla)
        conexion.commit()
        conexion.close()
        print("[BD] ✔️ Archivo guardado en SQLite (.db)")
    except Exception as e:
        print(f"[BD] ❌ Error: {e}")

def comprobar_y_entrenar_modelo():
    if os.path.exists(MODELO_FILE):
        print("[INFO] Modelo predictivo cargado.")
        return
    print("[INFO] Entrenando modelo de Machine Learning...")
    datos = []
    for _ in range(4000):
        datos.append([np.random.uniform(63.0, 65.0), np.random.uniform(15.0, 25.0), np.random.uniform(1300.0, 1700.0), 0])
    for _ in range(1000):
        t = np.random.choice([np.random.uniform(61.0, 63.0), np.random.uniform(65.0, 67.0)])
        p = np.random.choice([np.random.uniform(10.0, 15.0), np.random.uniform(25.0, 30.0)])
        c = np.random.choice([np.random.uniform(1100.0, 1300.0), np.random.uniform(1700.0, 1900.0)])
        datos.append([t, p, c, 1])
    for _ in range(500):
        t = np.random.choice([np.random.uniform(55.0, 60.9), np.random.uniform(67.1, 75.0)])
        p = np.random.choice([np.random.uniform(0.0, 9.9), np.random.uniform(30.1, 40.0)])
        c = np.random.choice([np.random.uniform(500.0, 999.0), np.random.uniform(2001.0, 2500.0)])
        datos.append([t, p, c, 2])
        
    df = pd.DataFrame(datos, columns=['temperatura', 'presion_diferencial', 'caudal', 'label'])
    X = df[['temperatura', 'presion_diferencial', 'caudal']]
    y = df['label']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    modelo = RandomForestClassifier(n_estimators=100, random_state=42)
    modelo.fit(X_train, y_train)
    with open(MODELO_FILE, 'wb') as f:
        pickle.dump(modelo, f)
    print("[OK] Cerebro de IA listo.")

def on_connect(client, userdata, flags, rc, properties=None):
    print(f"Servidor IA escuchando tópico crudo: {MQTT_TOPIC_ENTRADA}")
    client.subscribe(MQTT_TOPIC_ENTRADA)

def on_message(client, userdata, msg):
    try:
        payload_texto = msg.payload.decode()
        datos_diccionario = json.loads(payload_texto)
        
        ts = datos_diccionario["timestamp"]
        temp = datos_diccionario["temperatura"]
        presion = datos_diccionario["presion_diferencial"]
        caudal = datos_diccionario["caudal"]
        estado_sensor = datos_diccionario["estado_operativo"]
        
        # Clasificación con Inteligencia Artificial
        caracteristicas = np.array([[temp, presion, caudal]])
        prediccion_numerica = modelo_ia.predict(caracteristicas)[0]
        estado_predicho = MAPA_ESTADOS[prediccion_numerica]
        
        probabilidades = modelo_ia.predict_proba(caracteristicas)[0]
        probabilidad_falla = float((1 - probabilidades[0]) * 100)
        
        # 1. Almacenar fila histórica inmutable en Base de Datos SQL
        registro_tupla = (ts, temp, presion, caudal, estado_sensor, estado_predicho, round(probabilidad_falla, 2))
        guardar_en_base_datos(registro_tupla)
        
        # 2. CORREGIDO: Empaquetar JSON con IA e inyectarlo de vuelta a Mosquitto para Flask
        paquete_enriquecido = {
            "timestamp": ts,
            "temperatura": temp,
            "presion_diferencial": presion,
            "caudal": caudal,
            "diagnostico_ia": estado_predicho,
            "riesgo_falla": round(probabilidad_falla, 1)
        }
        client.publish(MQTT_TOPIC_PROCESADO, json.dumps(paquete_enriquecido))
        print(f"[🤖 IA PROCESADA Y PUBLICADA] -> Riesgo: {probabilidad_falla:.1f}%")
        
    except Exception as e:
        print(f"Error procesando el flujo de datos: {e}")

if __name__ == "__main__":
    inicializar_base_datos()
    comprobar_y_entrenar_modelo()
    
    with open(MODELO_FILE, 'rb') as archivo:
        modelo_ia = pickle.load(archivo)
        
    cliente = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    cliente.on_connect = on_connect
    cliente.on_message = on_message
    
    cliente.connect(MQTT_BROKER, MQTT_PORT, 60)
    cliente.loop_forever()