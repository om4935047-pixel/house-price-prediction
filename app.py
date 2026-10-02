from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "house_prices.csv"
MODEL_PATH = Path(__file__).resolve().parent / "model.joblib"

FEATURES = ["area_sqft", "bedrooms", "bathrooms", "age_years", "location_score", "parking"]

app = Flask(__name__, static_folder=str(ROOT / "frontend"), static_url_path="")
CORS(app)

def train_model():
    df = pd.read_csv(DATA_PATH)
    X = df[FEATURES]
    y = df["price_lakh"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    model = LinearRegression()
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    metrics = {
        "mae": round(float(mean_absolute_error(y_test, pred)), 3),
        "mse": round(float(mean_squared_error(y_test, pred)), 3),
        "rmse": round(float(np.sqrt(mean_squared_error(y_test, pred))), 3),
        "r2": round(float(r2_score(y_test, pred)), 4),
        "train_samples": int(len(X_train)),
        "test_samples": int(len(X_test))
    }
    joblib.dump(model, MODEL_PATH)
    return model, metrics

if MODEL_PATH.exists():
    model = joblib.load(MODEL_PATH)
    _, metrics = train_model()  # retrain so dataset/model always match
    model = joblib.load(MODEL_PATH)
else:
    model, metrics = train_model()

@app.get("/")
def home():
    return send_from_directory(ROOT / "frontend", "index.html")

@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "model": "Linear Regression"})

@app.get("/api/metrics")
def get_metrics():
    return jsonify(metrics)

@app.post("/api/predict")
def predict():
    try:
        data = request.get_json(force=True)
        values = {f: float(data[f]) for f in FEATURES}

        if values["area_sqft"] <= 0:
            return jsonify({"error": "Area must be greater than 0."}), 400
        if not 1 <= values["bedrooms"] <= 10:
            return jsonify({"error": "Bedrooms must be between 1 and 10."}), 400
        if not 1 <= values["bathrooms"] <= 10:
            return jsonify({"error": "Bathrooms must be between 1 and 10."}), 400
        if not 0 <= values["age_years"] <= 150:
            return jsonify({"error": "Age must be between 0 and 150 years."}), 400
        if not 1 <= values["location_score"] <= 10:
            return jsonify({"error": "Location score must be between 1 and 10."}), 400
        if not 0 <= values["parking"] <= 5:
            return jsonify({"error": "Parking spaces must be between 0 and 5."}), 400

        X = pd.DataFrame([values], columns=FEATURES)
        prediction = float(model.predict(X)[0])
        prediction = max(0, prediction)

        return jsonify({
            "predicted_price_lakh": round(prediction, 2),
            "predicted_price_inr": round(prediction * 100000, 0),
            "currency": "INR",
            "unit": "lakh"
        })
    except KeyError as e:
        return jsonify({"error": f"Missing field: {e.args[0]}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.post("/api/retrain")
def retrain():
    global model, metrics
    model, metrics = train_model()
    return jsonify({"message": "Model retrained successfully.", "metrics": metrics})

@app.get("/api/data-summary")
def data_summary():
    df = pd.read_csv(DATA_PATH)
    return jsonify({
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "features": FEATURES,
        "price_min": round(float(df.price_lakh.min()), 2),
        "price_max": round(float(df.price_lakh.max()), 2),
        "price_avg": round(float(df.price_lakh.mean()), 2)
    })

import os

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )
