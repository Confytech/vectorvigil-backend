from flask import Flask, request, jsonify, render_template
from geospatial import process_geospatial_data
import pickle
import numpy as np
import sqlite3

app = Flask(__name__)

# Load model
with open('model/malaria_model.pkl', 'rb') as f:
    malaria_model = pickle.load(f)

# Home route to serve the HTML form
@app.route('/')
def home():
    return render_template('index.html')

# Predict route that also stores data in DB
@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()

    try:
        rainfall = float(data['rainfall'])
        temperature = float(data['temperature'])
        humidity = float(data['humidity'])
        latitude = float(data['latitude'])
        longitude = float(data['longitude'])
    except (KeyError, ValueError):
        return jsonify({"error": "Invalid input. Please provide rainfall, temperature, humidity, latitude, and longitude."}), 400

    # Predict
    features = np.array([[rainfall, temperature, humidity]])
    prediction = malaria_model.predict(features)[0]

    # Save to database
    conn = sqlite3.connect('instance/vectorvigil.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO predictions (rainfall, temperature, humidity, latitude, longitude, prediction)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (rainfall, temperature, humidity, latitude, longitude, int(prediction)))
    conn.commit()
    conn.close()

    return jsonify({"risk": int(prediction)})

# Map data endpoint for Leaflet
@app.route('/map-data')
def map_data():
    conn = sqlite3.connect('instance/vectorvigil.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''
        SELECT latitude, longitude, rainfall, prediction
        FROM predictions
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        ORDER BY timestamp DESC
        LIMIT 100
    ''')
    rows = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(rows)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)

