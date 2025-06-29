from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from geospatial import process_geospatial_data
import pickle
import numpy as np
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Replace with a secure random value

# Load model
with open('model/malaria_model.pkl', 'rb') as f:
    malaria_model = pickle.load(f)


# ---------- USER AUTH ROUTES ----------

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        conn = sqlite3.connect('instance/vectorvigil.db')
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)', (name, email, password))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Email already exists. Try logging in."
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('instance/vectorvigil.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, password FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect(url_for('home'))
        else:
            return "Invalid email or password."
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ---------- MAIN APP ROUTES ----------

@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', user=session['username'])


@app.route('/predict', methods=['POST'])
def predict():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    try:
        rainfall = float(data['rainfall'])
        temperature = float(data['temperature'])
        humidity = float(data['humidity'])
        latitude = float(data['latitude'])
        longitude = float(data['longitude'])
    except (KeyError, ValueError):
        return jsonify({"error": "Invalid input. Please provide rainfall, temperature, humidity, latitude, and longitude."}), 400

    # ✅ Restrict to Nigeria bounds
    if not (4.0 <= latitude <= 14.0 and 3.0 <= longitude <= 15.0):
        return jsonify({"error": "Location must be within Nigeria."}), 400

    # Predict
    features = np.array([[rainfall, temperature, humidity]])
    prediction = malaria_model.predict(features)[0]

    # Optional: classify region using your helper
    geo_info = process_geospatial_data(latitude, longitude)
    region = geo_info.get("region", "Unknown")
    risk_zone = geo_info.get("risk_zone", "Unknown")

    # Save to database (add region/risk_zone later if you extend DB schema)
    conn = sqlite3.connect('instance/vectorvigil.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO predictions (rainfall, temperature, humidity, latitude, longitude, prediction)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (rainfall, temperature, humidity, latitude, longitude, int(prediction)))
    conn.commit()
    conn.close()

    return jsonify({
        "risk": int(prediction),
        "region": region,
        "risk_zone": risk_zone
    })


@app.route('/map-data')
def map_data():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 403

    conn = sqlite3.connect('instance/vectorvigil.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT latitude, longitude, rainfall, prediction
        FROM predictions
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        ORDER BY timestamp DESC
        LIMIT 100
    ''')
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(rows)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
