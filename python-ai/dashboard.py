import os
from pathlib import Path

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv


ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(ENV_PATH)

API_URL = os.getenv("API_URL", "http://127.0.0.1:8001")

st.set_page_config(
    page_title="Vinted Analytics Dashboard",
    layout="wide"
)

st.title("Vinted Analytics Dashboard")

query = st.text_input("Szukana fraza", value="nike hoodie")

if st.button("Pobierz / odśwież dane"):
    requests.get(f"{API_URL}/vinted-offers", params={"query": query})

response = requests.get(f"{API_URL}/analytics/dashboard", params={"query": query})

if response.status_code != 200:
    st.error("Nie udało się pobrać danych z API")
    st.stop()

data = response.json()

summary = data["summary"]

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Liczba ofert", summary["offers_count"])
col2.metric("Średnia cena", f'{summary["average_price_pln"]} zł')
col3.metric("Mediana", f'{summary["median_price_pln"]} zł')
col4.metric("Min", f'{summary["min_price_pln"]} zł')
col5.metric("Max", f'{summary["max_price_pln"]} zł')

st.divider()

brands_df = pd.DataFrame(data["brands"])
sizes_df = pd.DataFrame(data["sizes"])
trend_df = pd.DataFrame(data["trend"])
distribution_df = pd.DataFrame(data["distribution"])
deals_df = pd.DataFrame(data["best_deals"])
outliers_df = pd.DataFrame(data["outliers"].get("outliers", []))

left, right = st.columns(2)

with left:
    st.subheader("Średnia cena według marki")
    if not brands_df.empty:
        fig = px.bar(
            brands_df,
            x="brand",
            y="average_price",
            text="offers_count"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Brak danych o markach")

with right:
    st.subheader("Rozmiary")
    if not sizes_df.empty:
        fig = px.bar(
            sizes_df,
            x="size",
            y="offers_count"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Brak danych o rozmiarach")

st.subheader("Trend cen w czasie")

if not trend_df.empty:
    fig = px.line(
        trend_df,
        x="date",
        y="average_price",
        markers=True
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Brak danych trendu")

st.subheader("Rozkład cen")

if not distribution_df.empty:
    fig = px.bar(
        distribution_df,
        x="price_bucket",
        y="offers_count"
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Brak danych rozkładu cen")

st.subheader("Najlepsze okazje")

if not deals_df.empty:
    st.dataframe(
        deals_df[
            [
                "title",
                "brand",
                "size",
                "price",
                "reference_price",
                "deal_score",
                "deal_label",
                "url"
            ]
        ],
        use_container_width=True
    )
else:
    st.info("Brak okazji")

st.subheader("Outliery")

if not outliers_df.empty:
    st.warning(f"Wykryto {len(outliers_df)} nietypowych ofert")
    st.dataframe(outliers_df, use_container_width=True)
else:
    st.success("Brak widocznych outlierów")

st.subheader("ML price prediction")

brand = st.text_input("Marka do predykcji", value="Nike")
size = st.text_input("Rozmiar do predykcji", value="M")

if st.button("Przewidź cenę"):
    prediction_response = requests.get(
        f"{API_URL}/analytics/predict-price",
        params={
            "query": query,
            "brand": brand,
            "size": size
        }
    )

    if prediction_response.status_code != 200:
        st.error("Nie udało się pobrać predykcji z API")
        st.stop()

    prediction = prediction_response.json()

    if "error" in prediction:
        st.error(prediction["error"])
    else:
        st.success(
            f'Przewidywana cena: {prediction["predicted_price_pln"]} zł '
            f'na podstawie {prediction["training_offers"]} ofert'
        )