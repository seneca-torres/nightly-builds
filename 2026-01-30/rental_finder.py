#!/usr/bin/env python3
"""Rental Finder Agent (prototype).

Searches Zillow, Apartments.com, and optionally Craigslist for rentals that
match the user's criteria. Results are stored with URL-based deduplication.
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup

DATA_FILE = "listings.json"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)
HEADERS = {"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"}

CRITERIA = {
    "locations": ["Scottsdale 85254", "Arcadia Phoenix"],
    "min_beds": 3,
    "price_min": 3000,
    "price_max": 5000,
    "lease_term": "1 year",
    "availability": "end of March or mid-April 2026",
}


def load_listings() -> List[Dict]:
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_listings(listings: List[Dict]) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(listings, f, indent=2, sort_keys=True)


def dedupe(existing: List[Dict], new_items: List[Dict]) -> List[Dict]:
    seen = {item.get("link") for item in existing if item.get("link")}
    merged = list(existing)
    for item in new_items:
        link = item.get("link")
        if not link or link in seen:
            continue
        merged.append(item)
        seen.add(link)
    return merged


def fetch(url: str) -> Optional[str]:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return None
        return resp.text
    except Exception:
        return None


def parse_price(text: str) -> Optional[int]:
    if not text:
        return None
    match = re.search(r"\$([0-9,]+)", text)
    if not match:
        return None
    return int(match.group(1).replace(",", ""))


def parse_beds(text: str) -> Optional[int]:
    if not text:
        return None
    match = re.search(r"(\d+)\s*bed", text.lower())
    if not match:
        return None
    return int(match.group(1))


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def within_criteria(price: Optional[int], beds: Optional[int]) -> bool:
    if price is not None:
        if price < CRITERIA["price_min"] or price > CRITERIA["price_max"]:
            return False
    if beds is not None and beds < CRITERIA["min_beds"]:
        return False
    return True


def parse_zillow(html: str) -> List[Dict]:
    results = []
    soup = BeautifulSoup(html, "html.parser")

    # Try JSON-LD first
    for script in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            data = json.loads(script.string or "")
        except Exception:
            continue
        if isinstance(data, dict) and data.get("@type") == "ItemList":
            for item in data.get("itemListElement", []):
                entity = item.get("item", {})
                link = entity.get("url")
                address = entity.get("name")
                price = parse_price(entity.get("description", ""))
                beds = parse_beds(entity.get("description", ""))
                if not within_criteria(price, beds):
                    continue
                results.append(
                    {
                        "address": address,
                        "price": price,
                        "beds_baths": entity.get("description"),
                        "link": link,
                        "listing_date": datetime.utcnow().strftime("%Y-%m-%d"),
                        "source": "zillow",
                    }
                )

    # Fallback to visible cards
    for card in soup.select("article"):
        link_tag = card.find("a", href=True)
        if not link_tag:
            continue
        link = link_tag["href"]
        if link.startswith("/"):
            link = "https://www.zillow.com" + link
        price = parse_price(card.get_text(" "))
        beds = parse_beds(card.get_text(" "))
        if not within_criteria(price, beds):
            continue
        address = normalize_space(card.get_text(" ")[:120])
        results.append(
            {
                "address": address,
                "price": price,
                "beds_baths": normalize_space(card.get_text(" ")),
                "link": link,
                "listing_date": datetime.utcnow().strftime("%Y-%m-%d"),
                "source": "zillow",
            }
        )
    return results


def parse_apartments(html: str) -> List[Dict]:
    results = []
    soup = BeautifulSoup(html, "html.parser")
    for card in soup.select("article.placard"):
        link_tag = card.find("a", href=True)
        if not link_tag:
            continue
        link = link_tag["href"]
        price_text = card.get_text(" ")
        price = parse_price(price_text)
        beds = parse_beds(price_text)
        if not within_criteria(price, beds):
            continue
        address_tag = card.select_one(".property-address")
        address = normalize_space(address_tag.get_text(" ") if address_tag else "")
        results.append(
            {
                "address": address,
                "price": price,
                "beds_baths": normalize_space(price_text),
                "link": link,
                "listing_date": datetime.utcnow().strftime("%Y-%m-%d"),
                "source": "apartments.com",
            }
        )
    return results


def parse_craigslist(html: str) -> List[Dict]:
    results = []
    soup = BeautifulSoup(html, "html.parser")
    for row in soup.select("li.result-row"):
        link_tag = row.find("a", class_="result-title", href=True)
        if not link_tag:
            continue
        link = link_tag["href"]
        price_tag = row.find("span", class_="result-price")
        price = parse_price(price_tag.get_text(" ") if price_tag else "")
        beds_tag = row.find("span", class_="housing")
        beds = parse_beds(beds_tag.get_text(" ") if beds_tag else "")
        if not within_criteria(price, beds):
            continue
        address = normalize_space(link_tag.get_text(" "))
        date_tag = row.find("time", class_="result-date")
        listing_date = date_tag["datetime"][:10] if date_tag else datetime.utcnow().strftime("%Y-%m-%d")
        results.append(
            {
                "address": address,
                "price": price,
                "beds_baths": normalize_space((beds_tag.get_text(" ") if beds_tag else "") or ""),
                "link": link,
                "listing_date": listing_date,
                "source": "craigslist",
            }
        )
    return results


def build_urls() -> Dict[str, List[str]]:
    urls = {
        "zillow": [],
        "apartments": [],
        "craigslist": [],
    }
    for location in CRITERIA["locations"]:
        zillow_query = location.replace(" ", "-")
        urls["zillow"].append(
            f"https://www.zillow.com/{zillow_query}/rentals/"
        )
        apartments_query = location.replace(" ", "-")
        urls["apartments"].append(
            f"https://www.apartments.com/{apartments_query}/"
        )
        craigslist_query = location.replace(" ", "+")
        urls["craigslist"].append(
            "https://phoenix.craigslist.org/search/apa?query="
            + craigslist_query
            + "&min_price=3000&max_price=5000&min_bedrooms=3&availabilityMode=0"
        )
    return urls


def demo_results() -> List[Dict]:
    today = datetime.utcnow().strftime("%Y-%m-%d")
    return [
        {
            "address": "Demo: 1234 E Example St, Scottsdale, AZ 85254",
            "price": 4200,
            "beds_baths": "4 beds 3 baths",
            "link": "https://example.com/listing/1",
            "listing_date": today,
            "source": "demo",
        },
        {
            "address": "Demo: 9876 N Sample Ave, Phoenix, AZ 85018",
            "price": 3500,
            "beds_baths": "3 beds 2 baths",
            "link": "https://example.com/listing/2",
            "listing_date": today,
            "source": "demo",
        },
    ]


def search(use_craigslist: bool, use_demo: bool) -> List[Dict]:
    urls = build_urls()
    all_results: List[Dict] = []

    for url in urls["zillow"]:
        html = fetch(url)
        if html:
            all_results.extend(parse_zillow(html))

    for url in urls["apartments"]:
        html = fetch(url)
        if html:
            all_results.extend(parse_apartments(html))

    if use_craigslist:
        for url in urls["craigslist"]:
            html = fetch(url)
            if html:
                all_results.extend(parse_craigslist(html))

    if not all_results and use_demo:
        all_results = demo_results()

    return all_results


def report() -> None:
    listings = load_listings()
    if not listings:
        print("No saved listings found.")
        return

    for item in listings:
        print(f"- {item.get('address')} | ${item.get('price')} | {item.get('beds_baths')} | {item.get('link')} | {item.get('listing_date')}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Rental Finder Agent")
    parser.add_argument("--search", action="store_true", help="Search for new listings")
    parser.add_argument("--report", action="store_true", help="Show saved listings")
    parser.add_argument("--with-craigslist", action="store_true", help="Include Craigslist")
    parser.add_argument("--demo", action="store_true", help="Use demo data if scraping fails")

    args = parser.parse_args()

    if not args.search and not args.report:
        parser.print_help()
        return 1

    if args.search:
        existing = load_listings()
        new_items = search(use_craigslist=args.with_craigslist, use_demo=args.demo)
        merged = dedupe(existing, new_items)
        save_listings(merged)
        print(f"Saved {len(merged)} listings (added {len(merged) - len(existing)}).")

    if args.report:
        report()

    return 0


if __name__ == "__main__":
    sys.exit(main())
