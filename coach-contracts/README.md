# College Football Coach Contract Scraper

Scrapes FBS head coach salary and contract data from public sources.

## Data Points Captured

- **Coach name**
- **School**  
- **Total pay** (annual compensation)
- **School pay** (base from school)
- **Conference**
- **Maximum bonus** available
- **Bonuses paid** (2024-25 season)
- **Buyout owed** (as of Dec 1, 2025)

## Sources

| Source | URL | Status |
|--------|-----|--------|
| USA Today Coach Salaries | https://sportsdata.usatoday.com/ncaa/salaries/football/coach | ✅ Working |
| Public university databases | Various | 🔜 Future |
| ESPN/Athletic archives | Manual | 📋 Notes only |

## Setup

```bash
# Create virtual environment (if needed)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install playwright
playwright install chromium
```

## Usage

```bash
# Run the scraper
python scraper.py

# Output will be in data/ directory:
# - coach_contracts_YYYYMMDD.json
# - coach_contracts_YYYYMMDD.csv  
# - coach_contracts_latest.json (symlink to latest)
# - coach_contracts_latest.csv
```

## Output Format

### JSON Structure
```json
{
  "metadata": {
    "source": "USA Today NCAA Football Coach Salaries",
    "url": "https://sportsdata.usatoday.com/ncaa/salaries/football/coach",
    "scraped_at": "2025-01-29T14:15:00Z",
    "total_coaches": 136,
    "season": "2025"
  },
  "coaches": [
    {
      "rank": 1,
      "coach_name": "Kirby Smart",
      "school": "Georgia", 
      "total_pay": 13282580,
      "conference": "SEC",
      "school_pay": 13003000,
      "max_bonus": 1775000,
      "bonuses_paid_2024_25": 800000,
      "buyout_owed_dec_2025": 105107583
    }
  ]
}
```

## Scraping Policy

- **Rate limiting**: 2 second delay between requests
- **User-Agent**: Identifies as educational research tool
- **Respectful**: Only scrapes public data, no login bypass

## Notes

### Sources that are hard to scrape:
- **ESPN**: Paywall + dynamic loading, requires subscription
- **The Athletic**: Subscription-only content
- **Individual contracts**: Often PDFs via FOIA requests

### Data limitations:
- Private school salaries (Notre Dame, USC, etc.) often marked with `*` indicating estimates
- Some buyout figures unavailable
- Contract term/length not in main table (available on individual coach pages)

## Future Enhancements

- [ ] Scrape individual coach pages for contract term details
- [ ] Add historical data comparison
- [ ] Track assistant coordinator salaries
- [ ] FOIA request tracker for actual contracts
