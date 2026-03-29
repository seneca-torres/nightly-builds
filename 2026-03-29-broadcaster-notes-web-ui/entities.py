#!/usr/bin/env python3
"""
Entity extraction for broadcaster notes.
Uses static lists of coaches, schools, etc. (no ML dependencies).
"""

import re
import json
from datetime import datetime

# Static lists of entities (can be extended)
COACHES = [
    # Head coaches
    "Nick Saban", "Kirby Smart", "Dabo Swinney", "Jim Harbaugh", "Ryan Day",
    "Lincoln Riley", "Brian Kelly", "Dan Lanning", "Kalen DeBoer", "Steve Sarkisian",
    "Mike Norvell", "Lane Kiffin", "James Franklin", "Mark Stoops", "Josh Heupel",
    "Billy Napier", "Brent Venables", "Sam Pittman", "Shane Beamer", "Dave Aranda",
    "Dan Mullen", "Mack Brown", "Pat Narduzzi", "Kirk Ferentz", "P.J. Fleck",
    "Jeff Brohm", "Luke Fickell", "Matt Rhule", "Deion Sanders", "Bret Bielema",
    "Mike Gundy", "Kyle Whittingham", "Jonathan Smith", "Chris Klieman", "Lance Leipold",
    
    # Common first names/last names for pattern matching
    "Saban", "Smart", "Swinney", "Harbaugh", "Day", "Riley", "Kelly", "Lanning",
    "DeBoer", "Sarkisian", "Norvell", "Kiffin", "Franklin", "Stoops", "Heupel",
    "Napier", "Venables", "Pittman", "Beamer", "Aranda", "Mullen", "Brown",
    
    # Assistants and coordinators
    "Dan Casey", "Mike Macdonald", "Wink Martindale", "Todd Monken", "Mike Denbrock",
    "Garrett Riley", "Phil Parker", "Jim Knowles", "Pete Golding", "Kevin Steele",
    "Alex Grinch", "Jeff Lebby", "Kendal Briles", "Joe Moorhead", "Josh Gattis",
]

SCHOOLS = [
    # Power 5 Schools
    "Alabama", "Georgia", "Clemson", "Michigan", "Ohio State",
    "USC", "Notre Dame", "Oregon", "Washington", "Texas",
    "Florida State", "Ole Miss", "Penn State", "Kentucky", "Tennessee",
    "Florida", "Oklahoma", "Arkansas", "South Carolina", "Baylor",
    "LSU", "North Carolina", "Pittsburgh", "Iowa", "Minnesota",
    "Purdue", "Wisconsin", "Nebraska", "Colorado", "Illinois",
    "Oklahoma State", "Utah", "Michigan State", "Kansas State", "Kansas",
    
    # Group of 5 and others
    "Cincinnati", "UCF", "Houston", "BYU", "Boise State",
    "San Diego State", "Fresno State", "Appalachian State", "Coastal Carolina",
    "Liberty", "Tulane", "SMU", "Memphis", "Navy", "Army", "Air Force",
    
    # Conferences
    "SEC", "Big Ten", "ACC", "Big 12", "Pac-12", "American", "Mountain West",
    "MAC", "Sun Belt", "C-USA", "FBS", "FCS",
    
    # Common abbreviations
    "UA", "UGA", "UM", "OSU", "ND", "UT", "FSU", "OU", "UF", "USC",
]

ROLES = [
    "Head Coach", "Offensive Coordinator", "Defensive Coordinator",
    "Special Teams Coordinator", "Quarterbacks Coach", "Running Backs Coach",
    "Wide Receivers Coach", "Tight Ends Coach", "Offensive Line Coach",
    "Defensive Line Coach", "Linebackers Coach", "Defensive Backs Coach",
    "Safeties Coach", "Cornerbacks Coach", "Strength Coach",
    "Director of Operations", "Recruiting Coordinator", "Analyst",
    "Graduate Assistant", "Quality Control", "Assistant Head Coach",
    "Co-Offensive Coordinator", "Co-Defensive Coordinator",
    "Passing Game Coordinator", "Running Game Coordinator",
]

def extract_dates(text):
    """Extract dates from text using regex patterns."""
    date_patterns = [
        # YYYY-MM-DD
        r'\b\d{4}-\d{2}-\d{2}\b',
        # MM/DD/YYYY or MM/DD/YY
        r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
        # Month DD, YYYY
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',
        # DD Month YYYY
        r'\b\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b',
        # Year only
        r'\b(?:19|20)\d{2}\b',
        # Recent years (last 10 years)
        r'\b20(?:1[6-9]|2[0-6])\b',
    ]
    
    dates = set()
    for pattern in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        dates.update(matches)
    
    return list(dates)

def extract_entities(text):
    """
    Extract coaches, schools, dates, and roles from text.
    Returns a dictionary with sets of entities.
    """
    text_lower = text.lower()
    
    # Extract coaches
    coaches_found = set()
    for coach in COACHES:
        if coach.lower() in text_lower:
            coaches_found.add(coach)
    
    # Extract schools
    schools_found = set()
    for school in SCHOOLS:
        if school.lower() in text_lower:
            schools_found.add(school)
    
    # Extract roles
    roles_found = set()
    for role in ROLES:
        if role.lower() in text_lower:
            roles_found.add(role)
    
    # Extract dates
    dates_found = extract_dates(text)
    
    return {
        'coaches': list(coaches_found),
        'schools': list(schools_found),
        'roles': list(roles_found),
        'dates': dates_found
    }

if __name__ == '__main__':
    # Test the extraction
    sample_text = """
    Met with Nick Saban at Alabama on 2023-03-15. Discussed offensive coordinator search.
    Also talked to Dan Casey about the QB development program. Ryan Day from Ohio State
    was mentioned as a reference. Follow-up scheduled for April 20, 2024.
    """
    
    entities = extract_entities(sample_text)
    print("Extracted entities:")
    print(json.dumps(entities, indent=2))