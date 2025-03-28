import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import IsolationForest
import joblib
from datetime import datetime
from geopy.distance import geodesic

# Load dataset
df = pd.read_csv("useractivityvariation5.csv")
print(f"✅ Dataset loaded. Shape: {df.shape}")

# Encode categorical features
label_encoders = {}
categorical_cols = ["IPaddress", "Timezone", "DeviceInfo"]
for col in categorical_cols:
    le = LabelEncoder()
    df[col] = le.fit_transform(df[col])
    label_encoders[col] = le
joblib.dump(label_encoders, "label_encoders.pkl")
print("✅ Label encoders saved.")

# Compute frequency of each IP address & add as feature
ip_frequencies = df["IPaddress"].value_counts(normalize=True).to_dict()
df["ip_frequency"] = df["IPaddress"].map(ip_frequencies)
joblib.dump(ip_frequencies, "ip_frequencies.pkl")

# Convert `LoginTime` to datetime
#df["LoginTime"] = pd.to_datetime(df["LoginTime"], format="%d-%m-%Y %H:%M", dayfirst=True, errors="coerce")

df["LoginTime"] = pd.to_datetime(df["LoginTime"], dayfirst=True, errors="coerce")


# Sort by userID and LoginTime for sequential processing
df = df.sort_values(by=["userID", "LoginTime"])
df["prev_latitude"] = df.groupby("userID")["Latitude"].shift(1)
df["prev_longitude"] = df.groupby("userID")["Longitude"].shift(1)
df["prev_login_time"] = df.groupby("userID")["LoginTime"].shift(1)

# Drop NaN values (ensures every entry has a valid previous login)
df.dropna(inplace=True)
if df.empty:
    raise ValueError("Error: The dataset is empty after preprocessing! Check data loading.")

def calculate_speed(row):
    try:
        prev_location = (row["prev_latitude"], row["prev_longitude"])
        current_location = (row["Latitude"], row["Longitude"])
        
        if pd.isnull(row["prev_login_time"]) or pd.isnull(row["LoginTime"]):
            return 0.0
        
        time_diff = (row["LoginTime"] - row["prev_login_time"]).total_seconds() / 3600.0
        distance = geodesic(prev_location, current_location).km
        
        return distance / time_diff if time_diff > 0 else 0.0
    except:
        return 0.0

df["geo_velocity"] = df.apply(calculate_speed, axis=1)
print("✅ Geo-velocity computed.")

# Extract login hour
df["login_hour"] = df["LoginTime"].dt.hour

# Normalize numerical features
numerical_cols = ["Latitude", "Longitude", "TypingSpeed", "MouseSpeed", "geo_velocity", "login_hour", "ip_frequency"]
scaler = MinMaxScaler()
df[numerical_cols] = scaler.fit_transform(df[numerical_cols])
joblib.dump(scaler, "scaler.pkl")
print("✅ Numerical features normalized and scaler saved.")

# Prepare training data
X = df[numerical_cols].values
if X.shape[0] == 0:
    raise ValueError("Error: No training data available after preprocessing!")

# Train Isolation Forest model
iso_forest = IsolationForest(n_estimators=100, contamination=0.14, random_state=42)
iso_forest.fit(X)

# Save the model
joblib.dump(iso_forest, "isolation_forest_model.pkl")
print("✅ Isolation Forest training complete. Model saved successfully!")