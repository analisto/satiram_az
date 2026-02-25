"""
Scraper for cms.satiram.az/api/v1/az/products
Fetches all pages concurrently with asyncio + aiohttp, saves to data/satiram.csv
"""

from __future__ import annotations

import asyncio
import csv
import sys
import time
from pathlib import Path

import aiohttp

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BASE_URL = "https://cms.satiram.az/api/v1/az/products"
HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://satiram.az/",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/145.0.0.0 Safari/537.36"
    ),
    "DNT": "1",
}
CONCURRENCY = 20          # simultaneous requests
RETRY_LIMIT = 4
RETRY_DELAY = 2.0         # seconds between retries
OUTPUT_PATH = Path(__file__).parent.parent / "data" / "satiram.csv"

# ---------------------------------------------------------------------------
# CSV columns
# ---------------------------------------------------------------------------
COLUMNS = [
    "id", "name", "slug", "status",
    "price", "old_price",
    "views", "rating", "favorites_count", "contact_count",
    "is_new", "has_delivery", "is_premium", "is_shop",
    "warranty", "whatsapp_enabled",
    "category_id", "category_name", "category_slug",
    "city_id", "city_name",
    "customer_id", "customer_name", "customer_phone",
    "customer_is_shop", "customer_ads_count",
    "images",
    "created_at", "updated_at", "last_auto_refresh",
    "description", "meta_title", "meta_description", "meta_keywords",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def flatten(product: dict) -> dict:
    cat = product.get("category") or {}
    city = product.get("city") or {}
    cust = product.get("customer") or {}
    images = product.get("images") or []

    return {
        "id":                  product.get("id"),
        "name":                product.get("name"),
        "slug":                product.get("slug"),
        "status":              product.get("status"),
        "price":               product.get("price"),
        "old_price":           product.get("old_price"),
        "views":               product.get("views"),
        "rating":              product.get("rating"),
        "favorites_count":     product.get("favorites_count"),
        "contact_count":       product.get("contact_count"),
        "is_new":              product.get("is_new"),
        "has_delivery":        product.get("has_delivery"),
        "is_premium":          product.get("is_premium"),
        "is_shop":             product.get("is_shop"),
        "warranty":            product.get("warranty"),
        "whatsapp_enabled":    product.get("whatsapp_enabled"),
        "category_id":         cat.get("id"),
        "category_name":       cat.get("name"),
        "category_slug":       cat.get("slug"),
        "city_id":             city.get("id"),
        "city_name":           city.get("name"),
        "customer_id":         cust.get("id"),
        "customer_name":       cust.get("name"),
        "customer_phone":      cust.get("phone"),
        "customer_is_shop":    cust.get("is_shop"),
        "customer_ads_count":  cust.get("ads_count"),
        "images":              " | ".join(images) if isinstance(images, list) else images,
        "created_at":          product.get("created_at"),
        "updated_at":          product.get("updated_at"),
        "last_auto_refresh":   product.get("last_auto_refresh"),
        "description":         product.get("description"),
        "meta_title":          product.get("meta_title"),
        "meta_description":    product.get("meta_description"),
        "meta_keywords":       product.get("meta_keywords"),
    }


# ---------------------------------------------------------------------------
# Async fetch with retries
# ---------------------------------------------------------------------------
async def fetch_page(
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    page: int,
) -> list[dict]:
    url = f"{BASE_URL}?page={page}"
    for attempt in range(1, RETRY_LIMIT + 1):
        async with sem:
            try:
                async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    resp.raise_for_status()
                    data = await resp.json(content_type=None)
                    products = data.get("products") or []
                    return [flatten(p) for p in products]
            except Exception as exc:
                if attempt == RETRY_LIMIT:
                    print(f"\n[ERROR] page {page} failed after {RETRY_LIMIT} attempts: {exc}", file=sys.stderr)
                    return []
                await asyncio.sleep(RETRY_DELAY * attempt)
    return []


async def get_last_page(session: aiohttp.ClientSession) -> int:
    async with session.get(
        f"{BASE_URL}?page=1", headers=HEADERS, timeout=aiohttp.ClientTimeout(total=30)
    ) as resp:
        resp.raise_for_status()
        data = await resp.json(content_type=None)
        return data["pagination"]["last_page"]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
async def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    connector = aiohttp.TCPConnector(limit=CONCURRENCY, ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        print("Fetching page 1 to discover total pages …")
        last_page = await get_last_page(session)
        print(f"Total pages: {last_page}")

        sem = asyncio.Semaphore(CONCURRENCY)
        tasks = [fetch_page(session, sem, p) for p in range(1, last_page + 1)]

        written = 0
        start = time.monotonic()

        with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=COLUMNS)
            writer.writeheader()

            # gather with progress display
            for coro in asyncio.as_completed(tasks):
                rows = await coro
                writer.writerows(rows)
                written += len(rows)
                elapsed = time.monotonic() - start
                done = written
                rate = done / elapsed if elapsed else 0
                print(f"\r  {done:>6} products saved  |  {rate:.0f} products/s  |  {elapsed:.1f}s elapsed", end="", flush=True)

    print(f"\nDone. {written} rows saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
