from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

import pandas as pd
import numpy as np
import os

# ==========================================================
# FLASK APP
# ==========================================================

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_PATH = os.path.join(BASE_DIR, "house_prices.csv")

# IMPORTANT:
# Get the folder where app.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ==========================================================
# SERVE WEBSITE FILES
# ==========================================================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(BASE_DIR, filename)


# ==========================================================
# LOAD DATASET
# ==========================================================

# house_prices.csv is in the SAME folder as app.py
DATA_PATH = os.path.join(BASE_DIR, "house_prices.csv")


if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(
        "house_prices.csv not found. Make sure it is in the same folder as app.py"
    )


df = pd.read_csv(DATA_PATH)


# ==========================================================
# CLEAN COLUMN NAMES
# ==========================================================

df.columns = (
    df.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
)

print("Dataset columns:", list(df.columns))


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
    col for col in required_columns
    if col not in df.columns
]


if missing_columns:
    raise ValueError(
        f"Missing columns in house_prices.csv: {missing_columns}"
    )


# ==========================================================
# CLEAN DATA
# ==========================================================

df = df.dropna(subset=required_columns)


# Convert numeric columns
for col in ["bhk", "bathrooms", "sqft", "age", "price"]:
    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )


df = df.dropna()


# Remove invalid values
df = df[
    (df["bhk"] > 0) &
    (df["bathrooms"] > 0) &
    (df["sqft"] > 0) &
    (df["age"] >= 0) &
    (df["price"] > 0)
]


# ==========================================================
# FEATURES
# ==========================================================

X = df[
    [
        "area",
        "bhk",
        "bathrooms",
        "sqft",
        "age"
    ]
]


y = df["price"]


categorical_features = [
    "area"
]


numeric_features = [
    "bhk",
    "bathrooms",
    "sqft",
    "age"
]


# ==========================================================
# PREPROCESSOR
# ==========================================================

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


# ==========================================================
# MACHINE LEARNING MODEL
# ==========================================================

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
                min_samples_split=2
            )
        )
    ]
)


# ==========================================================
# TRAIN MODEL
# ==========================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
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


print("========================================")
print("Model trained successfully")
print("Dataset rows:", len(df))
print("MAE:", mae)
print("R2:", r2)
print("========================================")


# ==========================================================
# HEALTH CHECK
# ==========================================================

@app.route("/api/health")
def health():

    return jsonify({
        "status": "success",
        "message": "House Price API is running",
        "rows": len(df),
        "model_r2": round(float(r2), 3)
    })


# ==========================================================
# GET ALL AREAS
# ==========================================================

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


# ==========================================================
# AREA DETAILS
# ==========================================================

@app.route("/api/area/<path:area_name>")
def area_details(area_name):

    area_data = df[
        df["area"]
        .astype(str)
        .str.lower()
        == area_name.lower()
    ]


    if area_data.empty:

        return jsonify({
            "success": False,
            "message": "Area not found"
        }), 404


    avg_price = area_data["price"].mean()

    avg_sqft = area_data["sqft"].mean()

    price_per_sqft = (
        area_data["price"] /
        area_data["sqft"]
    ).mean()

    min_price = area_data["price"].min()

    max_price = area_data["price"].max()

    avg_bhk = area_data["bhk"].mean()


    return jsonify({

        "success": True,

        "area": area_name,

        "properties": len(area_data),

        "average_price": round(
            float(avg_price),
            2
        ),

        "minimum_price": round(
            float(min_price),
            2
        ),

        "maximum_price": round(
            float(max_price),
            2
        ),

        "average_sqft": round(
            float(avg_sqft),
            2
        ),

        "price_per_sqft": round(
            float(price_per_sqft),
            2
        ),

        "average_bhk": round(
            float(avg_bhk),
            2
        )
    })


# ==========================================================
# ALL AREA STATISTICS
# ==========================================================

@app.route("/api/area-stats")
def area_stats():

    grouped = df.groupby("area")

    results = []


    for area, data in grouped:

        avg_price = data["price"].mean()

        price_per_sqft = (
            data["price"] /
            data["sqft"]
        ).mean()


        results.append({

            "area": str(area),

            "average_price": round(
                float(avg_price),
                2
            ),

            "price_per_sqft": round(
                float(price_per_sqft),
                2
            ),

            "properties": len(data)
        })


    results = sorted(
        results,
        key=lambda x: x["average_price"],
        reverse=True
    )


    return jsonify({

        "success": True,

        "data": results
    })


# ==========================================================
# PRICE PREDICTION
# ==========================================================

@app.route("/api/predict", methods=["POST"])
def predict():

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "message": "No data received"
            }), 400


        # ----------------------------------------------
        # GET INPUT VALUES
        # ----------------------------------------------

        area = str(
            data.get(
                "area",
                ""
            )
        ).strip()


        bhk = float(
            data.get(
                "bhk",
                0
            )
        )


        bathrooms = float(
            data.get(
                "bathrooms",
                0
            )
        )


        sqft = float(
            data.get(
                "sqft",
                0
            )
        )


        age = float(
            data.get(
                "age",
                0
            )
        )


        # ----------------------------------------------
        # VALIDATION
        # ----------------------------------------------

        if not area:

            return jsonify({
                "success": False,
                "message": "Please select an area"
            }), 400


        if bhk <= 0:

            return jsonify({
                "success": False,
                "message": "Invalid BHK"
            }), 400


        if bathrooms <= 0:

            return jsonify({
                "success": False,
                "message": "Invalid bathrooms"
            }), 400


        if sqft <= 0:

            return jsonify({
                "success": False,
                "message": "Invalid square feet"
            }), 400


        if age < 0:

            return jsonify({
                "success": False,
                "message": "Invalid property age"
            }), 400


        # ----------------------------------------------
        # CREATE INPUT DATA
        # ----------------------------------------------

        input_data = pd.DataFrame([{

            "area": area,

            "bhk": bhk,

            "bathrooms": bathrooms,

            "sqft": sqft,

            "age": age

        }])


        # ----------------------------------------------
        # PREDICT PRICE
        # ----------------------------------------------

        predicted_price = model.predict(
            input_data
        )[0]


        # ----------------------------------------------
        # AREA INFORMATION
        # ----------------------------------------------

        area_data = df[
            df["area"]
            .astype(str)
            .str.lower()
            == area.lower()
        ]


        if not area_data.empty:

            area_avg = (
                area_data["price"]
                .mean()
            )


            area_price_sqft = (
                area_data["price"] /
                area_data["sqft"]
            ).mean()


        else:

            area_avg = predicted_price

            area_price_sqft = (
                predicted_price /
                sqft
            )


        # ----------------------------------------------
        # PRICE RANGE
        # ----------------------------------------------

        lower_price = (
            predicted_price * 0.90
        )


        upper_price = (
            predicted_price * 1.10
        )


        # ----------------------------------------------
        # PRICE PER SQFT
        # ----------------------------------------------

        predicted_price_sqft = (
            predicted_price /
            sqft
        )


        # ----------------------------------------------
        # RESPONSE
        # ----------------------------------------------

        return jsonify({

            "success": True,

            "predicted_price": round(
                float(predicted_price),
                2
            ),

            "minimum_estimate": round(
                float(lower_price),
                2
            ),

            "maximum_estimate": round(
                float(upper_price),
                2
            ),

            "price_per_sqft": round(
                float(predicted_price_sqft),
                2
            ),

            "area_average_price": round(
                float(area_avg),
                2
            ),

            "area_price_per_sqft": round(
                float(area_price_sqft),
                2
            ),

            "model_accuracy": round(
                float(r2 * 100),
                2
            ),

            "area": area,

            "sqft": sqft,

            "bhk": bhk,

            "bathrooms": bathrooms,

            "age": age
        })


    except ValueError:

        return jsonify({

            "success": False,

            "message": "Please enter valid numeric values."
        }), 400


    except Exception as e:

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500


# ==========================================================
# MARKET SUMMARY
# ==========================================================

@app.route("/api/market-summary")
def market_summary():

    average_price = (
        df["price"].mean()
    )


    median_price = (
        df["price"].median()
    )


    average_sqft = (
        df["sqft"].mean()
    )


    average_price_sqft = (
        df["price"] /
        df["sqft"]
    ).mean()


    area_prices = (
        df.groupby("area")["price"]
        .mean()
    )


    most_expensive_area = (
        area_prices.idxmax()
    )


    cheapest_area = (
        area_prices.idxmin()
    )


    return jsonify({

        "success": True,

        "total_properties": len(df),

        "total_areas": df[
            "area"
        ].nunique(),

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
            float(average_price_sqft),
            2
        ),

        "most_expensive_area":
            str(most_expensive_area),

        "cheapest_area":
            str(cheapest_area)
    })


# ==========================================================
# RECOMMENDED AREAS
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
        grouped["average_price"] /
        grouped["average_sqft"]
    )


    grouped = grouped.sort_values(
        "price_per_sqft"
    )


    result = []


    for _, row in grouped.head(6).iterrows():

        result.append({

            "area": str(
                row["area"]
            ),

            "average_price": round(
                float(
                    row["average_price"]
                ),
                2
            ),

            "price_per_sqft": round(
                float(
                    row["price_per_sqft"]
                ),
                2
            ),

            "properties": int(
                row["properties"]
            )
        })


    return jsonify({

        "success": True,

        "data": result
    })


# ==========================================================
# RUN SERVER
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
