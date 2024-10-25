from flask import Flask, request, jsonify
import pandas as pd
import psycopg2
import time
import requests
from datetime import datetime

app = Flask(__name__)

def create_connection():
    while True:
        try:
            conn = psycopg2.connect(
                host="pruebatec_db_1",
                database="postcode_db",
                user="test",
                password="test"
            )
            return conn
        except psycopg2.OperationalError:
            print("Base de datos no lista, esperando un momento...")
            time.sleep(5)

# Función para crear un log en la tabla `log`
def crear_log(cur, tipo_log, detalle):
    fecha_creacion = datetime.now()
    cur.execute(
        "INSERT INTO log (tipo_log, detalle, fecha_creacion) VALUES (%s, %s, %s) RETURNING id_log",
        (tipo_log, detalle, fecha_creacion)
    )
    return cur.fetchone()[0]  # Retorna el id_log del nuevo registro de log

# Función para obtener el ID de ejecución
def obtener_id_ejecucion(cur):
    cur.execute("SELECT COALESCE(MAX(ejecucion), 0) + 1 FROM coordenadas")
    return cur.fetchone()[0]

# Endpoint para recibir el archivo CSV
@app.route('/upload', methods=['POST'])
def upload_csv():
    file = request.files['file']
    
    # Leer el archivo CSV, especificando el delimitador como '|'
    df = pd.read_csv(file, delimiter='|', quotechar="'", header=0, names=['lat', 'lon'], dtype=str)
    df = df.where(pd.notnull(df), None)  # Reemplaza los NaN con None
    
    # Limpiar datos: quitar comillas y reemplazar ',' por '.'
    df['lat'] = df['lat'].str.replace("'", "").str.replace(",", ".")
    df['lon'] = df['lon'].str.replace("'", "").str.replace(",", ".")
    
    conn = create_connection()
    try:
        with conn.cursor() as cur:
            ejecucion_id = obtener_id_ejecucion(cur)  # Obtener ID de ejecución para esta carga
            
            for index, row in df.iterrows():
                lat = row.get('lat')
                lon = row.get('lon')
                
                # Validar coordenadas y generar log si están incorrectas
                if lat is None or lon is None or lat == "0" or lon == "0":
                    detalle = f"Datos inválidos en CSV en el índice {index}: {row}"
                    id_log = crear_log(cur, "Error", detalle)
                    cur.execute("INSERT INTO coordenadas (latitude, longitude, postcode, id_log, ejecucion) VALUES (%s, %s, null, %s, %s)", (lat, lon, id_log, ejecucion_id))
                    conn.commit()
                    continue

                try:
                    # Llamar al servicio externo para obtener el código postal
                    response = requests.post('http://microservice2:5000/get_postcode', json={'latitude': lat, 'longitude': lon})
                    
                    if response.status_code == 200:
                        data = response.json()
                        if 'postcode' in data:
                            # Log de éxito y almacenar coordenada con código postal
                            postcode = data['postcode']
                            id_log = crear_log(cur, "Info", f"Código postal encontrado para ({lat}, {lon})")
                            cur.execute("INSERT INTO coordenadas (latitude, longitude, postcode, id_log, ejecucion) VALUES (%s, %s, %s, %s, %s)", (lat, lon, postcode, id_log, ejecucion_id))
                        else:
                            # Log de error cuando no hay código postal
                            id_log = crear_log(cur, "Error", f"No se encontró código postal para ({lat}, {lon})")
                            cur.execute("INSERT INTO coordenadas (latitude, longitude, postcode, id_log, ejecucion) VALUES (%s, %s, null, %s, %s)", (lat, lon, id_log, ejecucion_id))
                    else:
                        # Log de error cuando el servicio no responde
                        id_log = crear_log(cur, "Error", f"Servicio no responde para coordenadas ({lat}, {lon})")
                        cur.execute("INSERT INTO coordenadas (latitude, longitude, postcode, id_log, ejecucion) VALUES (%s, %s, null, %s, %s)", (lat, lon, id_log, ejecucion_id))

                    conn.commit()

                except Exception as e:
                    # Log de excepción si ocurre un error con la llamada al servicio
                    detalle = f"Error en el servicio para coordenadas ({lat}, {lon}): {e}"
                    id_log = crear_log(cur, "Error", detalle)
                    cur.execute("INSERT INTO coordenadas (latitude, longitude, postcode, id_log, ejecucion) VALUES (%s, %s, null, %s, %s)", (lat, lon, id_log, ejecucion_id))
                    conn.commit()

    finally:
        conn.close()  # Cerrar la conexión a la base de datos

    return jsonify({"message": "Datos procesados"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
