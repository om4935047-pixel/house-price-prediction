import os
import warnings
import joblib
import numpy as np
import pandas as pd

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error

warnings.filterwarnings("ignore")

# =========================================================
# APP CONFIGURATION
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
CORS(app)

DATA_PATH = os.path.join(BASE_DIR, "house_prices.csv")
MODEL_PATH = os.path.join(BASE_DIR, "model.joblib")


# =========================================================
# LOAD DATASET
# =========================================================

if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(
        "house_prices.csv not found. Make sure it is in the same folder as app.py"
    )

df = pd.read_csv(DATA_PATH)

# Clean column names
df.columns = (
    df.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
)

print("Dataset columns:", list(df.columns))

# Required columns
required_columns = [
    "area",
    "bhk",
    "bathrooms",
    "sqft",
    "age",
    "price"
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing columns in house_prices.csv: {missing_columns}"
    )


# =========================================================
# CLEAN DATA
# =========================================================

df["area"] = df["area"].astype(str).str.strip()

for column in ["bhk", "bathrooms", "sqft", "age", "price"]:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )

df = df.dropna(
    subset=[
        "area",
        "bhk",
        "bathrooms",
        "sqft",
        "age",
        "price"
    ]
)

df = df[df["sqft"] > 0]
df = df[df["price"] > 0]

df = df.reset_index(drop=True)

print(f"Loaded {len(df)} properties")
print(f"Areas: {df['area'].nunique()}")


# =========================================================
# TRAIN MACHINE LEARNING MODEL
# =========================================================

FEATURES = [
    "area",
    "bhk",
    "bathrooms",
    "sqft",
    "age"
]

TARGET = "price"

X = df[FEATURES]
y = df[TARGET]

categorical_features = ["area"]

numeric_features = [
    "bhk",
    "bathrooms",
    "sqft",
    "age"
]

preprocessor = ColumnTransformer(
    transformers=[
        (
            "area",
            OneHotEncoder(
                handle_unknown="ignore"
            ),
            categorical_features
        ),
        (
            "numeric",
            "passthrough",
            numeric_features
        )
    ]
)

model = Pipeline(
    steps=[
        (
            "preprocessor",
            preprocessor
        ),
        (
            "model",
            RandomForestRegressor(
                n_estimators=250,
                random_state=42,
                max_depth=18,
                min_samples_leaf=2,
                n_jobs=-1
            )
        )
    ]
)


# =========================================================
# MODEL EVALUATION
# =========================================================

if len(df) >= 10:

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    model_r2 = r2_score(
        y_test,
        predictions
    )

    model_mae = mean_absolute_error(
        y_test,
        predictions
    )

else:

    model.fit(X, y)

    model_r2 = 0
    model_mae = 0


# =========================================================
# SAVE MODEL
# =========================================================

try:
    joblib.dump(
        model,
        MODEL_PATH
    )
except Exception as e:
    print("Could not save model:", e)


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def safe_float(value, default=0):
    try:
        return float(value)
    except:
        return default


def safe_int(value, default=0):
    try:
        return int(float(value))
    except:
        return default


def area_statistics(area_name):

    area_data = df[
        df["area"].str.lower()
        == str(area_name).lower()
    ]

    if area_data.empty:
        return None

    average_price = area_data["price"].mean()

    average_sqft = area_data["sqft"].mean()

    price_per_sqft = (
        area_data["price"] /
        area_data["sqft"]
    ).mean()

    return {
        "area": str(area_data["area"].iloc[0]),
        "properties": int(len(area_data)),
        "average_price": round(float(average_price), 2),
        "minimum_price": round(
            float(area_data["price"].min()), 2
        ),
        "maximum_price": round(
            float(area_data["price"].max()), 2
        ),
        "average_sqft": round(
            float(average_sqft), 2
        ),
        "price_per_sqft": round(
            float(price_per_sqft), 2
        )
    }


def all_area_statistics():

    result = []

    for area in sorted(
        df["area"].dropna().unique()
    ):

        stats = area_statistics(area)

        if stats:
            result.append(stats)

    return result


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def home():

    return send_from_directory(
        BASE_DIR,
        "index.html"
    )


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/api/health")
def health():

    return jsonify({
        "status": "success",
        "message": "House Price Prediction API is running",
        "properties": int(len(df)),
        "areas": int(df["area"].nunique())
    })


# =========================================================
# GET ALL AREAS
# =========================================================

@app.route("/api/areas")
def get_areas():

    areas = sorted(
        df["area"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    return jsonify({
        "success": True,
        "areas": areas
    })


# =========================================================
# AREA INFORMATION
# =========================================================

@app.route("/api/area/<path:area_name>")
def get_area(area_name):

    stats = area_statistics(area_name)

    if stats is None:

        return jsonify({
            "success": False,
            "message": "Area not found"
        }), 404

    return jsonify({
        "success": True,
        "data": stats
    })


# =========================================================
# AREA-WISE STATISTICS
# =========================================================

@app.route("/api/area-stats")
def area_stats():

    stats = all_area_statistics()

    return jsonify({
        "success": True,
        "data": stats
    })


# =========================================================
# PRICE PREDICTION
# =========================================================

@app.route("/api/predict", methods=["POST"])
def predict():

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "message": "No data received"
            }), 400

        area = str(
            data.get("area", "")
        ).strip()

        bhk = safe_int(
            data.get("bhk")
        )

        bathrooms = safe_int(
            data.get("bathrooms")
        )

        sqft = safe_float(
            data.get("sqft")
        )

        age = safe_int(
            data.get("age")
        )

        if not area:
            return jsonify({
                "success": False,
                "message": "Please select an area"
            }), 400

        if bhk <= 0:
            return jsonify({
                "success": False,
                "message": "BHK must be greater than 0"
            }), 400

        if bathrooms <= 0:
            return jsonify({
                "success": False,
                "message": "Bathrooms must be greater than 0"
            }), 400

        if sqft <= 0:
            return jsonify({
                "success": False,
                "message": "Area in square feet must be greater than 0"
            }), 400

        if age < 0:
            return jsonify({
                "success": False,
                "message": "Property age cannot be negative"
            }), 400

        input_data = pd.DataFrame([
            {
                "area": area,
                "bhk": bhk,
                "bathrooms": bathrooms,
                "sqft": sqft,
                "age": age
            }
        ])

        predicted_price = float(
            model.predict(input_data)[0]
        )

        price_per_sqft = (
            predicted_price / sqft
        )

        # Area statistics
        selected_area_data = df[
            df["area"].str.lower()
            == area.lower()
        ]

        if not selected_area_data.empty:

            area_average = float(
                selected_area_data["price"].mean()
            )

            area_min = float(
                selected_area_data["price"].min()
            )

            area_max = float(
                selected_area_data["price"].max()
            )

        else:

            area_average = predicted_price
            area_min = predicted_price * 0.85
            area_max = predicted_price * 1.15

        # Estimated prediction range
        prediction_min = max(
            0,
            predicted_price * 0.90
        )

        prediction_max = (
            predicted_price * 1.10
        )

        return jsonify({
            "success": True,

            "prediction": {
                "price": round(
                    predicted_price,
                    2
                ),

                "minimum": round(
                    prediction_min,
                    2
                ),

                "maximum": round(
                    prediction_max,
                    2
                ),

                "price_per_sqft": round(
                    price_per_sqft,
                    2
                ),

                "area_average": round(
                    area_average,
                    2
                ),

                "area_minimum": round(
                    area_min,
                    2
                ),

                "area_maximum": round(
                    area_max,
                    2
                ),

                "model_r2": round(
                    float(model_r2),
                    4
                )
            }
        })

    except Exception as e:

        print("Prediction error:", e)

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# =========================================================
# MARKET SUMMARY
# =========================================================

@app.route("/api/market-summary")
def market_summary():

    average_price = df["price"].mean()

    price_per_sqft = (
        df["price"] /
        df["sqft"]
    ).mean()

    return jsonify({

        "success": True,

        "total_properties": int(
            len(df)
        ),

        "total_areas": int(
            df["area"].nunique()
        ),

        "average_price": round(
            float(average_price),
            2
        ),

        "average_price_per_sqft": round(
            float(price_per_sqft),
            2
        ),

        "model_r2": round(
            float(model_r2),
            4
        )
    })


# =========================================================
# SIMILAR AREA RECOMMENDATIONS
# =========================================================

@app.route("/api/recommendations")
def recommendations():

    selected_area = request.args.get(
        "area",
        ""
    ).strip()

    stats = all_area_statistics()

    if not stats:

        return jsonify({
            "success": True,
            "data": []
        })

    # If an area is selected, find areas
    # with similar average price.
    if selected_area:

        selected = area_statistics(
            selected_area
        )

        if selected:

            target_price = selected[
                "average_price"
            ]

            target_ppsf = selected[
                "price_per_sqft"
            ]

            for item in stats:

                price_difference = abs(
                    item["average_price"]
                    - target_price
                ) / max(
                    target_price,
                    1
                )

                ppsf_difference = abs(
                    item["price_per_sqft"]
                    - target_ppsf
                ) / max(
                    target_ppsf,
                    1
                )

                item["_similarity"] = (
                    price_difference
                    + ppsf_difference
                )

            stats = sorted(
                stats,
                key=lambda x: x["_similarity"]
            )

            # Remove selected area
            stats = [
                x for x in stats
                if x["area"].lower()
                != selected_area.lower()
            ]

            stats = stats[:6]

            for item in stats:
                item.pop(
                    "_similarity",
                    None
                )

            return jsonify({
                "success": True,
                "data": stats
            })

    # Default: return six areas with
    # lower average price per sqft
    stats = sorted(
        stats,
        key=lambda x: x["price_per_sqft"]
    )

    return jsonify({
        "success": True,
        "data": stats[:6]
    })


# =========================================================
# BUDGET-BASED AREA SEARCH
# =========================================================

@app.route("/api/budget")
def budget_search():

    budget = safe_float(
        request.args.get(
            "budget",
            0
        )
    )

    if budget <= 0:

        return jsonify({
            "success": False,
            "message": "Please enter a valid budget"
        }), 400

    stats = all_area_statistics()

    matches = [
        item
        for item in stats
        if item["average_price"] <= budget
    ]

    matches = sorted(
        matches,
        key=lambda x: x["average_price"]
    )

    return jsonify({
        "success": True,
        "budget": budget,
        "data": matches
    })


# =========================================================
# PRICE DISTRIBUTION
# =========================================================

@app.route("/api/price-distribution")
def price_distribution():

    bins = 8

    try:

        counts, edges = np.histogram(
            df["price"],
            bins=bins
        )

        result = []

        for i in range(
            len(counts)
        ):

            result.append({

                "minimum": round(
                    float(edges[i]),
                    2
                ),

                "maximum": round(
                    float(edges[i + 1]),
                    2
                ),

                "count": int(
                    counts[i]
                )
            })

        return jsonify({
            "success": True,
            "data": result
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# =========================================================
# TREND DATA
# =========================================================

@app.route("/api/trend")
def trend():

    # Look for a possible time/year column
    possible_columns = [
        "year",
        "date",
        "listed_date",
        "listing_date",
        "created_at",
        "sold_date"
    ]

    trend_column = None

    for column in possible_columns:

        if column in df.columns:
            trend_column = column
            break

    # Dataset doesn't contain time information
    if trend_column is None:

        return jsonify({
            "success": False,
            "available": False,
            "message": (
                "Your dataset does not contain a "
                "year or date column. A true historical "
                "price trend requires time-based data."
            )
        })

    temp = df.copy()

    # Numeric year
    if trend_column == "year":

        temp["period"] = pd.to_numeric(
            temp["year"],
            errors="coerce"
        )

    else:

        temp["period"] = pd.to_datetime(
            temp[trend_column],
            errors="coerce"
        ).dt.year

    temp["period"] = pd.to_numeric(
        temp["period"],
        errors="coerce"
    )

    temp = temp.dropna(
        subset=["period"]
    )

    if temp.empty:

        return jsonify({
            "success": False,
            "available": False,
            "message": "No valid date/year data found."
        })

    grouped = (
        temp
        .groupby("period")["price"]
        .mean()
        .reset_index()
        .sort_values("period")
    )

    result = []

    for _, row in grouped.iterrows():

        result.append({
            "year": int(row["period"]),
            "average_price": round(
                float(row["price"]),
                2
            )
        })

    return jsonify({
        "success": True,
        "available": True,
        "data": result
    })


# =========================================================
# AREA COMPARISON
# =========================================================

@app.route("/api/compare")
def compare():

    areas_parameter = request.args.get(
        "areas",
        ""
    )

    if not areas_parameter:

        return jsonify({
            "success": False,
            "message": "Please provide areas"
        }), 400

    requested_areas = [
        x.strip()
        for x in areas_parameter.split(",")
        if x.strip()
    ]

    result = []

    for area in requested_areas:

        stats = area_statistics(area)

        if stats:
            result.append(stats)

    return jsonify({
        "success": True,
        "data": result
    })


# =========================================================
# ERROR HANDLERS
# =========================================================

@app.errorhandler(404)
def not_found(error):

    return jsonify({
        "success": False,
        "message": "API endpoint not found"
    }), 404


@app.errorhandler(500)
def server_error(error):

    return jsonify({
        "success": False,
        "message": "Internal server error"
    }), 500


# =========================================================
# START SERVER
# =========================================================

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
