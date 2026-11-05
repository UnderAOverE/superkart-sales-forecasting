"""Streamlit frontend for the SuperKart sales forecasting API."""
import os

import pandas as pd
import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://superkart-backend:7860").rstrip("/")

st.set_page_config(page_title="SuperKart Sales Forecast", page_icon="🛒", layout="wide")
st.title("🛒 SuperKart - Product Sales Forecast")
st.caption(
    "Forecast the quarterly revenue of a product in a SuperKart outlet. "
    "Predictions are served by the Flask API running in the backend container."
)

# Backend health indicator in the sidebar
with st.sidebar:
    st.subheader("Backend status")
    try:
        health = requests.get(f"{BACKEND_URL}/", timeout=5)
        if health.ok:
            st.success(f"Connected: {BACKEND_URL}")
        else:
            st.error(f"Backend returned {health.status_code}")
    except requests.exceptions.RequestException:
        st.error(f"Cannot reach {BACKEND_URL}")
    st.markdown("---")
    st.markdown(
        "**Input guide**\n\n"
        "- *Product Id prefix*: FD = Food, DR = Drinks, NC = Non-Consumable\n"
        "- *Store age*: years since the store was opened\n"
        "- *Allocated area*: share of the store's display area (0-1)"
    )

tab_single, tab_batch = st.tabs(["Single prediction", "Batch prediction (CSV)"])

# ---------------------------------------------------------------------------
# Single prediction
# ---------------------------------------------------------------------------
with tab_single:
    st.subheader("Describe the product and the store")
    with st.form("single_prediction"):
        col_product, col_store = st.columns(2)
        with col_product:
            st.markdown("**Product**")
            product_weight = st.number_input("Product weight", min_value=1.0, max_value=50.0, value=12.66, step=0.01)
            product_mrp = st.number_input("Product MRP", min_value=10.0, max_value=500.0, value=117.08, step=0.01)
            product_allocated_area = st.slider("Allocated display area (ratio)", 0.0, 0.5, 0.027, 0.001, format="%.3f")
            product_sugar = st.selectbox("Sugar content", ["Low Sugar", "Regular", "No Sugar"])
            product_prefix = st.selectbox("Product Id prefix", ["FD", "DR", "NC"])
            product_category = st.selectbox("Product type category", ["Perishables", "Non Perishables"])
        with col_store:
            st.markdown("**Store**")
            store_type = st.selectbox("Store type", ["Supermarket Type1", "Supermarket Type2", "Departmental Store", "Food Mart"])
            store_size = st.selectbox("Store size", ["Small", "Medium", "High"])
            store_city = st.selectbox("City tier", ["Tier 1", "Tier 2", "Tier 3"])
            store_age = st.number_input("Store age (years)", min_value=0, max_value=100, value=16, step=1)
        submitted = st.form_submit_button("Predict sales", type="primary")

    if submitted:
        payload = {
            "Product_Weight": product_weight,
            "Product_Sugar_Content": product_sugar,
            "Product_Allocated_Area": product_allocated_area,
            "Product_MRP": product_mrp,
            "Store_Size": store_size,
            "Store_Location_City_Type": store_city,
            "Store_Type": store_type,
            "Product_Id_char": product_prefix,
            "Store_Age_Years": int(store_age),
            "Product_Type_Category": product_category,
        }
        try:
            resp = requests.post(f"{BACKEND_URL}/v1/predict", json=payload, timeout=30)
            if resp.ok:
                st.metric("Predicted product-store sales", f"$ {resp.json()['Predicted_Sales']:,.2f}")
            else:
                st.error(f"API error {resp.status_code}: {resp.json().get('error', resp.text)}")
        except requests.exceptions.RequestException as exc:
            st.error(f"Could not reach the backend: {exc}")

# ---------------------------------------------------------------------------
# Batch prediction
# ---------------------------------------------------------------------------
with tab_batch:
    st.subheader("Upload a CSV with one row per product-store record")
    st.markdown(
        "Required columns: `Product_Weight, Product_Sugar_Content, Product_Allocated_Area, Product_MRP, "
        "Store_Size, Store_Location_City_Type, Store_Type, Product_Id_char, Store_Age_Years, Product_Type_Category`"
    )
    uploaded = st.file_uploader("Choose a CSV file", type=["csv"])
    if uploaded is not None:
        batch_df = pd.read_csv(uploaded)
        st.write(f"{len(batch_df)} rows loaded - preview:")
        st.dataframe(batch_df.head(), use_container_width=True)

        if st.button("Predict for all rows", type="primary"):
            try:
                resp = requests.post(
                    f"{BACKEND_URL}/v1/predictbatch",
                    files={"file": ("batch.csv", batch_df.to_csv(index=False).encode("utf-8"), "text/csv")},
                    timeout=120,
                )
                if resp.ok:
                    preds = resp.json()
                    batch_df["Predicted_Sales"] = [preds[str(i)] for i in batch_df.index]
                    st.success("Predictions ready")
                    st.dataframe(batch_df, use_container_width=True)
                    st.metric("Total forecast revenue for this batch", f"$ {batch_df['Predicted_Sales'].sum():,.2f}")
                    st.download_button(
                        "Download predictions (CSV)",
                        data=batch_df.to_csv(index=False).encode("utf-8"),
                        file_name="superkart_batch_predictions.csv",
                        mime="text/csv",
                    )
                else:
                    st.error(f"API error {resp.status_code}: {resp.json().get('error', resp.text)}")
            except requests.exceptions.RequestException as exc:
                st.error(f"Could not reach the backend: {exc}")
