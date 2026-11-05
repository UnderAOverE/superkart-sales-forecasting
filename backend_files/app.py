"""
SuperKart sales forecasting API (Flask).

Endpoints
---------
GET  /                 -> health check
GET  /v1/schema        -> the features and categorical levels the model expects
POST /v1/predict       -> online inference: one product-store record as JSON
POST /v1/predictbatch  -> batch inference: a CSV file (multipart field "file") with one row per record
"""
import os

import joblib
import pandas as pd
from flask import Flask, jsonify, request

# ----------------------------------------------------------------------------
# App and model
# ----------------------------------------------------------------------------
superkart_api = Flask("superkart_sales_forecasting_api")

MODEL_PATH = os.getenv("MODEL_PATH", "superkart_model.joblib")
model = joblib.load(MODEL_PATH)  # preprocessing + tuned Random Forest pipeline

# Input contract (must match the columns the pipeline was trained on)
NUMERIC_FEATURES = ["Product_Weight", "Product_Allocated_Area", "Product_MRP", "Store_Age_Years"]
CATEGORICAL_FEATURES = [
    "Product_Sugar_Content",
    "Store_Size",
    "Store_Location_City_Type",
    "Store_Type",
    "Product_Id_char",
    "Product_Type_Category",
]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

# Levels seen during training (used for the schema endpoint; unseen levels are tolerated by the encoder)
KNOWN_LEVELS = {
    "Product_Sugar_Content": ["Low Sugar", "Regular", "No Sugar"],
    "Store_Size": ["Small", "Medium", "High"],
    "Store_Location_City_Type": ["Tier 1", "Tier 2", "Tier 3"],
    "Store_Type": ["Departmental Store", "Food Mart", "Supermarket Type1", "Supermarket Type2"],
    "Product_Id_char": ["FD", "DR", "NC"],
    "Product_Type_Category": ["Perishables", "Non Perishables"],
}


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def validate_frame(frame: pd.DataFrame):
    """Return an error message if the frame is not usable by the model, otherwise None."""
    missing = [f for f in FEATURES if f not in frame.columns]
    if missing:
        return f"Missing feature(s): {missing}"

    for col in NUMERIC_FEATURES:
        converted = pd.to_numeric(frame[col], errors="coerce")
        if converted.isna().any():
            return f"Feature '{col}' must be numeric for every record."
        frame[col] = converted

    if frame[CATEGORICAL_FEATURES].isna().any().any():
        return "Categorical features cannot be empty."
    return None


def predict_frame(frame: pd.DataFrame):
    """Run the pipeline on a validated frame and return the predictions rounded to 2 decimals."""
    preds = model.predict(frame[FEATURES])
    return [round(float(p), 2) for p in preds]


# ----------------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------------
@superkart_api.get("/")
def home():
    return jsonify({"status": "ok", "message": "SuperKart sales forecasting API is running."})


@superkart_api.get("/v1/schema")
def schema():
    return jsonify({"numeric_features": NUMERIC_FEATURES, "categorical_features": KNOWN_LEVELS})


@superkart_api.post("/v1/predict")
def predict():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Send a JSON object with the product and store attributes."}), 400

    frame = pd.DataFrame([payload])
    error = validate_frame(frame)
    if error:
        return jsonify({"error": error}), 400

    prediction = predict_frame(frame)[0]
    return jsonify({"Predicted_Sales": prediction, "currency": "USD"})


@superkart_api.post("/v1/predictbatch")
def predict_batch():
    if "file" not in request.files:
        return jsonify({"error": "Upload a CSV file in the multipart field named 'file'."}), 400

    try:
        frame = pd.read_csv(request.files["file"])
    except Exception as exc:  # malformed CSV
        return jsonify({"error": f"Could not read the CSV file: {exc}"}), 400

    if frame.empty:
        return jsonify({"error": "The CSV file contains no rows."}), 400

    error = validate_frame(frame)
    if error:
        return jsonify({"error": error}), 400

    predictions = predict_frame(frame)
    # Row index -> predicted sales, so the caller can align predictions with the uploaded rows
    return jsonify({str(i): p for i, p in zip(frame.index, predictions)})


if __name__ == "__main__":
    # Local development server; the Docker image runs the app with gunicorn instead
    superkart_api.run(host="0.0.0.0", port=7860)
