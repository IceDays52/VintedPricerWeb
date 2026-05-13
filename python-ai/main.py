from fastapi import FastAPI, Query
from urllib.parse import quote
from playwright.sync_api import sync_playwright
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from pathlib import Path

import os
import re
import statistics
import random

import pandas as pd
import numpy as np

from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder


ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(ENV_PATH)

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("Brak DATABASE_URL w pliku python-ai/.env")

engine = create_engine(DATABASE_URL)


KNOWN_BRANDS = [
    "nike", "adidas", "puma", "reebok", "zara", "h&m",
    "bershka", "pull&bear", "stradivarius", "reserved",
    "cropp", "house", "new balance", "tommy hilfiger",
    "calvin klein", "ralph lauren", "the north face",
    "columbia", "lacoste", "guess", "levis", "levi's",
    "ed hardy", "carhartt", "stussy", "supreme", "trapstar",
    "essentials", "palm angels", "chrome hearts", "balenciaga",
    "off-white", "fear of god", "represent", "vetements"
]

KNOWN_SIZES = [
    "xxs", "xs", "s", "m", "l", "xl", "xxl",
    "32", "34", "36", "38", "40", "42", "44", "46",
    "48", "50", "52"
]


def extract_price(text: str):
    match = re.search(r"(\d+[,.]?\d*)\s*zł", text.lower())

    try:
        return round(float(match.group(1).replace(",", "."))) if match else None
    except Exception:
        return None


def extract_brand(text: str):
    lower_text = text.lower()

    for brand in KNOWN_BRANDS:
        if brand in lower_text:
            return brand.title()

    return None


def extract_size(text: str):
    lower_text = text.lower()

    for size in KNOWN_SIZES:
        pattern = rf"\b{re.escape(size)}\b"
        if re.search(pattern, lower_text):
            return size.upper()

    return None


def classify_deal(score: int | None):
    if score is None:
        return "unknown"

    if score >= 30:
        return "very_good_deal"
    if score >= 10:
        return "good_deal"
    if score >= -10:
        return "fair_price"
    if score >= -25:
        return "expensive"

    return "very_expensive"


def calculate_deal_score(price: int, median_price: int | None):
    if not median_price or median_price <= 0:
        return None

    return round((median_price - price) / median_price * 100)


def save_offer(offer: dict, query: str):
    with engine.connect() as conn:
        conn.execute(
            text("""
                 INSERT INTO offers
                     (title, brand, size, price, source, url, searched_query)
                 VALUES
                     (:title, :brand, :size, :price, :source, :url, :searched_query)
                     ON CONFLICT (url) DO NOTHING
                 """),
            {
                "title": offer["title"],
                "brand": offer["brand"],
                "size": offer["size"],
                "price": offer["detectedPrice"],
                "source": offer["source"],
                "url": offer["link"],
                "searched_query": query
            }
        )
        conn.commit()


def get_median_price(query: str):
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                 SELECT
                     PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price) AS median_price
                 FROM offers
                 WHERE searched_query = :query
                 """),
            {"query": query}
        ).mappings().first()

    return round(result["median_price"]) if result and result["median_price"] else None


def get_segment_median(query: str, brand: str | None, size: str | None):
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                 SELECT
                     PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price) AS median_price
                 FROM offers
                 WHERE searched_query = :query
                   AND (:brand IS NULL OR brand = :brand)
                   AND (:size IS NULL OR size = :size)
                 """),
            {
                "query": query,
                "brand": brand,
                "size": size
            }
        ).mappings().first()

    return round(result["median_price"]) if result and result["median_price"] else None


def calculate_better_deal_score(
        price: int,
        query: str,
        brand: str | None,
        size: str | None
):
    segment_median = get_segment_median(query, brand, size)
    global_median = get_median_price(query)

    reference_price = segment_median or global_median

    if not reference_price:
        return {
            "deal_score": None,
            "deal_label": "unknown",
            "reference_price": None,
            "reference_type": None
        }

    score = round((reference_price - price) / reference_price * 100)

    return {
        "deal_score": score,
        "deal_label": classify_deal(score),
        "reference_price": reference_price,
        "reference_type": "segment" if segment_median else "global"
    }


def detect_outliers_iqr(prices: list[int]):
    if len(prices) < 4:
        return {}

    q1 = np.percentile(prices, 25)
    q3 = np.percentile(prices, 75)
    iqr = q3 - q1

    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    return {
        "q1": round(q1),
        "q3": round(q3),
        "iqr": round(iqr),
        "lower_bound": round(lower_bound),
        "upper_bound": round(upper_bound)
    }


@app.get("/vinted-offers")
def get_vinted_pricing(query: str = Query(...)):
    search_url = f"https://www.vinted.pl/catalog?search_text={quote(query)}"
    all_offers = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )

        try:
            page.goto(
                search_url,
                wait_until="domcontentloaded",
                timeout=30000
            )

            for _ in range(10):
                page.mouse.wheel(0, 2000)
                page.wait_for_timeout(1000)

            items = page.locator('[data-testid="grid-item"]').all()

            for item in items[:200]:
                item_text = item.inner_text()

                price = extract_price(item_text)
                brand = extract_brand(item_text)
                size = extract_size(item_text)

                if price:
                    link_el = item.locator("a").first
                    href = link_el.get_attribute("href") if link_el else ""

                    offer = {
                        "title": item_text.split("\n")[0][:80],
                        "brand": brand,
                        "size": size,
                        "link": (
                            "https://www.vinted.pl" + href
                            if href.startswith("/")
                            else href
                        ),
                        "source": "vinted.pl",
                        "detectedPrice": price,
                        "snippet": item_text.replace("\n", " ")
                    }

                    all_offers.append(offer)
                    save_offer(offer, query)

        finally:
            browser.close()

    if not all_offers:
        return {
            "error": "Nie znaleziono ofert",
            "query": query
        }

    prices = [offer["detectedPrice"] for offer in all_offers]
    median_price = round(statistics.median(prices))

    for offer in all_offers:
        score = calculate_deal_score(offer["detectedPrice"], median_price)
        offer["dealScore"] = score
        offer["dealLabel"] = classify_deal(score)

    random_offers = random.sample(all_offers, min(20, len(all_offers)))

    return {
        "query": query,
        "offers_analyzed": len(all_offers),
        "average_price_pln": round(sum(prices) / len(prices)),
        "median_price_pln": median_price,
        "min_price_pln": min(prices),
        "max_price_pln": max(prices),
        "comment": (
            f"Analiza {len(all_offers)} ofert dla zapytania: {query}. "
            f"Zapisano oferty do PostgreSQL. "
            f"Pokazano {len(random_offers)} losowych podobnych ofert."
        ),
        "similarOffers": random_offers
    }


@app.get("/analytics/price-summary")
def get_price_summary(query: str = Query(...)):
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                 SELECT
                     COUNT(*) AS offers_count,
                     ROUND(AVG(price)) AS average_price,
                     PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price) AS median_price,
                     MIN(price) AS min_price,
                     MAX(price) AS max_price
                 FROM offers
                 WHERE searched_query = :query
                 """),
            {"query": query}
        ).mappings().first()

    return {
        "query": query,
        "offers_count": result["offers_count"],
        "average_price_pln": result["average_price"],
        "median_price_pln": round(result["median_price"]) if result["median_price"] else None,
        "min_price_pln": result["min_price"],
        "max_price_pln": result["max_price"]
    }


@app.get("/analytics/brands")
def get_brand_analytics(query: str = Query(...)):
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                 SELECT
                     brand,
                     COUNT(*) AS offers_count,
                     ROUND(AVG(price)) AS average_price,
                     MIN(price) AS min_price,
                     MAX(price) AS max_price
                 FROM offers
                 WHERE searched_query = :query
                   AND brand IS NOT NULL
                 GROUP BY brand
                 ORDER BY offers_count DESC
                 """),
            {"query": query}
        ).mappings().all()

    return {
        "query": query,
        "brands": [dict(row) for row in result]
    }


@app.get("/analytics/sizes")
def get_size_analytics(query: str = Query(...)):
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                 SELECT
                     size,
                     COUNT(*) AS offers_count,
                     ROUND(AVG(price)) AS average_price,
                     MIN(price) AS min_price,
                     MAX(price) AS max_price
                 FROM offers
                 WHERE searched_query = :query
                   AND size IS NOT NULL
                 GROUP BY size
                 ORDER BY offers_count DESC
                 """),
            {"query": query}
        ).mappings().all()

    return {
        "query": query,
        "sizes": [dict(row) for row in result]
    }


@app.get("/analytics/price-trend")
def get_price_trend(query: str = Query(...)):
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                 SELECT
                     DATE(created_at) AS date,
                     COUNT(*) AS offers_count,
                     ROUND(AVG(price)) AS average_price,
                     MIN(price) AS min_price,
                     MAX(price) AS max_price
                 FROM offers
                 WHERE searched_query = :query
                 GROUP BY DATE(created_at)
                 ORDER BY DATE(created_at)
                 """),
            {"query": query}
        ).mappings().all()

    return {
        "query": query,
        "trend": [dict(row) for row in result]
    }


@app.get("/analytics/price-distribution")
def get_price_distribution(query: str = Query(...)):
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                 SELECT
                     FLOOR(price / 10) * 10 AS price_bucket,
                     COUNT(*) AS offers_count
                 FROM offers
                 WHERE searched_query = :query
                 GROUP BY price_bucket
                 ORDER BY price_bucket
                 """),
            {"query": query}
        ).mappings().all()

    return {
        "query": query,
        "distribution": [dict(row) for row in result]
    }


@app.get("/analytics/outliers")
def get_outliers(query: str = Query(...)):
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                 SELECT
                     title,
                     brand,
                     size,
                     price,
                     url,
                     created_at
                 FROM offers
                 WHERE searched_query = :query
                 """),
            {"query": query}
        ).mappings().all()

    offers = [dict(row) for row in rows]
    prices = [offer["price"] for offer in offers]

    bounds = detect_outliers_iqr(prices)

    if not bounds:
        return {
            "query": query,
            "message": "Za mało danych do wykrywania outlierów",
            "bounds": None,
            "outliers_count": 0,
            "outliers": []
        }

    outliers = [
        offer for offer in offers
        if offer["price"] < bounds["lower_bound"]
           or offer["price"] > bounds["upper_bound"]
    ]

    return {
        "query": query,
        "bounds": bounds,
        "outliers_count": len(outliers),
        "outliers": outliers
    }


@app.get("/analytics/deals")
def get_deals(query: str = Query(...), limit: int = Query(20)):
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                 SELECT
                     title,
                     brand,
                     size,
                     price,
                     source,
                     url,
                     created_at
                 FROM offers
                 WHERE searched_query = :query
                 ORDER BY price ASC
                     LIMIT :limit
                 """),
            {
                "query": query,
                "limit": limit
            }
        ).mappings().all()

    deals = []

    for row in rows:
        offer = dict(row)

        deal_data = calculate_better_deal_score(
            price=offer["price"],
            query=query,
            brand=offer["brand"],
            size=offer["size"]
        )

        offer.update(deal_data)
        deals.append(offer)

    return {
        "query": query,
        "deals": deals
    }


@app.get("/analytics/predict-price")
def predict_price(
        query: str = Query(...),
        brand: str | None = Query(None),
        size: str | None = Query(None)
):
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                 SELECT
                     title,
                     brand,
                     size,
                     price
                 FROM offers
                 WHERE searched_query = :query
                   AND price IS NOT NULL
                 """),
            {"query": query}
        ).mappings().all()

    data = pd.DataFrame([dict(row) for row in rows])

    if len(data) < 10:
        return {
            "query": query,
            "error": "Za mało danych do predykcji ML. Potrzeba minimum 10 ofert."
        }

    data["brand"] = data["brand"].fillna("unknown")
    data["size"] = data["size"].fillna("unknown")
    data["title"] = data["title"].fillna("")

    X = data[["brand", "size"]]
    y = data["price"]

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                ["brand", "size"]
            )
        ]
    )

    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "model",
                RandomForestRegressor(
                    n_estimators=100,
                    random_state=42
                )
            )
        ]
    )

    model.fit(X, y)

    prediction_input = pd.DataFrame([{
        "brand": brand or "unknown",
        "size": size or "unknown"
    }])

    predicted_price = model.predict(prediction_input)[0]

    return {
        "query": query,
        "brand": brand,
        "size": size,
        "predicted_price_pln": round(predicted_price),
        "training_offers": len(data)
    }


@app.get("/analytics/dashboard")
def get_dashboard(query: str = Query(...)):
    return {
        "query": query,
        "summary": get_price_summary(query),
        "brands": get_brand_analytics(query)["brands"],
        "sizes": get_size_analytics(query)["sizes"],
        "trend": get_price_trend(query)["trend"],
        "distribution": get_price_distribution(query)["distribution"],
        "best_deals": get_deals(query, limit=10)["deals"],
        "outliers": get_outliers(query)
    }