#!/usr/bin/env python3
"""
College Football Coach Contract Scraper
Scrapes coach salary/contract data from USA Today's salary database.

Data source: https://sportsdata.usatoday.com/ncaa/salaries/football/coach
"""

import json
import csv
import time
import re
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

# Respectful scraping settings
USER_AGENT = "Mozilla/5.0 (compatible; CoachContractScraper/1.0; Educational Research)"
RATE_LIMIT_SECONDS = 2


def parse_money(value: str) -> int | None:
    """Parse money string like '$13,282,580' to integer cents."""
    if not value or value == "-":
        return None
    # Remove $, *, commas and convert to int
    cleaned = re.sub(r'[\$,\*]', '', value.strip())
    try:
        return int(float(cleaned))
    except ValueError:
        return None


def scrape_usa_today_salaries(headless: bool = True) -> list[dict]:
    """
    Scrape coach salary data from USA Today's database.
    Returns list of coach contract dictionaries.
    """
    coaches = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(user_agent=USER_AGENT)
        page = context.new_page()
        
        print("📊 Fetching USA Today coach salaries...")
        page.goto("https://sportsdata.usatoday.com/ncaa/salaries/football/coach")
        
        # Wait for table to load
        page.wait_for_selector("table", timeout=15000)
        time.sleep(RATE_LIMIT_SECONDS)  # Rate limiting
        
        # Get all table rows
        rows = page.query_selector_all("table tbody tr")
        
        for row in rows:
            cells = row.query_selector_all("td")
            if len(cells) < 9:
                continue
            
            try:
                coach = {
                    "rank": int(cells[0].inner_text().strip()) if cells[0].inner_text().strip().isdigit() else None,
                    "coach_name": cells[1].inner_text().strip().replace("*", ""),
                    "school": cells[2].inner_text().strip(),
                    "total_pay": parse_money(cells[3].inner_text()),
                    "conference": cells[4].inner_text().strip(),
                    "school_pay": parse_money(cells[5].inner_text()),
                    "max_bonus": parse_money(cells[6].inner_text()),
                    "bonuses_paid_2024_25": parse_money(cells[7].inner_text()),
                    "buyout_owed_dec_2025": parse_money(cells[8].inner_text()),
                    "source": "USA Today Coaches Database",
                    "source_url": "https://sportsdata.usatoday.com/ncaa/salaries/football/coach",
                    "scraped_at": datetime.utcnow().isoformat() + "Z"
                }
                coaches.append(coach)
                print(f"  ✓ {coach['coach_name']} ({coach['school']}): ${coach['total_pay']:,}" if coach['total_pay'] else f"  ✓ {coach['coach_name']} ({coach['school']}): -")
            except Exception as e:
                print(f"  ⚠ Error parsing row: {e}")
                continue
        
        browser.close()
    
    print(f"\n✅ Scraped {len(coaches)} coaches")
    return coaches


def save_to_json(coaches: list[dict], filepath: Path) -> None:
    """Save coaches to JSON file."""
    with open(filepath, 'w') as f:
        json.dump({
            "metadata": {
                "source": "USA Today NCAA Football Coach Salaries",
                "url": "https://sportsdata.usatoday.com/ncaa/salaries/football/coach",
                "scraped_at": datetime.utcnow().isoformat() + "Z",
                "total_coaches": len(coaches),
                "season": "2025"
            },
            "coaches": coaches
        }, f, indent=2)
    print(f"💾 Saved JSON to {filepath}")


def save_to_csv(coaches: list[dict], filepath: Path) -> None:
    """Save coaches to CSV file."""
    if not coaches:
        return
    
    fieldnames = [
        "rank", "coach_name", "school", "conference", 
        "total_pay", "school_pay", "max_bonus", 
        "bonuses_paid_2024_25", "buyout_owed_dec_2025",
        "source", "source_url", "scraped_at"
    ]
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(coaches)
    
    print(f"💾 Saved CSV to {filepath}")


def main():
    """Main entry point."""
    output_dir = Path(__file__).parent / "data"
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d")
    
    print("🏈 College Football Coach Contract Scraper")
    print("=" * 50)
    
    # Scrape USA Today data
    coaches = scrape_usa_today_salaries()
    
    if coaches:
        # Save outputs
        save_to_json(coaches, output_dir / f"coach_contracts_{timestamp}.json")
        save_to_csv(coaches, output_dir / f"coach_contracts_{timestamp}.csv")
        
        # Also save a "latest" version
        save_to_json(coaches, output_dir / "coach_contracts_latest.json")
        save_to_csv(coaches, output_dir / "coach_contracts_latest.csv")
        
        # Summary stats
        total_pay = sum(c['total_pay'] for c in coaches if c['total_pay'])
        avg_pay = total_pay / len([c for c in coaches if c['total_pay']])
        
        print("\n📈 Summary:")
        print(f"   Total coaches: {len(coaches)}")
        print(f"   With salary data: {len([c for c in coaches if c['total_pay']])}")
        print(f"   Average salary: ${avg_pay:,.0f}")
        print(f"   Highest paid: {coaches[0]['coach_name']} (${coaches[0]['total_pay']:,})")
    else:
        print("❌ No data scraped")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
