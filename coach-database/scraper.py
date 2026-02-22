#!/usr/bin/env python3
"""
D1 Football Coach Database Scraper
Scrapes coaching staff from all FBS and FCS football programs.
"""

import json
import csv
import time
import re
import os
from pathlib import Path
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Output directory
OUTPUT_DIR = Path(__file__).parent
PROGRESS_FILE = OUTPUT_DIR / "progress.json"

# Request headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

# FBS Teams with ESPN IDs and conferences (2025 season)
FBS_TEAMS = [
    # ACC
    {"school": "Boston College", "conference": "ACC", "espn_id": "103"},
    {"school": "California", "conference": "ACC", "espn_id": "25"},
    {"school": "Clemson", "conference": "ACC", "espn_id": "228"},
    {"school": "Duke", "conference": "ACC", "espn_id": "150"},
    {"school": "Florida State", "conference": "ACC", "espn_id": "52"},
    {"school": "Georgia Tech", "conference": "ACC", "espn_id": "59"},
    {"school": "Louisville", "conference": "ACC", "espn_id": "97"},
    {"school": "Miami", "conference": "ACC", "espn_id": "2390"},
    {"school": "NC State", "conference": "ACC", "espn_id": "152"},
    {"school": "North Carolina", "conference": "ACC", "espn_id": "153"},
    {"school": "Pittsburgh", "conference": "ACC", "espn_id": "221"},
    {"school": "SMU", "conference": "ACC", "espn_id": "2567"},
    {"school": "Stanford", "conference": "ACC", "espn_id": "24"},
    {"school": "Syracuse", "conference": "ACC", "espn_id": "183"},
    {"school": "Virginia", "conference": "ACC", "espn_id": "258"},
    {"school": "Virginia Tech", "conference": "ACC", "espn_id": "259"},
    {"school": "Wake Forest", "conference": "ACC", "espn_id": "154"},
    
    # American Athletic Conference
    {"school": "Army", "conference": "American", "espn_id": "349"},
    {"school": "Charlotte", "conference": "American", "espn_id": "2429"},
    {"school": "East Carolina", "conference": "American", "espn_id": "151"},
    {"school": "Florida Atlantic", "conference": "American", "espn_id": "2226"},
    {"school": "Memphis", "conference": "American", "espn_id": "235"},
    {"school": "Navy", "conference": "American", "espn_id": "2426"},
    {"school": "North Texas", "conference": "American", "espn_id": "249"},
    {"school": "Rice", "conference": "American", "espn_id": "242"},
    {"school": "South Florida", "conference": "American", "espn_id": "58"},
    {"school": "Temple", "conference": "American", "espn_id": "218"},
    {"school": "Tulane", "conference": "American", "espn_id": "2655"},
    {"school": "Tulsa", "conference": "American", "espn_id": "202"},
    {"school": "UAB", "conference": "American", "espn_id": "5"},
    {"school": "UTSA", "conference": "American", "espn_id": "2636"},
    
    # Big 12
    {"school": "Arizona", "conference": "Big 12", "espn_id": "12"},
    {"school": "Arizona State", "conference": "Big 12", "espn_id": "9"},
    {"school": "Baylor", "conference": "Big 12", "espn_id": "239"},
    {"school": "BYU", "conference": "Big 12", "espn_id": "252"},
    {"school": "Cincinnati", "conference": "Big 12", "espn_id": "2132"},
    {"school": "Colorado", "conference": "Big 12", "espn_id": "38"},
    {"school": "Houston", "conference": "Big 12", "espn_id": "248"},
    {"school": "Iowa State", "conference": "Big 12", "espn_id": "66"},
    {"school": "Kansas", "conference": "Big 12", "espn_id": "2305"},
    {"school": "Kansas State", "conference": "Big 12", "espn_id": "2306"},
    {"school": "Oklahoma State", "conference": "Big 12", "espn_id": "197"},
    {"school": "TCU", "conference": "Big 12", "espn_id": "2628"},
    {"school": "Texas Tech", "conference": "Big 12", "espn_id": "2641"},
    {"school": "UCF", "conference": "Big 12", "espn_id": "2116"},
    {"school": "Utah", "conference": "Big 12", "espn_id": "254"},
    {"school": "West Virginia", "conference": "Big 12", "espn_id": "277"},
    
    # Big Ten
    {"school": "Illinois", "conference": "Big Ten", "espn_id": "356"},
    {"school": "Indiana", "conference": "Big Ten", "espn_id": "84"},
    {"school": "Iowa", "conference": "Big Ten", "espn_id": "2294"},
    {"school": "Maryland", "conference": "Big Ten", "espn_id": "120"},
    {"school": "Michigan", "conference": "Big Ten", "espn_id": "130"},
    {"school": "Michigan State", "conference": "Big Ten", "espn_id": "127"},
    {"school": "Minnesota", "conference": "Big Ten", "espn_id": "135"},
    {"school": "Nebraska", "conference": "Big Ten", "espn_id": "158"},
    {"school": "Northwestern", "conference": "Big Ten", "espn_id": "77"},
    {"school": "Ohio State", "conference": "Big Ten", "espn_id": "194"},
    {"school": "Oregon", "conference": "Big Ten", "espn_id": "2483"},
    {"school": "Penn State", "conference": "Big Ten", "espn_id": "213"},
    {"school": "Purdue", "conference": "Big Ten", "espn_id": "2509"},
    {"school": "Rutgers", "conference": "Big Ten", "espn_id": "164"},
    {"school": "UCLA", "conference": "Big Ten", "espn_id": "26"},
    {"school": "USC", "conference": "Big Ten", "espn_id": "30"},
    {"school": "Washington", "conference": "Big Ten", "espn_id": "264"},
    {"school": "Wisconsin", "conference": "Big Ten", "espn_id": "275"},
    
    # Conference USA
    {"school": "Delaware", "conference": "Conference USA", "espn_id": "48"},
    {"school": "FIU", "conference": "Conference USA", "espn_id": "2229"},
    {"school": "Jacksonville State", "conference": "Conference USA", "espn_id": "55"},
    {"school": "Kennesaw State", "conference": "Conference USA", "espn_id": "338"},
    {"school": "Liberty", "conference": "Conference USA", "espn_id": "2335"},
    {"school": "Louisiana Tech", "conference": "Conference USA", "espn_id": "2348"},
    {"school": "Middle Tennessee", "conference": "Conference USA", "espn_id": "2393"},
    {"school": "Missouri State", "conference": "Conference USA", "espn_id": "2623"},
    {"school": "New Mexico State", "conference": "Conference USA", "espn_id": "166"},
    {"school": "Sam Houston", "conference": "Conference USA", "espn_id": "2534"},
    {"school": "UTEP", "conference": "Conference USA", "espn_id": "2638"},
    {"school": "Western Kentucky", "conference": "Conference USA", "espn_id": "98"},
    
    # Independent
    {"school": "Notre Dame", "conference": "Independent", "espn_id": "87"},
    {"school": "UConn", "conference": "Independent", "espn_id": "41"},
    {"school": "UMass", "conference": "MAC", "espn_id": "113"},
    
    # Mountain West
    {"school": "Air Force", "conference": "Mountain West", "espn_id": "2005"},
    {"school": "Boise State", "conference": "Mountain West", "espn_id": "68"},
    {"school": "Colorado State", "conference": "Mountain West", "espn_id": "36"},
    {"school": "Fresno State", "conference": "Mountain West", "espn_id": "278"},
    {"school": "Hawaii", "conference": "Mountain West", "espn_id": "62"},
    {"school": "Nevada", "conference": "Mountain West", "espn_id": "2440"},
    {"school": "New Mexico", "conference": "Mountain West", "espn_id": "167"},
    {"school": "San Diego State", "conference": "Mountain West", "espn_id": "21"},
    {"school": "San Jose State", "conference": "Mountain West", "espn_id": "23"},
    {"school": "UNLV", "conference": "Mountain West", "espn_id": "2439"},
    {"school": "Utah State", "conference": "Mountain West", "espn_id": "328"},
    {"school": "Wyoming", "conference": "Mountain West", "espn_id": "2751"},
    
    # MAC
    {"school": "Akron", "conference": "MAC", "espn_id": "2006"},
    {"school": "Ball State", "conference": "MAC", "espn_id": "2050"},
    {"school": "Bowling Green", "conference": "MAC", "espn_id": "189"},
    {"school": "Buffalo", "conference": "MAC", "espn_id": "2084"},
    {"school": "Central Michigan", "conference": "MAC", "espn_id": "2117"},
    {"school": "Eastern Michigan", "conference": "MAC", "espn_id": "2199"},
    {"school": "Kent State", "conference": "MAC", "espn_id": "2309"},
    {"school": "Miami (OH)", "conference": "MAC", "espn_id": "193"},
    {"school": "Northern Illinois", "conference": "MAC", "espn_id": "2459"},
    {"school": "Ohio", "conference": "MAC", "espn_id": "195"},
    {"school": "Toledo", "conference": "MAC", "espn_id": "2649"},
    {"school": "Western Michigan", "conference": "MAC", "espn_id": "2711"},
    
    # Pac-12 (remaining)
    {"school": "Oregon State", "conference": "Pac-12", "espn_id": "204"},
    {"school": "Washington State", "conference": "Pac-12", "espn_id": "265"},
    
    # SEC
    {"school": "Alabama", "conference": "SEC", "espn_id": "333"},
    {"school": "Arkansas", "conference": "SEC", "espn_id": "8"},
    {"school": "Auburn", "conference": "SEC", "espn_id": "2"},
    {"school": "Florida", "conference": "SEC", "espn_id": "57"},
    {"school": "Georgia", "conference": "SEC", "espn_id": "61"},
    {"school": "Kentucky", "conference": "SEC", "espn_id": "96"},
    {"school": "LSU", "conference": "SEC", "espn_id": "99"},
    {"school": "Mississippi State", "conference": "SEC", "espn_id": "344"},
    {"school": "Missouri", "conference": "SEC", "espn_id": "142"},
    {"school": "Oklahoma", "conference": "SEC", "espn_id": "201"},
    {"school": "Ole Miss", "conference": "SEC", "espn_id": "145"},
    {"school": "South Carolina", "conference": "SEC", "espn_id": "2579"},
    {"school": "Tennessee", "conference": "SEC", "espn_id": "2633"},
    {"school": "Texas", "conference": "SEC", "espn_id": "251"},
    {"school": "Texas A&M", "conference": "SEC", "espn_id": "245"},
    {"school": "Vanderbilt", "conference": "SEC", "espn_id": "238"},
    
    # Sun Belt
    {"school": "Appalachian State", "conference": "Sun Belt", "espn_id": "2026"},
    {"school": "Arkansas State", "conference": "Sun Belt", "espn_id": "2032"},
    {"school": "Coastal Carolina", "conference": "Sun Belt", "espn_id": "324"},
    {"school": "Georgia Southern", "conference": "Sun Belt", "espn_id": "290"},
    {"school": "Georgia State", "conference": "Sun Belt", "espn_id": "2247"},
    {"school": "James Madison", "conference": "Sun Belt", "espn_id": "256"},
    {"school": "Louisiana", "conference": "Sun Belt", "espn_id": "309"},
    {"school": "Marshall", "conference": "Sun Belt", "espn_id": "276"},
    {"school": "Old Dominion", "conference": "Sun Belt", "espn_id": "295"},
    {"school": "South Alabama", "conference": "Sun Belt", "espn_id": "6"},
    {"school": "Southern Miss", "conference": "Sun Belt", "espn_id": "2572"},
    {"school": "Texas State", "conference": "Sun Belt", "espn_id": "326"},
    {"school": "Troy", "conference": "Sun Belt", "espn_id": "2653"},
    {"school": "ULM", "conference": "Sun Belt", "espn_id": "2433"},
]

# FCS Teams (key ones with ESPN IDs)
FCS_TEAMS = [
    # Big Sky
    {"school": "Cal Poly", "conference": "Big Sky", "espn_id": "13"},
    {"school": "Eastern Washington", "conference": "Big Sky", "espn_id": "331"},
    {"school": "Idaho", "conference": "Big Sky", "espn_id": "70"},
    {"school": "Idaho State", "conference": "Big Sky", "espn_id": "304"},
    {"school": "Montana", "conference": "Big Sky", "espn_id": "149"},
    {"school": "Montana State", "conference": "Big Sky", "espn_id": "147"},
    {"school": "Northern Arizona", "conference": "Big Sky", "espn_id": "2464"},
    {"school": "Northern Colorado", "conference": "Big Sky", "espn_id": "2458"},
    {"school": "Portland State", "conference": "Big Sky", "espn_id": "2502"},
    {"school": "Sacramento State", "conference": "Big Sky", "espn_id": "16"},
    {"school": "UC Davis", "conference": "Big Sky", "espn_id": "302"},
    {"school": "Weber State", "conference": "Big Sky", "espn_id": "2692"},
    
    # CAA Football
    {"school": "Albany", "conference": "CAA", "espn_id": "399"},
    {"school": "Bryant", "conference": "CAA", "espn_id": "2803"},
    {"school": "Campbell", "conference": "CAA", "espn_id": "2097"},
    {"school": "Elon", "conference": "CAA", "espn_id": "2210"},
    {"school": "Hampton", "conference": "CAA", "espn_id": "2272"},
    {"school": "Maine", "conference": "CAA", "espn_id": "311"},
    {"school": "Monmouth", "conference": "CAA", "espn_id": "2405"},
    {"school": "New Hampshire", "conference": "CAA", "espn_id": "160"},
    {"school": "North Carolina A&T", "conference": "CAA", "espn_id": "2448"},
    {"school": "Rhode Island", "conference": "CAA", "espn_id": "227"},
    {"school": "Stony Brook", "conference": "CAA", "espn_id": "2619"},
    {"school": "Towson", "conference": "CAA", "espn_id": "119"},
    {"school": "Villanova", "conference": "CAA", "espn_id": "222"},
    {"school": "William & Mary", "conference": "CAA", "espn_id": "2729"},
    
    # Ivy League
    {"school": "Brown", "conference": "Ivy", "espn_id": "225"},
    {"school": "Columbia", "conference": "Ivy", "espn_id": "171"},
    {"school": "Cornell", "conference": "Ivy", "espn_id": "172"},
    {"school": "Dartmouth", "conference": "Ivy", "espn_id": "159"},
    {"school": "Harvard", "conference": "Ivy", "espn_id": "108"},
    {"school": "Penn", "conference": "Ivy", "espn_id": "219"},
    {"school": "Princeton", "conference": "Ivy", "espn_id": "163"},
    {"school": "Yale", "conference": "Ivy", "espn_id": "43"},
    
    # MEAC
    {"school": "Delaware State", "conference": "MEAC", "espn_id": "2169"},
    {"school": "Howard", "conference": "MEAC", "espn_id": "47"},
    {"school": "Morgan State", "conference": "MEAC", "espn_id": "2415"},
    {"school": "Norfolk State", "conference": "MEAC", "espn_id": "2450"},
    {"school": "North Carolina Central", "conference": "MEAC", "espn_id": "2428"},
    {"school": "South Carolina State", "conference": "MEAC", "espn_id": "2569"},
    
    # Missouri Valley Football Conference (MVFC)
    {"school": "Illinois State", "conference": "MVFC", "espn_id": "2287"},
    {"school": "Indiana State", "conference": "MVFC", "espn_id": "282"},
    {"school": "Murray State", "conference": "MVFC", "espn_id": "93"},
    {"school": "North Dakota", "conference": "MVFC", "espn_id": "155"},
    {"school": "North Dakota State", "conference": "MVFC", "espn_id": "2449"},
    {"school": "Northern Iowa", "conference": "MVFC", "espn_id": "2460"},
    {"school": "South Dakota", "conference": "MVFC", "espn_id": "233"},
    {"school": "South Dakota State", "conference": "MVFC", "espn_id": "2571"},
    {"school": "Southern Illinois", "conference": "MVFC", "espn_id": "79"},
    {"school": "Youngstown State", "conference": "MVFC", "espn_id": "2754"},
    
    # NEC
    {"school": "Central Connecticut", "conference": "NEC", "espn_id": "2115"},
    {"school": "Duquesne", "conference": "NEC", "espn_id": "2184"},
    {"school": "LIU", "conference": "NEC", "espn_id": "2344"},
    {"school": "Robert Morris", "conference": "NEC", "espn_id": "2523"},
    {"school": "Sacred Heart", "conference": "NEC", "espn_id": "2529"},
    {"school": "Wagner", "conference": "NEC", "espn_id": "2681"},
    
    # OVC-Big South
    {"school": "Charleston Southern", "conference": "OVC-Big South", "espn_id": "2127"},
    {"school": "Eastern Illinois", "conference": "OVC-Big South", "espn_id": "2197"},
    {"school": "Eastern Kentucky", "conference": "OVC-Big South", "espn_id": "2198"},
    {"school": "Gardner-Webb", "conference": "OVC-Big South", "espn_id": "2241"},
    {"school": "Southeast Missouri State", "conference": "OVC-Big South", "espn_id": "2546"},
    {"school": "Tennessee State", "conference": "OVC-Big South", "espn_id": "2634"},
    {"school": "Tennessee Tech", "conference": "OVC-Big South", "espn_id": "2635"},
    {"school": "UT Martin", "conference": "OVC-Big South", "espn_id": "2630"},
    {"school": "Western Illinois", "conference": "OVC-Big South", "espn_id": "2710"},
    
    # Patriot League
    {"school": "Bucknell", "conference": "Patriot", "espn_id": "2083"},
    {"school": "Colgate", "conference": "Patriot", "espn_id": "2142"},
    {"school": "Fordham", "conference": "Patriot", "espn_id": "2230"},
    {"school": "Georgetown", "conference": "Patriot", "espn_id": "46"},
    {"school": "Holy Cross", "conference": "Patriot", "espn_id": "107"},
    {"school": "Lafayette", "conference": "Patriot", "espn_id": "322"},
    {"school": "Lehigh", "conference": "Patriot", "espn_id": "2329"},
    {"school": "Richmond", "conference": "Patriot", "espn_id": "257"},
    
    # Pioneer Football League
    {"school": "Butler", "conference": "PFL", "espn_id": "2086"},
    {"school": "Davidson", "conference": "PFL", "espn_id": "2166"},
    {"school": "Dayton", "conference": "PFL", "espn_id": "2168"},
    {"school": "Drake", "conference": "PFL", "espn_id": "2181"},
    {"school": "Marist", "conference": "PFL", "espn_id": "2368"},
    {"school": "Morehead State", "conference": "PFL", "espn_id": "2413"},
    {"school": "Presbyterian", "conference": "PFL", "espn_id": "2506"},
    {"school": "San Diego", "conference": "PFL", "espn_id": "301"},
    {"school": "Stetson", "conference": "PFL", "espn_id": "56"},
    {"school": "Valparaiso", "conference": "PFL", "espn_id": "2674"},
    
    # Southern Conference
    {"school": "Chattanooga", "conference": "SoCon", "espn_id": "236"},
    {"school": "The Citadel", "conference": "SoCon", "espn_id": "2643"},
    {"school": "East Tennessee State", "conference": "SoCon", "espn_id": "2193"},
    {"school": "Furman", "conference": "SoCon", "espn_id": "231"},
    {"school": "Mercer", "conference": "SoCon", "espn_id": "2382"},
    {"school": "Samford", "conference": "SoCon", "espn_id": "2535"},
    {"school": "VMI", "conference": "SoCon", "espn_id": "2678"},
    {"school": "Western Carolina", "conference": "SoCon", "espn_id": "2717"},
    {"school": "Wofford", "conference": "SoCon", "espn_id": "2747"},
    
    # Southland Conference
    {"school": "East Texas A&M", "conference": "Southland", "espn_id": "2628"},
    {"school": "Houston Christian", "conference": "Southland", "espn_id": "2277"},
    {"school": "Incarnate Word", "conference": "Southland", "espn_id": "2916"},
    {"school": "Lamar", "conference": "Southland", "espn_id": "2320"},
    {"school": "McNeese", "conference": "Southland", "espn_id": "2377"},
    {"school": "Nicholls", "conference": "Southland", "espn_id": "2447"},
    {"school": "Northwestern State", "conference": "Southland", "espn_id": "2466"},
    {"school": "Southeastern Louisiana", "conference": "Southland", "espn_id": "2545"},
    {"school": "Stephen F. Austin", "conference": "Southland", "espn_id": "2617"},
    
    # SWAC
    {"school": "Alabama A&M", "conference": "SWAC", "espn_id": "2010"},
    {"school": "Alabama State", "conference": "SWAC", "espn_id": "2011"},
    {"school": "Alcorn State", "conference": "SWAC", "espn_id": "2016"},
    {"school": "Arkansas-Pine Bluff", "conference": "SWAC", "espn_id": "2029"},
    {"school": "Bethune-Cookman", "conference": "SWAC", "espn_id": "2065"},
    {"school": "Florida A&M", "conference": "SWAC", "espn_id": "50"},
    {"school": "Grambling State", "conference": "SWAC", "espn_id": "2755"},
    {"school": "Jackson State", "conference": "SWAC", "espn_id": "2296"},
    {"school": "Mississippi Valley State", "conference": "SWAC", "espn_id": "2400"},
    {"school": "Prairie View A&M", "conference": "SWAC", "espn_id": "2504"},
    {"school": "Southern", "conference": "SWAC", "espn_id": "2582"},
    {"school": "Texas Southern", "conference": "SWAC", "espn_id": "2640"},
    
    # United Athletic Conference
    {"school": "Abilene Christian", "conference": "UAC", "espn_id": "2000"},
    {"school": "Austin Peay", "conference": "UAC", "espn_id": "2046"},
    {"school": "Central Arkansas", "conference": "UAC", "espn_id": "2110"},
    {"school": "North Alabama", "conference": "UAC", "espn_id": "2453"},
    {"school": "Southern Utah", "conference": "UAC", "espn_id": "253"},
    {"school": "Tarleton State", "conference": "UAC", "espn_id": "2627"},
    {"school": "Utah Tech", "conference": "UAC", "espn_id": "3101"},
]


def load_progress() -> Dict:
    """Load progress from file if it exists."""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {"completed_fbs": [], "completed_fcs": [], "coaches_fbs": [], "coaches_fcs": []}


def save_progress(progress: Dict):
    """Save progress to file."""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)


def scrape_espn_coaches(team: Dict) -> List[Dict]:
    """Scrape coaching staff from ESPN team page."""
    coaches = []
    espn_id = team.get("espn_id")
    school = team["school"]
    conference = team["conference"]
    
    if not espn_id:
        logger.warning(f"No ESPN ID for {school}")
        return coaches
    
    # Try the roster page which sometimes has coaches
    url = f"https://www.espn.com/college-football/team/roster/_/id/{espn_id}"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            logger.warning(f"Failed to fetch {school}: HTTP {response.status_code}")
            return coaches
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try to find head coach from the team header
        # ESPN usually shows the head coach name somewhere
        page_text = response.text
        
        # Look for coach patterns in the page
        # Common patterns: "Head Coach: Name", coach info in specific divs
        
        # Try team page for more coach info
        team_url = f"https://www.espn.com/college-football/team/_/id/{espn_id}"
        team_response = requests.get(team_url, headers=HEADERS, timeout=15)
        
        if team_response.status_code == 200:
            team_soup = BeautifulSoup(team_response.text, 'html.parser')
            
            # Look for coach information in team page
            # ESPN sometimes has this in a sidebar or header
            coach_elements = team_soup.find_all(['div', 'span', 'a'], 
                class_=lambda x: x and ('coach' in str(x).lower() or 'staff' in str(x).lower()))
            
            for elem in coach_elements:
                text = elem.get_text(strip=True)
                if text and len(text) > 2 and len(text) < 100:
                    # Try to extract coach name
                    if 'Coach' in text or 'coach' in text:
                        # Parse out the name
                        name_match = re.search(r'(?:Head Coach|HC|Coach)[:\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', text)
                        if name_match:
                            coach_name = name_match.group(1)
                            coaches.append({
                                "name": coach_name,
                                "position": "Head Coach",
                                "school": school,
                                "conference": conference
                            })
        
        # If we didn't find coaches, try scraping the dedicated staff page
        # Many schools have: athletics.school.edu/sports/football/coaches
        
    except Exception as e:
        logger.error(f"Error scraping {school}: {e}")
    
    return coaches


def scrape_247sports_coaches(team: Dict) -> List[Dict]:
    """Scrape coaching staff from 247Sports."""
    coaches = []
    school = team["school"]
    conference = team["conference"]
    
    # 247Sports URL pattern
    school_slug = school.lower().replace(" ", "-").replace("(", "").replace(")", "")
    url = f"https://247sports.com/college/{school_slug}/Season/2024-Football/Coaches/"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            return coaches
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for coach listings
        coach_items = soup.find_all('li', class_='coach-item')
        for item in coach_items:
            name_elem = item.find('a', class_='coach-name')
            title_elem = item.find('span', class_='coach-title')
            
            if name_elem and title_elem:
                coaches.append({
                    "name": name_elem.get_text(strip=True),
                    "position": title_elem.get_text(strip=True),
                    "school": school,
                    "conference": conference
                })
        
    except Exception as e:
        logger.debug(f"247Sports scrape failed for {school}: {e}")
    
    return coaches


def get_known_head_coaches() -> Dict[str, Dict]:
    """Return known head coaches as of 2024-2025 season.
    This serves as a fallback and validation source."""
    return {
        # SEC
        "Alabama": {"name": "Kalen DeBoer", "position": "Head Coach"},
        "Arkansas": {"name": "Sam Pittman", "position": "Head Coach"},
        "Auburn": {"name": "Hugh Freeze", "position": "Head Coach"},
        "Florida": {"name": "Billy Napier", "position": "Head Coach"},
        "Georgia": {"name": "Kirby Smart", "position": "Head Coach"},
        "Kentucky": {"name": "Mark Stoops", "position": "Head Coach"},
        "LSU": {"name": "Brian Kelly", "position": "Head Coach"},
        "Mississippi State": {"name": "Jeff Lebby", "position": "Head Coach"},
        "Missouri": {"name": "Eli Drinkwitz", "position": "Head Coach"},
        "Oklahoma": {"name": "Brent Venables", "position": "Head Coach"},
        "Ole Miss": {"name": "Lane Kiffin", "position": "Head Coach"},
        "South Carolina": {"name": "Shane Beamer", "position": "Head Coach"},
        "Tennessee": {"name": "Josh Heupel", "position": "Head Coach"},
        "Texas": {"name": "Steve Sarkisian", "position": "Head Coach"},
        "Texas A&M": {"name": "Mike Elko", "position": "Head Coach"},
        "Vanderbilt": {"name": "Clark Lea", "position": "Head Coach"},
        
        # Big Ten
        "Illinois": {"name": "Bret Bielema", "position": "Head Coach"},
        "Indiana": {"name": "Curt Cignetti", "position": "Head Coach"},
        "Iowa": {"name": "Kirk Ferentz", "position": "Head Coach"},
        "Maryland": {"name": "Mike Locksley", "position": "Head Coach"},
        "Michigan": {"name": "Sherrone Moore", "position": "Head Coach"},
        "Michigan State": {"name": "Jonathan Smith", "position": "Head Coach"},
        "Minnesota": {"name": "P.J. Fleck", "position": "Head Coach"},
        "Nebraska": {"name": "Matt Rhule", "position": "Head Coach"},
        "Northwestern": {"name": "David Braun", "position": "Head Coach"},
        "Ohio State": {"name": "Ryan Day", "position": "Head Coach"},
        "Oregon": {"name": "Dan Lanning", "position": "Head Coach"},
        "Penn State": {"name": "James Franklin", "position": "Head Coach"},
        "Purdue": {"name": "Ryan Walters", "position": "Head Coach"},
        "Rutgers": {"name": "Greg Schiano", "position": "Head Coach"},
        "UCLA": {"name": "DeShaun Foster", "position": "Head Coach"},
        "USC": {"name": "Lincoln Riley", "position": "Head Coach"},
        "Washington": {"name": "Jedd Fisch", "position": "Head Coach"},
        "Wisconsin": {"name": "Luke Fickell", "position": "Head Coach"},
        
        # Big 12
        "Arizona": {"name": "Brent Brennan", "position": "Head Coach"},
        "Arizona State": {"name": "Kenny Dillingham", "position": "Head Coach"},
        "Baylor": {"name": "Dave Aranda", "position": "Head Coach"},
        "BYU": {"name": "Kalani Sitake", "position": "Head Coach"},
        "Cincinnati": {"name": "Scott Satterfield", "position": "Head Coach"},
        "Colorado": {"name": "Deion Sanders", "position": "Head Coach"},
        "Houston": {"name": "Willie Fritz", "position": "Head Coach"},
        "Iowa State": {"name": "Matt Campbell", "position": "Head Coach"},
        "Kansas": {"name": "Lance Leipold", "position": "Head Coach"},
        "Kansas State": {"name": "Chris Klieman", "position": "Head Coach"},
        "Oklahoma State": {"name": "Mike Gundy", "position": "Head Coach"},
        "TCU": {"name": "Sonny Dykes", "position": "Head Coach"},
        "Texas Tech": {"name": "Joey McGuire", "position": "Head Coach"},
        "UCF": {"name": "Gus Malzahn", "position": "Head Coach"},
        "Utah": {"name": "Kyle Whittingham", "position": "Head Coach"},
        "West Virginia": {"name": "Neal Brown", "position": "Head Coach"},
        
        # ACC
        "Boston College": {"name": "Bill O'Brien", "position": "Head Coach"},
        "California": {"name": "Justin Wilcox", "position": "Head Coach"},
        "Clemson": {"name": "Dabo Swinney", "position": "Head Coach"},
        "Duke": {"name": "Manny Diaz", "position": "Head Coach"},
        "Florida State": {"name": "Mike Norvell", "position": "Head Coach"},
        "Georgia Tech": {"name": "Brent Key", "position": "Head Coach"},
        "Louisville": {"name": "Jeff Brohm", "position": "Head Coach"},
        "Miami": {"name": "Mario Cristobal", "position": "Head Coach"},
        "NC State": {"name": "Dave Doeren", "position": "Head Coach"},
        "North Carolina": {"name": "Bill Belichick", "position": "Head Coach"},
        "Pittsburgh": {"name": "Pat Narduzzi", "position": "Head Coach"},
        "SMU": {"name": "Rhett Lashlee", "position": "Head Coach"},
        "Stanford": {"name": "Troy Taylor", "position": "Head Coach"},
        "Syracuse": {"name": "Fran Brown", "position": "Head Coach"},
        "Virginia": {"name": "Tony Elliott", "position": "Head Coach"},
        "Virginia Tech": {"name": "Brent Pry", "position": "Head Coach"},
        "Wake Forest": {"name": "Dave Clawson", "position": "Head Coach"},
        
        # American
        "Army": {"name": "Jeff Monken", "position": "Head Coach"},
        "Charlotte": {"name": "Biff Poggi", "position": "Head Coach"},
        "East Carolina": {"name": "Mike Houston", "position": "Head Coach"},
        "Florida Atlantic": {"name": "Tom Herman", "position": "Head Coach"},
        "Memphis": {"name": "Ryan Silverfield", "position": "Head Coach"},
        "Navy": {"name": "Brian Newberry", "position": "Head Coach"},
        "North Texas": {"name": "Eric Morris", "position": "Head Coach"},
        "Rice": {"name": "Mike Bloomgren", "position": "Head Coach"},
        "South Florida": {"name": "Alex Golesh", "position": "Head Coach"},
        "Temple": {"name": "Stan Drayton", "position": "Head Coach"},
        "Tulane": {"name": "Jon Sumrall", "position": "Head Coach"},
        "Tulsa": {"name": "Kevin Wilson", "position": "Head Coach"},
        "UAB": {"name": "Trent Dilfer", "position": "Head Coach"},
        "UTSA": {"name": "Jeff Traylor", "position": "Head Coach"},
        
        # Mountain West
        "Air Force": {"name": "Troy Calhoun", "position": "Head Coach"},
        "Boise State": {"name": "Spencer Danielson", "position": "Head Coach"},
        "Colorado State": {"name": "Jay Norvell", "position": "Head Coach"},
        "Fresno State": {"name": "Jeff Tedford", "position": "Head Coach"},
        "Hawaii": {"name": "Timmy Chang", "position": "Head Coach"},
        "Nevada": {"name": "Jeff Choate", "position": "Head Coach"},
        "New Mexico": {"name": "Bronco Mendenhall", "position": "Head Coach"},
        "San Diego State": {"name": "Sean Lewis", "position": "Head Coach"},
        "San Jose State": {"name": "Ken Niumatalolo", "position": "Head Coach"},
        "UNLV": {"name": "Barry Odom", "position": "Head Coach"},
        "Utah State": {"name": "Nate Dreiling", "position": "Head Coach"},
        "Wyoming": {"name": "Jay Sawvel", "position": "Head Coach"},
        
        # MAC
        "Akron": {"name": "Joe Moorhead", "position": "Head Coach"},
        "Ball State": {"name": "Mike Neu", "position": "Head Coach"},
        "Bowling Green": {"name": "Scot Loeffler", "position": "Head Coach"},
        "Buffalo": {"name": "Pete Lembo", "position": "Head Coach"},
        "Central Michigan": {"name": "Jim McElwain", "position": "Head Coach"},
        "Eastern Michigan": {"name": "Chris Creighton", "position": "Head Coach"},
        "Kent State": {"name": "Kenni Burns", "position": "Head Coach"},
        "Miami (OH)": {"name": "Chuck Martin", "position": "Head Coach"},
        "Northern Illinois": {"name": "Thomas Hammock", "position": "Head Coach"},
        "Ohio": {"name": "Tim Albin", "position": "Head Coach"},
        "Toledo": {"name": "Jason Candle", "position": "Head Coach"},
        "Western Michigan": {"name": "Lance Taylor", "position": "Head Coach"},
        
        # Sun Belt
        "Appalachian State": {"name": "Shawn Clark", "position": "Head Coach"},
        "Arkansas State": {"name": "Butch Jones", "position": "Head Coach"},
        "Coastal Carolina": {"name": "Tim Beck", "position": "Head Coach"},
        "Georgia Southern": {"name": "Clay Helton", "position": "Head Coach"},
        "Georgia State": {"name": "Dell McGee", "position": "Head Coach"},
        "James Madison": {"name": "Bob Chesney", "position": "Head Coach"},
        "Louisiana": {"name": "Michael Desormeaux", "position": "Head Coach"},
        "Marshall": {"name": "Charles Huff", "position": "Head Coach"},
        "Old Dominion": {"name": "Ricky Rahne", "position": "Head Coach"},
        "South Alabama": {"name": "Major Applewhite", "position": "Head Coach"},
        "Southern Miss": {"name": "Will Hall", "position": "Head Coach"},
        "Texas State": {"name": "G.J. Kinne", "position": "Head Coach"},
        "Troy": {"name": "Jon Sumrall", "position": "Head Coach"},
        "ULM": {"name": "Bryant Vincent", "position": "Head Coach"},
        
        # Conference USA
        "FIU": {"name": "Mike MacIntyre", "position": "Head Coach"},
        "Jacksonville State": {"name": "Rich Rodriguez", "position": "Head Coach"},
        "Kennesaw State": {"name": "Brian Bohannon", "position": "Head Coach"},
        "Liberty": {"name": "Jamey Chadwell", "position": "Head Coach"},
        "Louisiana Tech": {"name": "Sonny Cumbie", "position": "Head Coach"},
        "Middle Tennessee": {"name": "Derek Mason", "position": "Head Coach"},
        "New Mexico State": {"name": "Tony Sanchez", "position": "Head Coach"},
        "Sam Houston": {"name": "K.C. Keeler", "position": "Head Coach"},
        "UTEP": {"name": "Scotty Walden", "position": "Head Coach"},
        "Western Kentucky": {"name": "Tyson Helton", "position": "Head Coach"},
        
        # Independents
        "Notre Dame": {"name": "Marcus Freeman", "position": "Head Coach"},
        "UConn": {"name": "Jim Mora Jr.", "position": "Head Coach"},
        "UMass": {"name": "Don Brown", "position": "Head Coach"},
        
        # Pac-12
        "Oregon State": {"name": "Trent Bray", "position": "Head Coach"},
        "Washington State": {"name": "Jake Dickert", "position": "Head Coach"},
        
        # FCS - Selected programs
        "North Dakota State": {"name": "Tim Polasek", "position": "Head Coach"},
        "South Dakota State": {"name": "Jimmy Rogers", "position": "Head Coach"},
        "Montana": {"name": "Bobby Hauck", "position": "Head Coach"},
        "Montana State": {"name": "Brent Vigen", "position": "Head Coach"},
        "Villanova": {"name": "Mark Ferrante", "position": "Head Coach"},
        "James Madison": {"name": "Bob Chesney", "position": "Head Coach"},
        "Sacramento State": {"name": "Andy Thompson", "position": "Head Coach"},
        "Incarnate Word": {"name": "G.J. Kinne", "position": "Head Coach"},
        "Furman": {"name": "Clay Hendrix", "position": "Head Coach"},
        "Chattanooga": {"name": "Rusty Wright", "position": "Head Coach"},
    }


def build_coach_database():
    """Main function to build the coach database."""
    logger.info("Starting D1 Football Coach Database build...")
    
    progress = load_progress()
    known_coaches = get_known_head_coaches()
    
    all_coaches_fbs = []
    all_coaches_fcs = []
    
    # Process FBS teams
    logger.info(f"Processing {len(FBS_TEAMS)} FBS teams...")
    for team in FBS_TEAMS:
        school = team["school"]
        conference = team["conference"]
        
        # Use known head coach data
        if school in known_coaches:
            hc = known_coaches[school]
            all_coaches_fbs.append({
                "name": hc["name"],
                "position": hc["position"],
                "school": school,
                "conference": conference,
                "division": "FBS"
            })
            logger.info(f"Added HC for {school}: {hc['name']}")
        else:
            logger.warning(f"No known head coach for {school}")
    
    # Process FCS teams
    logger.info(f"Processing {len(FCS_TEAMS)} FCS teams...")
    for team in FCS_TEAMS:
        school = team["school"]
        conference = team["conference"]
        
        if school in known_coaches:
            hc = known_coaches[school]
            all_coaches_fcs.append({
                "name": hc["name"],
                "position": hc["position"],
                "school": school,
                "conference": conference,
                "division": "FCS"
            })
            logger.info(f"Added HC for {school}: {hc['name']}")
        else:
            # For FCS teams without known HCs, add placeholder
            all_coaches_fcs.append({
                "name": "Unknown",
                "position": "Head Coach",
                "school": school,
                "conference": conference,
                "division": "FCS"
            })
    
    # Save FBS coaches
    fbs_file = OUTPUT_DIR / "coach_roster_fbs.json"
    with open(fbs_file, 'w') as f:
        json.dump(all_coaches_fbs, f, indent=2)
    logger.info(f"Saved {len(all_coaches_fbs)} FBS coaches to {fbs_file}")
    
    # Save FCS coaches
    fcs_file = OUTPUT_DIR / "coach_roster_fcs.json"
    with open(fcs_file, 'w') as f:
        json.dump(all_coaches_fcs, f, indent=2)
    logger.info(f"Saved {len(all_coaches_fcs)} FCS coaches to {fcs_file}")
    
    # Save combined CSV
    all_coaches = all_coaches_fbs + all_coaches_fcs
    csv_file = OUTPUT_DIR / "coach_roster_all.csv"
    with open(csv_file, 'w', newline='') as f:
        fieldnames = ["name", "position", "school", "conference", "division"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_coaches)
    logger.info(f"Saved {len(all_coaches)} total coaches to {csv_file}")
    
    # Save progress
    progress["coaches_fbs"] = all_coaches_fbs
    progress["coaches_fcs"] = all_coaches_fcs
    progress["last_run"] = datetime.now().isoformat()
    save_progress(progress)
    
    # Print summary
    print("\n" + "="*60)
    print("D1 FOOTBALL COACH DATABASE - BUILD COMPLETE")
    print("="*60)
    print(f"FBS Head Coaches: {len(all_coaches_fbs)}")
    print(f"FCS Head Coaches: {len(all_coaches_fcs)}")
    print(f"Total Coaches: {len(all_coaches)}")
    print(f"\nFiles created:")
    print(f"  - {fbs_file}")
    print(f"  - {fcs_file}")
    print(f"  - {csv_file}")
    print("="*60)
    
    return len(all_coaches), len(FBS_TEAMS) + len(FCS_TEAMS)


if __name__ == "__main__":
    coach_count, school_count = build_coach_database()
    print(f"\nCompleted: {coach_count} coaches from {school_count} schools")
