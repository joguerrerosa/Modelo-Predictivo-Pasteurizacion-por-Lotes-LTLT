import time
import random
import json
import paho.mqtt.client as mqtt

# --- CONFIGURACIÓN DEL BROKER LOCAL (MOSQUITTO) ---
MQTT_BROKER = "localhost" 
MQTT_PORT = 1883
MQTT_TOPIC = "industria/pasteurizadora/sensores"

def conectar_mqtt():
    """Inicializa y conecta el cliente MQTT local."""
    cliente = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    print(f"Conectando al Broker Mosquitto Local ({MQTT_BROKER})...")
    try:
        cliente.connect(MQTT_BROKER, MQTT_PORT, 60)
        return cliente
    except ConnectionRefusedError:
        print("\n[ERROR] No se pudo conectar a Mosquitto.")
        print("Asegúrate de que el servicio de Mosquitto esté encendido en tu PC.")
        exit(1)

def generar_datos_sensores():
    """Simula datos basados en rangos de Normal, Alerta y Falla."""
    probabilidad = random.random()
    
    if probabilidad < 0.30:
        # --- ESTADO NORMAL (80%) ---
        temperatura = round(random.uniform(63.0, 65.0), 2)          # 64 ± 1 °C
        caudal = round(random.uniform(1300.0, 1700.0), 1)           # 1500 ± 200 L/h
        presion_diferencial = round(random.uniform(15.0, 25.0), 2)  # 20 ± 5 kPa
        estado = "Normal"
        
    elif probabilidad < 0.50:
        # --- ESTADO ALERTA (15%) ---
        variable_desviada = random.choice(["temp", "caudal", "presion"])
        
        temperatura = round(random.uniform(63.0, 65.0), 2)
        caudal = round(random.uniform(1300.0, 1700.0), 1)
        presion_diferencial = round(random.uniform(15.0, 25.0), 2)
        
        if variable_desviada == "temp":
            temperatura = round(random.choice([random.uniform(61.0, 63.0), random.uniform(65.0, 67.0)]), 2)
        elif variable_desviada == "caudal":
            caudal = round(random.choice([random.uniform(1100.0, 1300.0), random.uniform(1700.0, 1900.0)]), 1)
        elif variable_desviada == "presion":
            presion_diferencial = round(random.choice([random.uniform(10.0, 15.0), random.uniform(25.0, 30.0)]), 2)
            
        estado = "Alerta: Desviación de Parámetros"
        
    else:
        # --- ESTADO FALLA CRÍTICA (5%) ---
        variable_critica = random.choice(["temp", "caudal", "presion"])
        
        temperatura = round(random.uniform(63.0, 65.0), 2)
        caudal = round(random.uniform(1300.0, 1700.0), 1)
        presion_diferencial = round(random.uniform(15.0, 25.0), 2)
        
        if variable_critica == "temp":
            temperatura = round(random.choice([random.uniform(55.0, 60.9), random.uniform(67.1, 75.0)]), 2)
            estado = "Falla: Temperatura fuera de límites"
        elif variable_critica == "caudal":
            caudal = round(random.choice([random.uniform(500.0, 999.0), random.uniform(2001.0, 2500.0)]), 1)
            estado = "Falla: Caudal fuera de límites"
        elif variable_critica == "presion":
            presion_diferencial = round(random.choice([random.uniform(0.0, 9.9), random.uniform(30.1, 45.0)]), 2)
            estado = "Falla: Presión fuera de límites"

    payload = {
        "timestamp": time.time(),
        "temperatura": temperatura,
        "presion_diferencial": presion_diferencial,
        "caudal": caudal,
        "estado_operativo": estado
    }
    return payload

def simular_iot():
    cliente = conectar_mqtt()
    cliente.loop_start() 
    
    print("Simulador IoT iniciado. Presiona Ctrl+C para detener.")
    try:
        while True:
            datos = generar_datos_sensores()
            mensaje = json.dumps(datos)
            resultado = cliente.publish(MQTT_TOPIC, mensaje)
            
            if resultado.rc == mqtt.MQTT_ERR_SUCCESS:
                if "Falla" in datos["estado_operativo"]:
                    print(f"[🔴 FALLA ENVIADA] -> {mensaje}")
                elif "Alerta" in datos["estado_operativo"]:
                    print(f"[🟡 ALERTA ENVIADA] -> {mensaje}")
                else:
                    print(f"[🟢 ENVIADO] -> {mensaje}")
            else:
                print("Error de envío al broker local.")
                
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nSimulación detenida por el usuario.")
    finally:
        cliente.loop_stop()
        cliente.disconnect()

if __name__ == "__main__":
    simular_iot()