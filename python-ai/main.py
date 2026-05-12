from fastapi import FastAPI, Query
from urllib.parse import quote
from playwright.sync_api import sync_playwright
import re
import statistics
import random

app = FastAPI()


def extract_price(text):
    match = re.search(r"(\d+[,.]?\d*)\s*zł", text.lower())

    try:
        return round(float(match.group(1).replace(",", "."))) if match else None
    except:
        return None


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

            # Scrollowanie, żeby załadować więcej ofert
            for _ in range(3):
                page.mouse.wheel(0, 2000)
                page.wait_for_timeout(1000)

            items = page.locator('[data-testid="grid-item"]').all()

            for item in items[:50]:
                text = item.inner_text()
                price = extract_price(text)

                if price:
                    link_el = item.locator("a").first
                    href = link_el.get_attribute("href") if link_el else ""

                    all_offers.append(
                        {
                            "title": text.split("\n")[0][:80],
                            "link": (
                                "https://www.vinted.pl" + href
                                if href.startswith("/")
                                else href
                            ),
                            "source": "vinted.pl",
                            "detectedPrice": price,
                            "snippet": text.replace("\n", " ")
                        }
                    )

        finally:
            browser.close()

    if not all_offers:
        return {
            "error": "Nie znaleziono ofert",
            "query": query
        }

    prices = [offer["detectedPrice"] for offer in all_offers]

    random_offers = random.sample(
        all_offers,
        min(20, len(all_offers))
    )

    return {
        "query": query,
        "average_price_pln": round(sum(prices) / len(prices)),
        "median_price_pln": round(statistics.median(prices)),
        "comment": (
            f"Analiza {len(all_offers)} ofert dla zapytania: {query}. "
            f"Pokazano {len(random_offers)} losowych podobnych ofert."
        ),
        "similarOffers": random_offers
    }