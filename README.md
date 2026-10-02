# HousePriceAI — House Price Prediction using Linear Regression

A complete BCA project website with a modern frontend and Python/Flask machine-learning backend.

## Features
- Responsive modern website
- House price prediction form
- Linear Regression model using scikit-learn
- Sample housing dataset included
- Train/test split
- MAE, MSE, RMSE and R² evaluation
- API health check
- Model retraining endpoint
- INR/lakh prediction output

## Project structure
house_price_prediction/
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   └── model.joblib (generated automatically)
├── data/
│   └── house_prices.csv
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
└── README.md

## Requirements
Install Python 3.10+.

## Windows setup
Open PowerShell inside the project folder:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

The backend will run at:
http://127.0.0.1:5000

Then open:
frontend/index.html

The frontend communicates with the Flask API on port 5000.

## If PowerShell blocks activation
Run:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

## API endpoints
GET  /api/health
GET  /api/metrics
GET  /api/data-summary
POST /api/predict
POST /api/retrain

## Prediction input
- area_sqft
- bedrooms
- bathrooms
- age_years
- location_score (1–10)
- parking

## Important project note
The included CSV is a generated educational dataset so the project works immediately. For a college submission with real-world results, replace `data/house_prices.csv` with a real housing dataset using the same feature columns, or update the preprocessing/model code for your chosen dataset.

## Suggested viva explanation
1. This is supervised machine learning because the dataset has labeled prices.
2. The target variable is continuous, so regression is used.
3. Linear Regression learns coefficients for the house features.
4. 80% of data is used for training and 20% for testing.
5. MAE/MSE/RMSE measure prediction error, while R² measures explained variance.
