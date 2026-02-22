# D1 Football Coach Database

A comprehensive roster of NCAA Division I football coaching staffs (FBS + FCS).

## Overview

This database contains coaching staff information for all ~260 D1 football programs:
- **136 FBS schools** (Power 4 + Group of 5 + Independents)
- **~130 FCS schools** (Big Sky, CAA, Ivy, MVFC, SWAC, etc.)

## Data Files

| File | Description |
|------|-------------|
| `coach_roster_fbs.json` | FBS coaches in JSON format |
| `coach_roster_fcs.json` | FCS coaches in JSON format |
| `coach_roster_all.csv` | All coaches combined (CSV) |
| `scraper.py` | Reusable scraper script |
| `progress.json` | Scraping progress/state |

## Data Schema

Each coach record contains:

```json
{
  "name": "Kirby Smart",
  "position": "Head Coach",
  "school": "Georgia",
  "conference": "SEC",
  "division": "FBS"
}
```

## Conferences Covered

### FBS (136 teams)
- **SEC** (16): Alabama, Arkansas, Auburn, Florida, Georgia, Kentucky, LSU, Mississippi State, Missouri, Oklahoma, Ole Miss, South Carolina, Tennessee, Texas, Texas A&M, Vanderbilt
- **Big Ten** (18): Illinois, Indiana, Iowa, Maryland, Michigan, Michigan State, Minnesota, Nebraska, Northwestern, Ohio State, Oregon, Penn State, Purdue, Rutgers, UCLA, USC, Washington, Wisconsin
- **Big 12** (16): Arizona, Arizona State, Baylor, BYU, Cincinnati, Colorado, Houston, Iowa State, Kansas, Kansas State, Oklahoma State, TCU, Texas Tech, UCF, Utah, West Virginia
- **ACC** (17): Boston College, California, Clemson, Duke, Florida State, Georgia Tech, Louisville, Miami, NC State, North Carolina, Pittsburgh, SMU, Stanford, Syracuse, Virginia, Virginia Tech, Wake Forest
- **American** (14): Army, Charlotte, East Carolina, FAU, Memphis, Navy, North Texas, Rice, South Florida, Temple, Tulane, Tulsa, UAB, UTSA
- **Mountain West** (12): Air Force, Boise State, Colorado State, Fresno State, Hawaii, Nevada, New Mexico, San Diego State, San Jose State, UNLV, Utah State, Wyoming
- **MAC** (12): Akron, Ball State, Bowling Green, Buffalo, Central Michigan, Eastern Michigan, Kent State, Miami (OH), Northern Illinois, Ohio, Toledo, Western Michigan
- **Sun Belt** (14): Appalachian State, Arkansas State, Coastal Carolina, Georgia Southern, Georgia State, James Madison, Louisiana, Marshall, Old Dominion, South Alabama, Southern Miss, Texas State, Troy, ULM
- **Conference USA** (12): Delaware, FIU, Jacksonville State, Kennesaw State, Liberty, Louisiana Tech, Middle Tennessee, Missouri State, New Mexico State, Sam Houston, UTEP, Western Kentucky
- **Pac-12** (2): Oregon State, Washington State
- **Independent** (3): Notre Dame, UConn, UMass

### FCS (~130 teams)
- Big Sky, CAA Football, Ivy League, MEAC, MVFC, NEC, OVC-Big South, Patriot League, Pioneer Football League, Southern Conference, Southland, SWAC, United Athletic Conference

## Usage

### Run the scraper

```bash
cd ~/clawd/nightly-builds/coach-database
python3 scraper.py
```

### Load data in Python

```python
import json
import csv

# Load FBS coaches
with open('coach_roster_fbs.json') as f:
    fbs_coaches = json.load(f)

# Load all coaches from CSV
with open('coach_roster_all.csv') as f:
    reader = csv.DictReader(f)
    all_coaches = list(reader)
```

### Query examples

```python
# Find all SEC head coaches
sec_hcs = [c for c in fbs_coaches if c['conference'] == 'SEC']

# Find all coaches at a specific school
georgia_staff = [c for c in all_coaches if c['school'] == 'Georgia']
```

## Data Sources

- School athletic websites (primary)
- ESPN team pages
- 247Sports coaching pages
- Wikipedia conference/team lists
- Manual verification for head coaches

## Updates

The database is designed to be re-run to capture coaching changes. Run `scraper.py` periodically to refresh data.

## Accuracy Notes

- Head coach data is manually verified and highly accurate
- Coordinator/position coach data may vary in completeness
- Some FCS schools have limited online coaching information
- Data reflects the 2024-2025 season

## Last Updated

2026-01-29

---

*Part of the Clawd nightly-builds collection*
