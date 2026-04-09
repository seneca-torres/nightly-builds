Rental Finder Agent

Prototype rental finder that searches Zillow, Apartments.com, and optionally Craigslist for rentals that match:
- Scottsdale 85254 or Arcadia area
- 3+ bedrooms
- $3000–$5000/month
- 1-year lease
- Availability: end of March or mid-April 2026 (informational; not enforced by most sites)

Setup
- Python 3
- Install dependencies:
  - `pip install requests beautifulsoup4`

Usage
- Search and save listings:
  - `python rental_finder.py --search`
- Search including Craigslist:
  - `python rental_finder.py --search --with-craigslist`
- Use demo results if scraping is blocked or returns nothing:
  - `python rental_finder.py --search --demo`
- Show saved listings:
  - `python rental_finder.py --report`

Notes
- Results are saved to `listings.json` with URL-based deduplication.
- Scraping may be blocked; the tool handles errors and can fall back to demo data.
- This is a prototype: selectors may need adjustment if site layouts change.
