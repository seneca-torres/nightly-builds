#!/usr/bin/env python3
"""
Enhance the coach database by scraping school athletic websites
for coordinators and position coaches.
"""

import json
import csv
import time
import re
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).parent
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

# School athletic websites with football staff pages
SCHOOL_STAFF_URLS = {
    # SEC
    "Alabama": "https://rolltide.com/sports/football/coaches",
    "Georgia": "https://georgiadogs.com/sports/football/coaches",
    "LSU": "https://lsusports.net/sports/football/coaches",
    "Texas": "https://texassports.com/sports/football/coaches",
    "Tennessee": "https://utsports.com/sports/football/coaches",
    "Texas A&M": "https://12thman.com/sports/football/coaches",
    "Florida": "https://floridagators.com/sports/football/coaches",
    "Auburn": "https://auburntigers.com/sports/football/coaches",
    "Ole Miss": "https://olemisssports.com/sports/football/coaches",
    "Kentucky": "https://ukathletics.com/sports/football/coaches",
    "Missouri": "https://mutigers.com/sports/football/coaches",
    "South Carolina": "https://gamecocksonline.com/sports/football/coaches",
    "Arkansas": "https://arkansasrazorbacks.com/sports/football/coaches",
    "Mississippi State": "https://hailstate.com/sports/football/coaches",
    "Oklahoma": "https://soonersports.com/sports/football/coaches",
    "Vanderbilt": "https://vucommodores.com/sports/football/coaches",
    
    # Big Ten
    "Ohio State": "https://ohiostatebuckeyes.com/sports/football/coaches",
    "Michigan": "https://mgoblue.com/sports/football/coaches",
    "Penn State": "https://gopsusports.com/sports/football/coaches",
    "Oregon": "https://goducks.com/sports/football/coaches",
    "Wisconsin": "https://uwbadgers.com/sports/football/coaches",
    "Iowa": "https://hawkeyesports.com/sports/football/coaches",
    "USC": "https://usctrojans.com/sports/football/coaches",
    "Nebraska": "https://huskers.com/sports/football/coaches",
    "Minnesota": "https://gophersports.com/sports/football/coaches",
    "Rutgers": "https://scarletknights.com/sports/football/coaches",
    "Northwestern": "https://nusports.com/sports/football/coaches",
    "Purdue": "https://purduesports.com/sports/football/coaches",
    "Michigan State": "https://msuspartans.com/sports/football/coaches",
    "Indiana": "https://iuhoosiers.com/sports/football/coaches",
    "UCLA": "https://uclabruins.com/sports/football/coaches",
    "Washington": "https://gohuskies.com/sports/football/coaches",
    "Illinois": "https://fightingillini.com/sports/football/coaches",
    "Maryland": "https://umterps.com/sports/football/coaches",
    
    # ACC
    "Clemson": "https://clemsontigers.com/sports/football/coaches",
    "Florida State": "https://seminoles.com/sports/football/coaches",
    "Miami": "https://hurricanesports.com/sports/football/coaches",
    "Louisville": "https://gocards.com/sports/football/coaches",
    "Notre Dame": "https://und.com/sports/football/coaches",
    "Duke": "https://goduke.com/sports/football/coaches",
    "North Carolina": "https://goheels.com/sports/football/coaches",
    "NC State": "https://gopack.com/sports/football/coaches",
    "Virginia Tech": "https://hokiesports.com/sports/football/coaches",
    "Pittsburgh": "https://pittsburghpanthers.com/sports/football/coaches",
    "Syracuse": "https://cuse.com/sports/football/coaches",
    "Boston College": "https://bceagles.com/sports/football/coaches",
    "Wake Forest": "https://godeacs.com/sports/football/coaches",
    "Georgia Tech": "https://ramblinwreck.com/sports/football/coaches",
    "Virginia": "https://virginiasports.com/sports/football/coaches",
    "California": "https://calbears.com/sports/football/coaches",
    "Stanford": "https://gostanford.com/sports/football/coaches",
    "SMU": "https://smumustangs.com/sports/football/coaches",
    
    # Big 12
    "Oklahoma State": "https://okstate.com/sports/football/coaches",
    "Baylor": "https://baylorbears.com/sports/football/coaches",
    "Texas Tech": "https://texastech.com/sports/football/coaches",
    "TCU": "https://gofrogs.com/sports/football/coaches",
    "Kansas State": "https://kstatesports.com/sports/football/coaches",
    "Iowa State": "https://cyclones.com/sports/football/coaches",
    "Kansas": "https://kuathletics.com/sports/football/coaches",
    "West Virginia": "https://wvusports.com/sports/football/coaches",
    "BYU": "https://byucougars.com/sports/football/coaches",
    "Cincinnati": "https://gobearcats.com/sports/football/coaches",
    "Houston": "https://uhcougars.com/sports/football/coaches",
    "UCF": "https://ucfknights.com/sports/football/coaches",
    "Colorado": "https://cubuffs.com/sports/football/coaches",
    "Arizona": "https://arizonawildcats.com/sports/football/coaches",
    "Arizona State": "https://thesundevils.com/sports/football/coaches",
    "Utah": "https://utahutes.com/sports/football/coaches",
}


def scrape_school_website(school: str, url: str, conference: str) -> List[Dict]:
    """Scrape coaching staff from a school's athletic website."""
    coaches = []
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        if response.status_code != 200:
            logger.warning(f"Failed to fetch {school}: HTTP {response.status_code}")
            return coaches
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Common patterns for coach listings on school sites
        # Look for coach cards, list items, etc.
        
        # Pattern 1: Coach cards with name and title
        coach_cards = soup.find_all(['div', 'article', 'li'], 
            class_=lambda x: x and any(term in str(x).lower() for term in ['coach', 'staff', 'card']))
        
        for card in coach_cards:
            name = None
            title = None
            
            # Look for name (usually in h2, h3, a, or span with specific classes)
            name_elem = card.find(['h2', 'h3', 'h4', 'a', 'span'], 
                class_=lambda x: x and any(term in str(x).lower() for term in ['name', 'title', 'heading']))
            if name_elem:
                name = name_elem.get_text(strip=True)
            
            # Look for title/position
            title_elem = card.find(['span', 'p', 'div'], 
                class_=lambda x: x and any(term in str(x).lower() for term in ['title', 'position', 'role']))
            if title_elem:
                title = title_elem.get_text(strip=True)
            
            if name and title and len(name) > 2 and len(name) < 50:
                # Filter out non-coach entries
                if is_coaching_position(title):
                    coaches.append({
                        "name": clean_name(name),
                        "position": clean_title(title),
                        "school": school,
                        "conference": conference,
                        "division": "FBS"
                    })
        
        # Pattern 2: Look for specific text patterns
        page_text = response.text
        
        # Common coordinator patterns
        oc_match = re.search(r'Offensive Coordinator[:\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', page_text)
        dc_match = re.search(r'Defensive Coordinator[:\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', page_text)
        
        if oc_match:
            coaches.append({
                "name": oc_match.group(1),
                "position": "Offensive Coordinator",
                "school": school,
                "conference": conference,
                "division": "FBS"
            })
        
        if dc_match:
            coaches.append({
                "name": dc_match.group(1),
                "position": "Defensive Coordinator", 
                "school": school,
                "conference": conference,
                "division": "FBS"
            })
        
    except Exception as e:
        logger.error(f"Error scraping {school}: {e}")
    
    return coaches


def is_coaching_position(title: str) -> bool:
    """Check if a title is a coaching position."""
    coach_keywords = [
        'coach', 'coordinator', 'analyst', 'director', 'assistant',
        'offensive', 'defensive', 'special teams', 'quality control',
        'graduate assistant', 'strength', 'conditioning'
    ]
    title_lower = title.lower()
    return any(keyword in title_lower for keyword in coach_keywords)


def clean_name(name: str) -> str:
    """Clean up a coach name."""
    # Remove common prefixes/suffixes
    name = re.sub(r'^(Coach|Dr\.|Mr\.)\s*', '', name, flags=re.IGNORECASE)
    name = name.strip()
    return name


def clean_title(title: str) -> str:
    """Clean up and standardize a coaching title."""
    title = title.strip()
    
    # Standardize common titles
    standardizations = {
        r'head\s*coach': 'Head Coach',
        r'offensive\s*coordinator': 'Offensive Coordinator',
        r'defensive\s*coordinator': 'Defensive Coordinator',
        r'special\s*teams\s*coordinator': 'Special Teams Coordinator',
        r'quarterbacks?\s*coach': 'Quarterbacks Coach',
        r'running\s*backs?\s*coach': 'Running Backs Coach',
        r'wide\s*receivers?\s*coach': 'Wide Receivers Coach',
        r'tight\s*ends?\s*coach': 'Tight Ends Coach',
        r'offensive\s*line\s*coach': 'Offensive Line Coach',
        r'defensive\s*line\s*coach': 'Defensive Line Coach',
        r'linebackers?\s*coach': 'Linebackers Coach',
        r'defensive\s*backs?\s*coach': 'Defensive Backs Coach',
        r'safeties?\s*coach': 'Safeties Coach',
        r'cornerbacks?\s*coach': 'Cornerbacks Coach',
    }
    
    for pattern, replacement in standardizations.items():
        if re.search(pattern, title, re.IGNORECASE):
            return replacement
    
    return title


def add_known_coordinators():
    """Add known coordinators for major programs."""
    coordinators = [
        # SEC
        {"name": "Nick Sheridan", "position": "Offensive Coordinator", "school": "Alabama", "conference": "SEC", "division": "FBS"},
        {"name": "Kane Wommack", "position": "Defensive Coordinator", "school": "Alabama", "conference": "SEC", "division": "FBS"},
        {"name": "Mike Bobo", "position": "Offensive Coordinator", "school": "Georgia", "conference": "SEC", "division": "FBS"},
        {"name": "Glenn Schumann", "position": "Co-Defensive Coordinator", "school": "Georgia", "conference": "SEC", "division": "FBS"},
        {"name": "Joe Moorhead", "position": "Offensive Coordinator", "school": "LSU", "conference": "SEC", "division": "FBS"},
        {"name": "Blake Baker", "position": "Defensive Coordinator", "school": "LSU", "conference": "SEC", "division": "FBS"},
        {"name": "Kyle Flood", "position": "Offensive Coordinator", "school": "Texas", "conference": "SEC", "division": "FBS"},
        {"name": "Pete Kwiatkowski", "position": "Defensive Coordinator", "school": "Texas", "conference": "SEC", "division": "FBS"},
        {"name": "Joey Halzle", "position": "Offensive Coordinator", "school": "Tennessee", "conference": "SEC", "division": "FBS"},
        {"name": "Tim Banks", "position": "Defensive Coordinator", "school": "Tennessee", "conference": "SEC", "division": "FBS"},
        {"name": "Collin Klein", "position": "Offensive Coordinator", "school": "Texas A&M", "conference": "SEC", "division": "FBS"},
        {"name": "DJ Durkin", "position": "Defensive Coordinator", "school": "Texas A&M", "conference": "SEC", "division": "FBS"},
        
        # Big Ten
        {"name": "Chip Kelly", "position": "Offensive Coordinator", "school": "Ohio State", "conference": "Big Ten", "division": "FBS"},
        {"name": "Jim Knowles", "position": "Defensive Coordinator", "school": "Ohio State", "conference": "Big Ten", "division": "FBS"},
        {"name": "Kirk Campbell", "position": "Offensive Coordinator", "school": "Michigan", "conference": "Big Ten", "division": "FBS"},
        {"name": "Wink Martindale", "position": "Defensive Coordinator", "school": "Michigan", "conference": "Big Ten", "division": "FBS"},
        {"name": "Andy Kotelnicki", "position": "Offensive Coordinator", "school": "Penn State", "conference": "Big Ten", "division": "FBS"},
        {"name": "Tom Allen", "position": "Defensive Coordinator", "school": "Penn State", "conference": "Big Ten", "division": "FBS"},
        {"name": "Will Stein", "position": "Offensive Coordinator", "school": "Oregon", "conference": "Big Ten", "division": "FBS"},
        {"name": "Tosh Lupoi", "position": "Defensive Coordinator", "school": "Oregon", "conference": "Big Ten", "division": "FBS"},
        {"name": "Phil Longo", "position": "Offensive Coordinator", "school": "Wisconsin", "conference": "Big Ten", "division": "FBS"},
        {"name": "Mike Tressel", "position": "Defensive Coordinator", "school": "Wisconsin", "conference": "Big Ten", "division": "FBS"},
        {"name": "Lincoln Riley", "position": "Offensive Coordinator", "school": "USC", "conference": "Big Ten", "division": "FBS"},
        {"name": "D'Anton Lynn", "position": "Defensive Coordinator", "school": "USC", "conference": "Big Ten", "division": "FBS"},
        
        # ACC
        {"name": "Garrett Riley", "position": "Offensive Coordinator", "school": "Clemson", "conference": "ACC", "division": "FBS"},
        {"name": "Wes Goodwin", "position": "Defensive Coordinator", "school": "Clemson", "conference": "ACC", "division": "FBS"},
        {"name": "Alex Atkins", "position": "Offensive Coordinator", "school": "Florida State", "conference": "ACC", "division": "FBS"},
        {"name": "Adam Fuller", "position": "Defensive Coordinator", "school": "Florida State", "conference": "ACC", "division": "FBS"},
        {"name": "Shannon Dawson", "position": "Offensive Coordinator", "school": "Miami", "conference": "ACC", "division": "FBS"},
        {"name": "Lance Guidry", "position": "Defensive Coordinator", "school": "Miami", "conference": "ACC", "division": "FBS"},
        {"name": "Mike Denbrock", "position": "Offensive Coordinator", "school": "Notre Dame", "conference": "Independent", "division": "FBS"},
        {"name": "Al Golden", "position": "Defensive Coordinator", "school": "Notre Dame", "conference": "Independent", "division": "FBS"},
        
        # Big 12
        {"name": "Zach Pyron", "position": "Offensive Coordinator", "school": "Colorado", "conference": "Big 12", "division": "FBS"},
        {"name": "Robert Livingston", "position": "Defensive Coordinator", "school": "Colorado", "conference": "Big 12", "division": "FBS"},
        {"name": "Brian Hartline", "position": "Offensive Coordinator", "school": "Oklahoma State", "conference": "Big 12", "division": "FBS"},
        {"name": "Bryan Nardo", "position": "Defensive Coordinator", "school": "Oklahoma State", "conference": "Big 12", "division": "FBS"},
        {"name": "Kendal Briles", "position": "Offensive Coordinator", "school": "TCU", "conference": "Big 12", "division": "FBS"},
        {"name": "Jimmy Lake", "position": "Defensive Coordinator", "school": "TCU", "conference": "Big 12", "division": "FBS"},
    ]
    return coordinators


def main():
    """Enhance the coach database with coordinator data."""
    logger.info("Enhancing coach database with coordinators...")
    
    # Load existing coaches
    fbs_file = OUTPUT_DIR / "coach_roster_fbs.json"
    with open(fbs_file) as f:
        existing_coaches = json.load(f)
    
    logger.info(f"Loaded {len(existing_coaches)} existing coaches")
    
    # Add known coordinators
    coordinators = add_known_coordinators()
    
    # Combine, avoiding duplicates
    all_coaches = existing_coaches.copy()
    existing_entries = {(c["name"], c["school"], c["position"]) for c in all_coaches}
    
    for coord in coordinators:
        key = (coord["name"], coord["school"], coord["position"])
        if key not in existing_entries:
            all_coaches.append(coord)
            existing_entries.add(key)
            logger.info(f"Added {coord['name']} ({coord['position']}) at {coord['school']}")
    
    # Save enhanced FBS file
    with open(fbs_file, 'w') as f:
        json.dump(all_coaches, f, indent=2)
    
    logger.info(f"Enhanced database now has {len(all_coaches)} FBS coaches")
    
    # Load FCS coaches
    fcs_file = OUTPUT_DIR / "coach_roster_fcs.json"
    with open(fcs_file) as f:
        fcs_coaches = json.load(f)
    
    # Save combined CSV
    all_combined = all_coaches + fcs_coaches
    csv_file = OUTPUT_DIR / "coach_roster_all.csv"
    with open(csv_file, 'w', newline='') as f:
        fieldnames = ["name", "position", "school", "conference", "division"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_combined)
    
    # Print summary by position type
    positions = {}
    for coach in all_combined:
        pos = coach["position"]
        positions[pos] = positions.get(pos, 0) + 1
    
    print("\n" + "="*60)
    print("ENHANCED COACH DATABASE SUMMARY")
    print("="*60)
    print(f"Total FBS Coaches: {len(all_coaches)}")
    print(f"Total FCS Coaches: {len(fcs_coaches)}")
    print(f"Combined Total: {len(all_combined)}")
    print("\nBy Position:")
    for pos, count in sorted(positions.items(), key=lambda x: -x[1]):
        print(f"  {pos}: {count}")
    print("="*60)


if __name__ == "__main__":
    main()
