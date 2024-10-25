from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/get_postcode', methods=['POST'])
def get_postcode():
    data = request.get_json()
    lat = data['latitude']
    lon = data['longitude']
    
    url = f"https://api.postcodes.io/postcodes?lat={lat}&lon={lon}"
    response = requests.get(url)
    if response.status_code == 200:
        result = response.json()
        if result['status'] == 200 and result['result']:
            postcode = result['result'][0]['postcode']
            return jsonify({"postcode": postcode}), 200
        else:
            return jsonify({"error": "No se encontró código postal para estas coordenadas"}), 404
    else:
        return jsonify({"error": "Error al consultar la API"}), response.status_code

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
