import json
import threading
import paho.mqtt.client as mqtt
from flask import Flask, render_template, jsonify

# --- CONFIGURACIÓN DE RED ---
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC_PROCESADO = "industria/pasteurizadora/dashboard"

app = Flask(__name__)

# Variable global en memoria para almacenar el último paquete que llegue de la IA
ULTIMO_DATO_IA = {
    "temperatura": 64.0,
    "presion_diferencial": 20.0,
    "caudal": 1500.0,
    "diagnostico_ia": "Esperando sincronización con Servidor IA...",
    "riesgo_falla": 0.0,
    "hora": "00:00:00"
}

# -------------------------------------------------------------
# TUS FUNCIONES DE CONTROL DE LÍMITES (Manteniendo tu estructura)
# -------------------------------------------------------------
def revisar_temperatura(valor):
    if valor > 85: nivel = "CRITICA"
    elif valor > 75: nivel = "ADVERTENCIA"
    else: nivel = "NORMAL"
    return {"variable": "Temperatura", "valor": valor, "unidad": "°C", "nivel": nivel}

def revisar_presion(valor):
    # Ajustado de 'bar' a 'kPa' para acoplarse al sensor IoT congelado (1 kPa ≈ 0.01 bar)
    if valor > 30.0: nivel = "CRITICA"
    elif valor > 25.0: nivel = "ADVERTENCIA"
    else: nivel = "NORMAL"
    return {"variable": "Presión", "valor": valor, "unidad": "kPa", "nivel": nivel}

def revisar_caudal(valor):
    # Ajustado a los rangos del sensor IoT congelado (L/h)
    if valor > 2000.0: nivel = "CRITICA"
    elif valor > 1700.0: nivel = "ADVERTENCIA"
    else: nivel = "NORMAL"
    return {"variable": "Caudal", "valor": valor, "unidad": "L/h", "nivel": nivel}

# -------------------------------------------------------------
# HILO DE SEGUNDO PLANO: ESCUCHADOR MQTT
# -------------------------------------------------------------
def on_message(client, userdata, msg):
    global ULTIMO_DATO_IA
    try:
        # 1. Recibir el JSON enriquecido por el Servidor IA
        payload = json.loads(msg.payload.decode())
        
        # 2. Extraer la hora exacta del sistema
        from datetime import datetime
        hora_actual = datetime.fromtimestamp(payload.get("timestamp")).strftime("%H:%M:%S")
        
        # 3. Guardar en la variable global compartida
        ULTIMO_DATO_IA = {
            "temperatura": payload["temperatura"],
            "presion_diferencial": payload["presion_diferencial"],
            "caudal": payload["caudal"],
            "diagnostico_ia": payload["diagnostico_ia"],
            "riesgo_falla": payload["riesgo_falla"],
            "hora": hora_actual
        }
    except Exception as e:
        print(f"[ERROR Flask-MQTT]: {e}")

def iniciar_mqtt():
    cliente = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    cliente.on_message = on_message
    cliente.connect(MQTT_BROKER, MQTT_PORT, 60)
    cliente.subscribe(MQTT_TOPIC_PROCESADO)
    cliente.loop_forever()

# Arrancar el escuchador MQTT en un hilo paralelo para que no bloquee a Flask
threading.Thread(target=iniciar_mqtt, daemon=True).start()


# -------------------------------------------------------------
# RUTAS DE FLASK ACTUALIZADAS
# -------------------------------------------------------------

@app.route("/")
def pagina_principal():
    return render_template("index.html")

@app.route("/datos")
def entregar_datos():
    # En lugar de simular con random, usamos los datos en vivo capturados por MQTT
    alarma_temp = revisar_temperatura(ULTIMO_DATO_IA["temperatura"])
    alarma_presion = revisar_presion(ULTIMO_DATO_IA["presion_diferencial"])
    alarma_caudal = revisar_caudal(ULTIMO_DATO_IA["caudal"])
    
    # Inyectamos la hora correspondiente
    alarma_temp["hora"] = ULTIMO_DATO_IA["hora"]
    alarma_presion["hora"] = ULTIMO_DATO_IA["hora"]
    alarma_caudal["hora"] = ULTIMO_DATO_IA["hora"]
    
    alarmas = [alarma_temp, alarma_presion, alarma_caudal]
    
    # Conteo de alarmas por nivel
    normales = sum(1 for a in alarmas if a["nivel"] == "NORMAL")
    advertencias = sum(1 for a in alarmas if a["nivel"] == "ADVERTENCIA")
    criticas = sum(1 for a in alarmas if a["nivel"] == "CRITICA")
    
    return jsonify({
        "alarmas": alarmas,
        "resumen": {
            "normales": normales,
            "advertencias": advertencias,
            "criticas": criticas
        },
        # --- NUEVOS CAMPOS: Inyectamos el análisis predictivo de la IA en la API ---
        "diagnostico_ia": ULTIMO_DATO_IA["diagnostico_ia"],
        "riesgo_falla": ULTIMO_DATO_IA["riesgo_falla"]
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)