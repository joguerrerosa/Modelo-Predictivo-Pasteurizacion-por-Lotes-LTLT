# Modelo-Predictivo-Pasteurización-por-Lotes-LTLT
Sistema predictivo de supervisión industrial en tiempo real enfocado en el proceso de pasteurización de baja temperatura y largo tiempo (LTLT). El proyecto implementa una arquitectura guiada por eventos (MQTT) para capturar telemetría IoT, evaluarla mediante un modelo de Machine Learning y almacenar de forma práctica el histórico operativo.
Parámetros Supervisados
El sistema analiza continuamente tres variables críticas del proceso:
-**Temperatura (°C):** Control del rango óptimo de pasteurización.
-**Caudal de Agitación (L/h):** Monitoreo del flujo constante del producto.
-**Presión Diferencial (kPa):** Indicador de la integridad y rendimiento del sistema.

Arquitectura del Ecosistema

El proyecto está dividido en 4 módulos independientes que trabajan en armonía:
1. **`simulador_iot.py` (Sensor de Telemetría):** Emulador IoT industrial que genera lecturas continuas basadas en una matriz de probabilidad operativa (80% Normal, 15% Alerta, 5% Falla Crítica) y las transmite vía MQTT.
2. **`servidor_ia.py` (Cerebro Predictivo y BD):** Servidor backend que consume los datos crudos, los procesa al vuelo a través de un modelo de clasificación (*Random Forest*) para determinar el porcentaje de riesgo de parada, y archiva cada registro en una base de datos relacional **SQLite**.
3. **`servidor_flask.py` (API & Dashboard):** Servidor web que expone una API REST con los datos en vivo enriquecidos por la IA y gestiona la interfaz gráfica de monitoreo.
4. **`exportador_reportes.py` (Módulo de Analítica):** Script de extracción que convierte el histórico de la base de datos a un formato plano CSV optimizado para su análisis directo en Excel.


Tecnologías Utilizadas
-**Lenguaje:** Python
-**Machine Learning:** Scikit-Learn (Random Forest Classifier), Pandas, NumPy
-**Protocolo de Red:** MQTT (Mosquitto Broker / Paho-MQTT)
-**Web & API:** Flask
-**Base de Datos:** SQLite3
