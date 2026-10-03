from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pandas as pd
import numpy as np
import os
from urllib.parse import unquote

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score


# ==========================================================
# FLASK APP
# ==========================================================

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "house_prices.csv")


# ==========================================================
# LOAD DATASET
# ==========================================================

if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(
        "house_prices.csv not found. "
        "Make sure house_prices.csv is in the same folder as app.py"
    )

df = pd.read_csv(DATA_PATH)

# Clean column names
df.columns = (
    df.columns
    .astype(str)
    .str.strip()
    .str.lower()
    .str.replace(" ", "_", regex=False)
)

print("Dataset columns:", list(df.columns))
print("Dataset rows:", len(df))


# ==========================================================
# REQUIRED COLUMNS
# ==========================================================

required_columns = [
    "area",
    "bhk",
    "bathrooms",
    "sqft",
    "age",
    "price"
]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing columns in house_prices.csv: {missing_columns}"
    )


# ==========================================================
# CLEAN DATA
# ==========================================================

df["area"] = (
    df["area"]
    .astype(str)
    .str.strip()
)

for column in [
    "bhk",
    "bathrooms",
    "sqft",
    "age",
    "price"
]:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )

df = df.dropna(
    subset=required_columns
)

df = df[
    (df["bhk"] > 0) &
    (df["bathrooms"] > 0) &
    (df["sqft"] > 0) &
    (df["age"] >= 0) &
    (df["price"] > 0)
].copy()


if len(df) < 5:
    raise ValueError(
        "house_prices.csv must contain at least 5 valid property records."
    )


# ==========================================================
# OPTIONAL STATE / CITY COLUMNS
# ==========================================================

if "state" in df.columns:
    df["state"] = (
        df["state"]
        .astype(str)
        .str.strip()
    )

if "city" in df.columns:
    df["city"] = (
        df["city"]
        .astype(str)
        .str.strip()
    )


# ==========================================================
# MACHINE LEARNING
# ==========================================================

features = [
    "area",
    "bhk",
    "bathrooms",
    "sqft",
    "age"
]

X = df[features]
y = df["price"]


categorical_features = ["area"]

preprocessor = ColumnTransformer(
    transformers=[
        (
            "area",
            OneHotEncoder(
                handle_unknown="ignore"
            ),
            categorical_features
        )
    ],
    remainder="passthrough"
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
                n_estimators=300,
                random_state=42,
                max_depth=18,
                min_samples_split=2,
                n_jobs=-1
            )
        )
    ]
)


# ==========================================================
# TRAIN / TEST
# ==========================================================

test_size = 0.20

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=test_size,
    random_state=42
)

model.fit(
    X_train,
    y_train
)


# ==========================================================
# MODEL EVALUATION
# ==========================================================

predictions = model.predict(X_test)

mae = mean_absolute_error(
    y_test,
    predictions
)

r2 = r2_score(
    y_test,
    predictions
)

print("-----------------------------------")
print("MODEL TRAINED SUCCESSFULLY")
print("Rows:", len(df))
print("MAE:", mae)
print("R2:", r2)
print("-----------------------------------")


# ==========================================================
# HOME
# ==========================================================

@app.route("/")
def home():
    return render_template("index.html")


# ==========================================================
# HEALTH CHECK
# ==========================================================

@app.route("/api/health")
def health():

    return jsonify({
        "success": True,
        "message": "House Price Prediction API is running",
        "dataset_rows": int(len(df)),
        "areas": int(df["area"].nunique()),
        "model_r2": round(float(r2), 4),
        "model_accuracy": round(float(r2 * 100), 2)
    })


# ==========================================================
# AREAS
# ==========================================================

@app.route("/api/areas")
def get_areas():

    areas = sorted(
        df["area"]
        .dropna()
        .unique()
        .tolist()
    )

    return jsonify({
        "success": True,
        "areas": areas
    })


# ==========================================================
# STATES / CITIES / AREAS
# ==========================================================

@app.route("/api/locations")
def locations():

    result = {
        "success": True,
        "states": [],
        "cities": [],
        "areas": sorted(
            df["area"].unique().tolist()
        )
    }

    if "state" in df.columns:

        result["states"] = sorted(
            df["state"]
            .dropna()
            .unique()
            .tolist()
        )

    if "city" in df.columns:

        result["cities"] = sorted(
            df["city"]
            .dropna()
            .unique()
            .tolist()
        )

    return jsonify(result)


# ==========================================================
# CITY FILTER
# ==========================================================

@app.route("/api/cities")
def cities():

    state = request.args.get(
        "state",
        ""
    ).strip()

    if "city" not in df.columns:

        return jsonify({
            "success": True,
            "cities": []
        })

    filtered = df.copy()

    if state and "state" in df.columns:

        filtered = filtered[
            filtered["state"].str.casefold()
            == state.casefold()
        ]

    cities_list = sorted(
        filtered["city"]
        .dropna()
        .unique()
        .tolist()
    )

    return jsonify({
        "success": True,
        "cities": cities_list
    })


# ==========================================================
# AREA FILTER
# ==========================================================

@app.route("/api/filter-areas")
def filter_areas():

    state = request.args.get(
        "state",
        ""
    ).strip()

    city = request.args.get(
        "city",
        ""
    ).strip()

    filtered = df.copy()

    if (
        state and
        "state" in filtered.columns
    ):

        filtered = filtered[
            filtered["state"].str.casefold()
            == state.casefold()
        ]

    if (
        city and
        "city" in filtered.columns
    ):

        filtered = filtered[
            filtered["city"].str.casefold()
            == city.casefold()
        ]

    areas = sorted(
        filtered["area"]
        .dropna()
        .unique()
        .tolist()
    )

    return jsonify({
        "success": True,
        "areas": areas
    })


# ==========================================================
# AREA DETAILS
# ==========================================================

@app.route("/api/area/<path:area_name>")
def area_details(area_name):

    area_name = unquote(
        area_name
    ).strip()

    area_data = df[
        df["area"].str.casefold()
        == area_name.casefold()
    ]

    if area_data.empty:

        return jsonify({
            "success": False,
            "message": "Area not found in training dataset"
        }), 404

    average_price = area_data["price"].mean()

    average_sqft = area_data["sqft"].mean()

    price_per_sqft = (
        area_data["price"]
        / area_data["sqft"]
    ).mean()

    return jsonify({
        "success": True,
        "area": area_name,
        "properties": int(len(area_data)),
        "average_price": round(
            float(average_price),
            2
        ),
        "minimum_price": round(
            float(area_data["price"].min()),
            2
        ),
        "maximum_price": round(
            float(area_data["price"].max()),
            2
        ),
        "average_sqft": round(
            float(average_sqft),
            2
        ),
        "price_per_sqft": round(
            float(price_per_sqft),
            2
        ),
        "average_bhk": round(
            float(area_data["bhk"].mean()),
            2
        )
    })


# ==========================================================
# AREA STATISTICS
# ==========================================================

@app.route("/api/area-stats")
def area_stats():

    grouped = (
        df.groupby("area")
        .agg(
            average_price=("price", "mean"),
            average_sqft=("sqft", "mean"),
            properties=("price", "count")
        )
        .reset_index()
    )

    grouped["price_per_sqft"] = (
        grouped["average_price"]
        / grouped["average_sqft"]
    )

    grouped = grouped.sort_values(
        "average_price",
        ascending=False
    )

    data = []

    for row in grouped.itertuples():

        data.append({
            "area": str(row.area),
            "average_price": round(
                float(row.average_price),
                2
            ),
            "average_sqft": round(
                float(row.average_sqft),
                2
            ),
            "price_per_sqft": round(
                float(row.price_per_sqft),
                2
            ),
            "properties": int(
                row.properties
            )
        })

    return jsonify({
        "success": True,
        "data": data
    })


# ==========================================================
# MARKET SUMMARY
# ==========================================================

@app.route("/api/market-summary")
def market_summary():

    average_price = df["price"].mean()

    median_price = df["price"].median()

    average_sqft = df["sqft"].mean()

    average_price_per_sqft = (
        df["price"] / df["sqft"]
    ).mean()

    area_prices = (
        df.groupby("area")["price"]
        .mean()
    )

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

        "median_price": round(
            float(median_price),
            2
        ),

        "average_sqft": round(
            float(average_sqft),
            2
        ),

        "average_price_per_sqft": round(
            float(average_price_per_sqft),
            2
        ),

        "most_expensive_area": str(
            area_prices.idxmax()
        ),

        "cheapest_area": str(
            area_prices.idxmin()
        ),

        "model_accuracy": round(
            float(r2 * 100),
            2
        ),

        "mae": round(
            float(mae),
            2
        )
    })


# ==========================================================
# RECOMMENDATIONS
# ==========================================================

@app.route("/api/recommendations")
def recommendations():

    grouped = (
        df.groupby("area")
        .agg(
            average_price=("price", "mean"),
            average_sqft=("sqft", "mean"),
            properties=("price", "count")
        )
        .reset_index()
    )

    grouped["price_per_sqft"] = (
        grouped["average_price"]
        / grouped["average_sqft"]
    )

    grouped = grouped.sort_values(
        "price_per_sqft"
    ).head(8)

    data = []

    for row in grouped.itertuples():

        data.append({
            "area": str(row.area),
            "average_price": round(
                float(row.average_price),
                2
            ),
            "price_per_sqft": round(
                float(row.price_per_sqft),
                2
            ),
            "properties": int(
                row.properties
            )
        })

    return jsonify({
        "success": True,
        "data": data
    })


# ==========================================================
# PREDICTION
# ==========================================================

@app.route(
    "/api/predict",
    methods=["POST"]
)
def predict_price():

    try:

        data = request.get_json(
            silent=True
        ) or {}

        area = str(
            data.get("area", "")
        ).strip()

        if not area:

            return jsonify({
                "success": False,
                "message": "Please select an area"
            }), 400


        # --------------------------------------------------
        # IMPORTANT:
        # Do not predict for an area that does not exist
        # in the training dataset.
        # --------------------------------------------------

        area_exists = (
            df["area"]
            .str.casefold()
            == area.casefold()
        ).any()

        if not area_exists:

            return jsonify({
                "success": False,
                "message":
                "Prediction is not available for this area. "
                "This area is not present in house_prices.csv."
            }), 400


        # --------------------------------------------------
        # Read numeric inputs
        # --------------------------------------------------

        values = {}

        for key in [
            "bhk",
            "bathrooms",
            "sqft",
            "age"
        ]:

            try:

                values[key] = float(
                    data.get(key)
                )

            except (
                TypeError,
                ValueError
            ):

                return jsonify({
                    "success": False,
                    "message":
                    f"Invalid value for {key}"
                }), 400


        # --------------------------------------------------
        # Validation
        # --------------------------------------------------

        if values["bhk"] <= 0:

            return jsonify({
                "success": False,
                "message": "BHK must be greater than 0"
            }), 400

        if values["bathrooms"] <= 0:

            return jsonify({
                "success": False,
                "message":
                "Bathrooms must be greater than 0"
            }), 400

        if values["sqft"] <= 0:

            return jsonify({
                "success": False,
                "message":
                "Square feet must be greater than 0"
            }), 400

        if values["age"] < 0:

            return jsonify({
                "success": False,
                "message":
                "Property age cannot be negative"
            }), 400


        # --------------------------------------------------
        # Prediction
        # --------------------------------------------------

        input_data = pd.DataFrame([
            {
                "area": area,
                "bhk": values["bhk"],
                "bathrooms": values["bathrooms"],
                "sqft": values["sqft"],
                "age": values["age"]
            }
        ])

        predicted_price = float(
            model.predict(
                input_data
            )[0]
        )


        # --------------------------------------------------
        # Area statistics
        # --------------------------------------------------

        area_data = df[
            df["area"].str.casefold()
            == area.casefold()
        ]

        area_average = float(
            area_data["price"].mean()
        )

        area_price_per_sqft = float(
            (
                area_data["price"]
                / area_data["sqft"]
            ).mean()
        )

        predicted_price_per_sqft = (
            predicted_price
            / values["sqft"]
        )


        # --------------------------------------------------
        # Result
        # --------------------------------------------------

        return jsonify({

            "success": True,

            "predicted_price": round(
                predicted_price,
                2
            ),

            "minimum_estimate": round(
                predicted_price * 0.90,
                2
            ),

            "maximum_estimate": round(
                predicted_price * 1.10,
                2
            ),

            "price_per_sqft": round(
                predicted_price_per_sqft,
                2
            ),

            "area_average_price": round(
                area_average,
                2
            ),

            "area_price_per_sqft": round(
                area_price_per_sqft,
                2
            ),

            "model_accuracy": round(
                float(r2 * 100),
                2
            ),

            "mae": round(
                float(mae),
                2
            ),

            "area": area,

            "bhk": values["bhk"],
            "bathrooms": values["bathrooms"],
            "sqft": values["sqft"],
            "age": values["age"]
        })


    except Exception as error:

        app.logger.exception(
            "Prediction error"
        )

        return jsonify({
            "success": False,
            "message":
            f"Prediction error: {str(error)}"
        }), 500


# ==========================================================
# RUN
# ==========================================================

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
