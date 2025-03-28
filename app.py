from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import joblib
import numpy as np
from geopy.distance import geodesic
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root1:root1@localhost/risk_auth_iforest_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Load trained Isolation Forest model and preprocessing objects
iso_forest = joblib.load("isolation_forest_model.pkl")
scaler = joblib.load("scaler.pkl")
label_encoders = joblib.load("label_encoders.pkl")
ip_frequencies = joblib.load("ip_frequencies.pkl")

# Define the database model
class LoginAttempt(db.Model):
    __tablename__ = "login_attempts"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userID = db.Column(db.String(255), nullable=False)
    IPaddress = db.Column(db.String(50), nullable=False)
    Latitude = db.Column(db.Float, nullable=False, default=0.0)
    Longitude = db.Column(db.Float, nullable=False, default=0.0)
    Timezone = db.Column(db.String(50))
    DeviceInfo = db.Column(db.String(255), default='Unknown')
    TypingSpeed = db.Column(db.Float, default=0.0)
    MouseSpeed = db.Column(db.Float, default=0.0)
    geo_velocity = db.Column(db.Float, default=0.0)
    LoginTime = db.Column(db.DateTime, default=datetime.utcnow)

# Function to calculate geo-velocity
def calculate_geo_velocity(prev_lat, prev_lon, prev_time, curr_lat, curr_lon, curr_time):
    try:
        if prev_lat is None or prev_lon is None or prev_time is None:
            return 0.0
        prev_location = (prev_lat, prev_lon)
        current_location = (curr_lat, curr_lon)
        time_diff = (curr_time - prev_time).total_seconds() / 3600.0  # Convert to hours
        if time_diff <= 0:
            return 0.0
        distance = geodesic(prev_location, current_location).km
        return distance / time_diff
    except Exception as e:
        print(f"Error calculating geo-velocity: {e}")
        return 0.0

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        userID = data.get("userID")
        IPaddress = data.get("IPaddress")
        Latitude = float(data.get("Latitude", 0.0))
        Longitude = float(data.get("Longitude", 0.0))
        Timezone = data.get("Timezone", "Unknown")
        DeviceInfo = data.get("DeviceInfo", "Unknown")
        TypingSpeed = float(data.get("TypingSpeed", 0.0))
        MouseSpeed = float(data.get("MouseSpeed", 0.0))
        LoginTime = datetime.utcnow()
        login_hour = LoginTime.hour

        prev_attempt = LoginAttempt.query.filter_by(userID=userID).order_by(LoginAttempt.LoginTime.desc()).first()
        changed_features = []
        error_score = 0

        if prev_attempt:
            if IPaddress != prev_attempt.IPaddress:
                error_score += 2
                changed_features.append("IP Address")
            if DeviceInfo != prev_attempt.DeviceInfo:
                error_score += 3
                changed_features.append("Device")
            if Timezone != prev_attempt.Timezone:
                error_score += 3
                changed_features.append("Timezone")
            if (Latitude, Longitude) != (prev_attempt.Latitude, prev_attempt.Longitude):
                error_score += 5
                changed_features.append("Location")
        
        geo_velocity = calculate_geo_velocity(
            prev_attempt.Latitude if prev_attempt else None,
            prev_attempt.Longitude if prev_attempt else None,
            prev_attempt.LoginTime if prev_attempt else None,
            Latitude, Longitude, LoginTime
        )

        # Block if geo-velocity exceeds 1000 km/h
        if geo_velocity > 1000:
            return jsonify({
                "isolation_forest_risk_score": "N/A",
                "feature_change_risk_score": error_score,
                "changed_features": changed_features,
                "total_risk_score": "Blocked due to extreme geo-velocity",
                "geo_velocity": geo_velocity,
                "risk_decision": "Block"
            })

        ip_freq = ip_frequencies.get(IPaddress, 0.0001)

        if "Timezone" in label_encoders and Timezone in label_encoders["Timezone"].classes_:
            Timezone = label_encoders["Timezone"].transform([Timezone])[0]
        else:
            Timezone = label_encoders["Timezone"].transform(["Unknown"])[0]

        if "DeviceInfo" in label_encoders and DeviceInfo in label_encoders["DeviceInfo"].classes_:
            DeviceInfo = label_encoders["DeviceInfo"].transform([DeviceInfo])[0]
        else:
            DeviceInfo = label_encoders["DeviceInfo"].transform(["Unknown"])[0]

        feature_vector = np.array([[Latitude, Longitude, TypingSpeed, MouseSpeed, geo_velocity, login_hour, ip_freq]])
        feature_vector = scaler.transform(feature_vector)
        risk_score = -iso_forest.decision_function(feature_vector)[0]

        # Always calculate total risk score
        total_risk_score = error_score - risk_score

        if not changed_features:  
            # No changes → Use isolation model thresholds
            if risk_score < -0.12:
                risk_decision = "Allow"
            elif -0.12 <= risk_score <= -0.05:
                risk_decision = "MFA"
            else:
                risk_decision = "Block"
        else:
            # Changes detected → Use total risk score
            if total_risk_score >= 8:
                risk_decision = "Block"
            elif total_risk_score >= 4:
                risk_decision = "MFA"
            else:
                risk_decision = "Allow"

        if risk_decision == "Allow":
            new_attempt = LoginAttempt(
                userID=userID,
                IPaddress=IPaddress,
                Latitude=Latitude,
                Longitude=Longitude,
                Timezone=data.get("Timezone", "Unknown"),
                DeviceInfo=data.get("DeviceInfo", "Unknown"),
                TypingSpeed=TypingSpeed,
                MouseSpeed=MouseSpeed,
                geo_velocity=geo_velocity,
                LoginTime=LoginTime
            )
            db.session.add(new_attempt)
            db.session.commit()

        return jsonify({
            "isolation_forest_risk_score": risk_score,
            "feature_change_risk_score": error_score,
            "changed_features": changed_features,
            "total_risk_score": total_risk_score,  
            "geo_velocity": geo_velocity,
            "risk_decision": risk_decision,
            "total_risk_score": total_risk_score,
            "risk_score": risk_score
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
