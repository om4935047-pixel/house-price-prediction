from flask import Flask, request, jsonify, send_from_directory
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import os

# ============================================================
# PROJECT PATHS
# ============================================================

ROOT = Path(__file__).resolve().parent

DATA_PATH = ROOT / "house_prices.csv"
MODEL_PATH = ROOT / "model.joblib"
FRONTEND_PATH = ROOT

FEATURES = [
    "area_sqft",
    "bedrooms",
    "bathrooms",
    "age_years",
    "location_score",
    "parking"
]

# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__, static_folder=str(FRONTEND_PATH), static_url_path="")
app.config["JSON_SORT_KEYS"] = False


# ============================================================
# TRAIN MODEL
# ============================================================

def train_model():

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}"
        )

    df = pd.read_csv(DATA_PATH)

    # Check required columns
    required_columns = FEATURES + ["price_lakh"]

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing columns in dataset: {missing_columns}"
        )

    X = df[FEATURES]
    y = df["price_lakh"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42
    )

    model = LinearRegression()

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    mse = mean_squared_error(y_test, predictions)

    metrics = {
        "mae": round(
            float(mean_absolute_error(y_test, predictions)),
            3
        ),

        "mse": round(
            float(mse),
            3
        ),

        "rmse": round(
            float(np.sqrt(mse)),
            3
        ),

        "r2": round(
            float(r2_score(y_test, predictions)),
            4
        ),

        "train_samples": int(len(X_train)),
        "test_samples": int(len(X_test))
    }

    # Save model
    joblib.dump(model, MODEL_PATH)

    return model, metrics


# ============================================================
# LOAD / TRAIN MODEL
# ============================================================

try:

    model, metrics = train_model()

    print("Model trained successfully.")
    print("Dataset:", DATA_PATH)
    print("Model:", MODEL_PATH)
    print("Metrics:", metrics)

except Exception as error:

    print("MODEL ERROR:", error)

    model = None
    metrics = {}


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def home():

    return send_from_directory(
        FRONTEND_PATH,
        "index.html"
    )


# ============================================================
# STATIC FILES
# ============================================================

@app.route("/<path:filename>")
def static_files(filename):

    return send_from_directory(
        FRONTEND_PATH,
        filename
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/api/health", methods=["GET"])
def health():

    return jsonify({
        "status": "ok",
        "model": "Linear Regression",
        "dataset": DATA_PATH.name
    })


# ============================================================
# MODEL METRICS
# ============================================================

@app.route("/api/metrics", methods=["GET"])
def get_metrics():

    if not metrics:

        return jsonify({
            "error": "Model is not available."
        }), 500

    return jsonify(metrics)


# ============================================================
# DATA SUMMARY
# ============================================================

@app.route("/api/data-summary", methods=["GET"])
def data_summary():

    try:

        df = pd.read_csv(DATA_PATH)

        return jsonify({

            "rows": int(len(df)),

            "columns": int(len(df.columns)),

            "features": FEATURES,

            "price_min": round(
                float(df["price_lakh"].min()),
                2
            ),

            "price_max": round(
                float(df["price_lakh"].max()),
                2
            ),

            "price_avg": round(
                float(df["price_lakh"].mean()),
                2
            )

        })

    except Exception as error:

        return jsonify({
            "error": str(error)
        }), 500


# ============================================================
# PREDICTION
# ============================================================

@app.route("/api/predict", methods=["POST"])
def predict():

    try:

        if model is None:

            return jsonify({
                "error": "Machine learning model is not available."
            }), 500

        data = request.get_json(force=True)

        values = {
            feature: float(data[feature])
            for feature in FEATURES
        }

        # Validation

        if values["area_sqft"] <= 0:

            return jsonify({
                "error": "Area must be greater than 0."
            }), 400

        if not 1 <= values["bedrooms"] <= 10:

            return jsonify({
                "error": "Bedrooms must be between 1 and 10."
            }), 400

        if not 1 <= values["bathrooms"] <= 10:

            return jsonify({
                "error": "Bathrooms must be between 1 and 10."
            }), 400

        if not 0 <= values["age_years"] <= 150:

            return jsonify({
                "error": "Age must be between 0 and 150 years."
            }), 400

        if not 1 <= values["location_score"] <= 10:

            return jsonify({
                "error": "Location score must be between 1 and 10."
            }), 400

        if not 0 <= values["parking"] <= 5:

            return jsonify({
                "error": "Parking spaces must be between 0 and 5."
            }), 400

        # Create DataFrame

        X = pd.DataFrame(
            [values],
            columns=FEATURES
        )

        # Prediction

        prediction = float(
            model.predict(X)[0]
        )

        # Prevent negative price

        prediction = max(0, prediction)

        price_inr = prediction * 100000

        return jsonify({

            "predicted_price_lakh": round(
                prediction,
                2
            ),

            "predicted_price_inr": round(
                price_inr,
                0
            ),

            "currency": "INR",

            "unit": "lakh"

        })

    except KeyError as error:

        return jsonify({
            "error": f"Missing field: {error.args[0]}"
        }), 400

    except ValueError:

        return jsonify({
            "error": "Please enter valid numeric values."
        }), 400

    except Exception as error:

        return jsonify({
            "error": str(error)
        }), 500


# ============================================================
# RETRAIN MODEL
# ============================================================

@app.route("/api/retrain", methods=["POST"])
def retrain():

    global model
    global metrics

    try:

        model, metrics = train_model()

        return jsonify({

            "message": "Model retrained successfully.",

            "metrics": metrics

        })

    except Exception as error:

        return jsonify({
            "error": str(error)
        }), 500


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
