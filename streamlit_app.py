import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# -------------------------------
# SETTINGS
# -------------------------------
DAYS_BACK = 185
SQFT_TOLERANCE = 0.20
LOT_TOLERANCE = 0.20

# ⬇️ Paste your API key(s) here once you have them
PROPWIRE_API_KEY = ""  # Example: "pk_live_1234"
ATTOM_API_KEY = ""     # Example: "attom_abc123"

st.set_page_config(page_title="ARV Calculator", layout="wide")
st.title("🏠 After Repair Value (ARV) Calculator")

# -------------------------------
# PROPWIRE DATA PULL
# -------------------------------
def get_propwire_comps(address, sqft, lot):
    endpoint = "https://api.propwire.com/v1/comps"
    params = {
        "address": address,
        "radius": 1,  # miles
        "days": DAYS_BACK,
        "min_sqft": int(sqft * (1 - SQFT_TOLERANCE)),
        "max_sqft": int(sqft * (1 + SQFT_TOLERANCE)),
        "min_lot": int(lot * (1 - LOT_TOLERANCE)),
        "max_lot": int(lot * (1 + LOT_TOLERANCE))
    }
    headers = {"Authorization": f"Bearer {PROPWIRE_API_KEY}"}
    response = requests.get(endpoint, params=params, headers=headers)
    if response.status_code == 200:
        return pd.DataFrame(response.json().get("results", []))
    return pd.DataFrame()

# -------------------------------
# ATTOM DATA PULL
# -------------------------------
def get_attom_sales(address):
    endpoint = "https://api.attomdata.com/propertyapi/v1.0.0/saleshistory"
    params = {"address": address}
    headers = {"apikey": ATTOM_API_KEY}
    response = requests.get(endpoint, params=params, headers=headers)
    if response.status_code == 200:
        return pd.DataFrame(response.json().get("property", []))
    return pd.DataFrame()

# -------------------------------
# INPUTS
# -------------------------------
address = st.text_input("Enter property address:")
property_sqft = st.number_input("Property living sqft:", min_value=300, step=50)
lot_size = st.number_input("Lot size (sqft):", min_value=500, step=100)
data_source = st.radio("Choose data source:", ["Propwire", "ATTOM"])

# -------------------------------
# RUN ANALYSIS
# -------------------------------
if address and property_sqft and lot_size:
    if data_source == "Propwire" and PROPWIRE_API_KEY:
        comps = get_propwire_comps(address, property_sqft, lot_size)
    elif data_source == "ATTOM" and ATTOM_API_KEY:
        comps = get_attom_sales(address)
    else:
        comps = pd.DataFrame()

    if comps.empty:
        st.warning("⚠️ No comps found. Check API key or try another source.")
    else:
        # Form 1 – All Comps
        st.subheader("📋 Form 1 - All Comparable Sales")
        st.dataframe(comps)

        # Form 2 – Top 3–5 Closest
        st.subheader("⭐ Form 2 - Top 3-5 Closest Matches")
        if "sqft" in comps.columns and "lot_size" in comps.columns:
            comps["score"] = abs(comps["sqft"] - property_sqft) + abs(comps["lot_size"] - lot_size)
            top_matches = comps.sort_values("score").head(5)
        else:
            top_matches = comps.head(5)
        st.dataframe(top_matches)

        # Form 3 – ARV
        st.subheader("💰 Form 3 - After Repair Value (ARV)")
        if "price" in top_matches.columns:
            arv = round(top_matches["price"].mean(), 0)
            st.metric("Estimated ARV", f"${arv:,.0f}")
        else:
            st.write("Price column not available in this dataset.")
