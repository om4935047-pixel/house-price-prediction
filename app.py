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

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "house_prices.csv")

if not os.path.exists(DATA_PATH):
    raise FileNotFoundError("house_prices.csv not found. Put it in the same folder as app.py")

df = pd.read_csv(DATA_PATH)
df.columns = (df.columns.astype(str).str.strip().str.lower().str.replace(" ", "_", regex=False))
required = ["area", "bhk", "bathrooms", "sqft", "age", "price"]
missing = [c for c in required if c not in df.columns]
if missing:
    raise ValueError(f"Missing columns in house_prices.csv: {missing}")

for c in ["bhk", "bathrooms", "sqft", "age", "price"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")
df["area"] = df["area"].astype(str).str.strip()
df = df.dropna(subset=required)
df = df[(df.bhk > 0) & (df.bathrooms > 0) & (df.sqft > 0) & (df.age >= 0) & (df.price > 0)]

if len(df) < 5:
    raise ValueError("Dataset must contain at least 5 valid property rows")

X = df[["area", "bhk", "bathrooms", "sqft", "age"]]
y = df["price"]
pre = ColumnTransformer([
    ("area", OneHotEncoder(handle_unknown="ignore"), ["area"])
], remainder="passthrough")
model = Pipeline([
    ("preprocessor", pre),
    ("model", RandomForestRegressor(n_estimators=300, random_state=42, max_depth=18, n_jobs=-1))
])

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)
model.fit(X_train, y_train)
pred = model.predict(X_test)
r2 = r2_score(y_test, pred) if len(y_test) > 1 else 0.0
mae = mean_absolute_error(y_test, pred) if len(y_test) else 0.0

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/health")
def health():
    return jsonify(success=True, message="House Price API is running", rows=len(df), model_r2=round(float(r2), 3))

@app.route("/api/locations")
def locations():
    # The dataset is the source of truth for prediction locations.
    # If state/city columns exist, return them too.
    result = {"states": [], "cities": [], "areas": sorted(df.area.unique().tolist())}
    if "state" in df.columns:
        result["states"] = sorted(df.state.dropna().astype(str).str.strip().unique().tolist())
    if "city" in df.columns:
        result["cities"] = sorted(df.city.dropna().astype(str).str.strip().unique().tolist())
    return jsonify(success=True, **result)

@app.route("/api/areas")
def areas():
    return jsonify(success=True, areas=sorted(df.area.unique().tolist()))

@app.route("/api/area/<path:area_name>")
def area_details(area_name):
    area_name = unquote(area_name).strip()
    d = df[df.area.str.casefold() == area_name.casefold()]
    if d.empty:
        return jsonify(success=False, message="Area not found in the training dataset"), 404
    avg = d.price.mean(); avg_sqft = d.sqft.mean(); pps = (d.price / d.sqft).mean()
    return jsonify(success=True, area=area_name, properties=len(d), average_price=round(float(avg),2),
                   minimum_price=round(float(d.price.min()),2), maximum_price=round(float(d.price.max()),2),
                   average_sqft=round(float(avg_sqft),2), price_per_sqft=round(float(pps),2),
                   average_bhk=round(float(d.bhk.mean()),2))

@app.route("/api/area-stats")
def area_stats():
    g = df.groupby("area").agg(average_price=("price","mean"), average_sqft=("sqft","mean"), properties=("price","count")).reset_index()
    g["price_per_sqft"] = g.average_price / g.average_sqft
    g = g.sort_values("average_price", ascending=False)
    return jsonify(success=True, data=[{"area":str(r.area), "average_price":round(float(r.average_price),2), "price_per_sqft":round(float(r.price_per_sqft),2), "properties":int(r.properties)} for r in g.itertuples()])

@app.route("/api/market-summary")
def market_summary():
    ap = df.price.mean(); pps = (df.price / df.sqft).mean(); by_area = df.groupby("area").price.mean()
    return jsonify(success=True, total_properties=len(df), total_areas=int(df.area.nunique()), average_price=round(float(ap),2),
                   median_price=round(float(df.price.median()),2), average_sqft=round(float(df.sqft.mean()),2),
                   average_price_per_sqft=round(float(pps),2), most_expensive_area=str(by_area.idxmax()), cheapest_area=str(by_area.idxmin()), model_accuracy=round(float(r2*100),2))

@app.route("/api/recommendations")
def recommendations():
    g = df.groupby("area").agg(average_price=("price","mean"), average_sqft=("sqft","mean"), properties=("price","count")).reset_index()
    g["price_per_sqft"] = g.average_price / g.average_sqft
    g = g.sort_values("price_per_sqft").head(8)
    return jsonify(success=True, data=[{"area":str(r.area),"average_price":round(float(r.average_price),2),"price_per_sqft":round(float(r.price_per_sqft),2),"properties":int(r.properties)} for r in g.itertuples()])

@app.route("/api/predict", methods=["POST"])
def predict_price():
    try:
        data = request.get_json(silent=True) or {}
        area = str(data.get("area", "")).strip()
        if not area: return jsonify(success=False, message="Please select an area"), 400
        if not (df.area.str.casefold() == area.casefold()).any():
            return jsonify(success=False, message="Prediction is not available for this area because it is not present in the training dataset. Add property records for this area to house_prices.csv first."), 400
        vals = {}
        for key in ["bhk","bathrooms","sqft","age"]:
            try: vals[key] = float(data.get(key, 0))
            except (TypeError, ValueError): return jsonify(success=False, message=f"Invalid {key}"), 400
        if vals["bhk"] <= 0 or vals["bathrooms"] <= 0 or vals["sqft"] <= 0 or vals["age"] < 0:
            return jsonify(success=False, message="Please enter valid positive property values"), 400
        inp = pd.DataFrame([{"area":area, **vals}])
        price = float(model.predict(inp)[0])
        ad = df[df.area.str.casefold() == area.casefold()]
        area_avg = float(ad.price.mean()); area_pps = float((ad.price/ad.sqft).mean())
        return jsonify(success=True, predicted_price=round(price,2), minimum_estimate=round(price*.90,2), maximum_estimate=round(price*1.10,2),
                       price_per_sqft=round(price/vals["sqft"],2), area_average_price=round(area_avg,2), area_price_per_sqft=round(area_pps,2),
                       model_accuracy=round(float(r2*100),2), area=area, **vals)
    except Exception as e:
        app.logger.exception("Prediction error")
        return jsonify(success=False, message=f"Prediction error: {e}"), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)), debug=False)
