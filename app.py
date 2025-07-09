from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from geospatial import process_geospatial_data
import pickle
import numpy as np
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Replace with a secure random value

# Load model
with open('model/malaria_model.pkl', 'rb') as f:
    malaria_model = pickle.load(f)

# ---------- MAIL CONFIGURATION ----------
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_USERNAME='chinazaconfidence22@gmail.com',         # <-- Replace this
    MAIL_PASSWORD='czxkuaueuztqufgs'             # <-- Replace this (App password from Gmail)
)
mail = Mail(app)
serializer = URLSafeTimedSerializer(app.secret_key)

# ---------- HELPER FUNCTIONS ----------

def get_user_by_email(email):
    conn = sqlite3.connect('instance/vectorvigil.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()
    return user

def send_reset_email(email, reset_url):
    msg = Message("Password Reset for VectorVigil",
                  sender=app.config['MAIL_USERNAME'],
                  recipients=[email])
    msg.body = f"""Hi,

You requested a password reset. Click the link below to reset your password:

{reset_url}

If you didn't request this, please ignore this message.
"""
    mail.send(msg)

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

# ---------- FORGOT PASSWORD ROUTE ----------

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = get_user_by_email(email)
        if user:
            token = serializer.dumps(email, salt='reset-password')
            reset_url = url_for('reset_password', token=token, _external=True)
            send_reset_email(email, reset_url)
            return "A reset link has been sent to your email."
        return "No account with that email."
    return render_template('forgot_password.html')

# (You will later define /reset-password/<token> route)

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='reset-password', max_age=3600)  # Token expires in 1 hour
    except Exception:
        return "Invalid or expired reset link."

    if request.method == 'POST':
        new_password = request.form['password']
        hashed_password = generate_password_hash(new_password)

        conn = sqlite3.connect('instance/vectorvigil.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET password = ? WHERE email = ?', (hashed_password, email))
        conn.commit()
        conn.close()
        return redirect(url_for('login'))

    return render_template('reset_password.html', token=token)


# ---------- MAIN APP ROUTES ----------

def label_risk_level(prediction):
    if prediction == 0:
        return "Low"
    elif prediction == 2:
        return "Medium"
    elif prediction == 1:
        return "High"
    else:
        return "Unknown"

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

    if not (4.0 <= latitude <= 14.0 and 3.0 <= longitude <= 15.0):
        return jsonify({"error": "Location must be within Nigeria."}), 400

    features = np.array([[rainfall, temperature, humidity]])
    prediction = malaria_model.predict(features)[0]
    risk_label = label_risk_level(prediction)

    geo_info = process_geospatial_data(latitude, longitude)
    region = geo_info.get("region", "Unknown")
    risk_zone = geo_info.get("risk_zone", "Unknown")

    conn = sqlite3.connect('instance/vectorvigil.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO predictions (rainfall, temperature, humidity, latitude, longitude, prediction, risk_level)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (rainfall, temperature, humidity, latitude, longitude, int(prediction), risk_label))
    conn.commit()
    conn.close()

    return jsonify({
        "risk": int(prediction),
        "risk_level": risk_label,
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
        LIMIT 1
    ''')
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(rows)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
