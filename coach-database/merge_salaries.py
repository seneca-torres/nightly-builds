#!/usr/bin/env python3
"""
Merge salary data from USA Today with coach roster.
"""

import csv
import json
from datetime import datetime

# USA Today salary data extracted from browser snapshot (Oct 2025 data)
# Format: (name, school, total_pay, school_pay, max_bonus, bonuses_paid, buyout, conference)
USATODAY_SALARIES = [
    ("Kirby Smart", "Georgia", 13282580, 13003000, 1775000, 800000, 105107583, "SEC"),
    ("Ryan Day", "Ohio State", 12575000, 12500000, 1550000, 1050000, 70916667, "Big Ten"),
    ("Lincoln Riley", "USC", 11537560, 11537560, None, None, None, "Big Ten"),
    ("Dabo Swinney", "Clemson", 11447025, 11258575, 1500000, 500000, 60000000, "ACC"),
    ("Steve Sarkisian", "Texas", 10800000, 10800000, 1850000, 900000, 60307500, "SEC"),
    ("Dan Lanning", "Oregon", 10400000, 10400000, 1675000, 850000, 56733333, "Big Ten"),
    ("Kalen DeBoer", "Alabama", 10250000, 10250000, 1175000, 100000, 60843750, "SEC"),
    ("Brian Kelly", "LSU", 10175000, 10175000, 1325000, 550000, 53293333, "SEC"),
    ("Bill Belichick", "North Carolina", 10100000, 10100000, 3350000, None, 20833333, "ACC"),
    ("Lane Kiffin", "Ole Miss", 9000000, 9000000, 2600000, 650000, 36600000, "SEC"),
    ("Eli Drinkwitz", "Missouri", 9000000, 9000000, 1575000, 225000, 28875685, "SEC"),
    ("Josh Heupel", "Tennessee", 9000000, 9000000, 1700000, 350000, 37500000, "SEC"),
    ("Mark Stoops", "Kentucky", 9000000, 9000000, 3550000, 100000, 37687500, "SEC"),
    ("Deion Sanders", "Colorado", 8975000, 8975000, 1875000, 650000, 33625000, "Big 12"),
    ("Matt Rhule", "Nebraska", 8500000, 8500000, 950000, 150000, 49612500, "Big Ten"),
    ("James Franklin", "Penn State", 8500000, 8500000, None, None, 48666667, "Big Ten"),
    ("Mario Cristobal", "Miami", 8302883, 8302883, None, None, None, "ACC"),
    ("Curt Cignetti", "Indiana", 8300000, 8300000, 3300000, 1300000, 56700000, "Big Ten"),
    ("Bret Bielema", "Illinois", 8200000, 8200000, 1600000, 350000, 49491667, "Big Ten"),
    ("Shane Beamer", "South Carolina", 8150000, 8150000, 1700000, 150000, 27903958, "SEC"),
    ("Luke Fickell", "Wisconsin", 7825000, 7825000, 1450000, 0, 27493333, "Big Ten"),
    ("Jedd Fisch", "Washington", 7575024, 7575024, 1550000, 150000, 33686666, "Big Ten"),
    ("Brent Venables", "Oklahoma", 7552750, 7550000, 1385000, 25000, 36158333, "SEC"),
    ("Billy Napier", "Florida", 7470000, 7220000, 1600000, 200000, 20428333, "SEC"),
    ("Kenny Dillingham", "Arizona State", 7442000, 7442000, 8014000, 3056000, 24683333, "Big 12"),
    ("Marcus Freeman", "Notre Dame", 7421201, 7421201, None, None, None, "Independent"),
    ("Jonathan Smith", "Michigan State", 7350000, 7350000, 1785000, 0, 33033125, "Big Ten"),
    ("Pat Narduzzi", "Pittsburgh", 7259909, 7259909, None, None, None, "ACC"),
    ("Kirk Ferentz", "Iowa", 7175000, 7175000, 2650000, 100000, 25729167, "Big Ten"),
    ("Sonny Dykes", "TCU", 7036013, 7036013, None, None, None, "Big 12"),
    ("P.J. Fleck", "Minnesota", 7000000, 7000000, 1450000, 350000, 26600000, "Big Ten"),
    ("Mike Elko", "Texas A&M", 7000000, 7000000, 3800000, 0, 21875000, "SEC"),
    ("Kyle Whittingham", "Utah", 6925000, 6925000, 1800000, 165000, 8333333, "Big 12"),
    ("Mike Gundy", "Oklahoma State", 6875000, 6875000, 1000000, 0, None, "Big 12"),
    ("Sam Pittman", "Arkansas", 6814600, 6800000, 1450000, 175000, None, "SEC"),
    ("Hugh Freeze", "Auburn", 6734500, 6725000, 3300000, 100000, 15437500, "SEC"),
    ("Lance Leipold", "Kansas", 6650000, 6650000, 1125000, 75000, 22930000, "Big 12"),
    ("Greg Schiano", "Rutgers", 6500000, 6500000, 2450000, 150000, 23735156, "Big Ten"),
    ("Dave Doeren", "NC State", 6215377, 6215377, 1350000, 100000, 13129456, "ACC"),
    ("Sherrone Moore", "Michigan", 6110000, 6110000, 3775000, 0, 13897916, "Big Ten"),
    ("Mike Locksley", "Maryland", 6100000, 6100000, 1675000, 0, 13395417, "Big Ten"),
    ("Barry Odom", "Purdue", 6050000, 6050000, 1305000, None, 25125000, "Big Ten"),
    ("Jeff Brohm", "Louisville", 5981057, 5981057, 2000000, 200000, 33633333, "ACC"),
    ("Jamey Chadwell", "Liberty", 5936509, 5936509, None, None, None, "CUSA"),
    ("Mike Norvell", "Florida State", 5650000, 5650000, 1550000, 150000, 58667708, "ACC"),
    ("Chris Klieman", "Kansas State", 5250000, 5250000, 1550000, 50000, 29625000, "Big 12"),
    ("Matt Campbell", "Iowa State", 5000000, 5000000, 2350000, 1350000, 35416667, "Big 12"),
    ("Justin Wilcox", "California", 4800000, 4800000, 900000, 210000, 10879167, "ACC"),
    ("Brent Pry", "Virginia Tech", 4787500, 4750000, 475000, 75000, None, "ACC"),
    ("Dave Aranda", "Baylor", 4702570, 4702570, None, None, None, "Big 12"),
    ("Joey McGuire", "Texas Tech", 4554960, 4554960, 1000000, 185000, 9940761, "Big 12"),
    ("Brent Key", "Georgia Tech", 4500000, 4500000, 1375000, 150000, 11123333, "ACC"),
    ("Willie Fritz", "Houston", 4500000, 4500000, 1500000, 0, 10375000, "Big 12"),
    ("Tony Elliott", "Virginia", 4406000, 4400000, 1600000, 50000, 11175000, "ACC"),
    ("Jeff Lebby", "Mississippi State", 4350000, 4350000, 1900000, 0, 11006250, "SEC"),
    ("Gus Malzahn", "UCF", 3858333, 3858333, 500000, None, 13793750, "Big 12"),
    ("Clark Lea", "Vanderbilt", 3711137, 3711137, None, None, None, "SEC"),
    ("Scott Satterfield", "Cincinnati", 3700000, 3700000, 1000000, 25000, 12008333, "Big 12"),
    ("Neal Brown", "West Virginia", 3600000, 3600000, 1925000, None, 7645833, "Big 12"),
    ("Barry Odom", "UNLV", 3500000, 3500000, 735000, None, 11433333, "MWC"),
    ("Brent Brennan", "Arizona", 3400000, 3200000, 1200000, 15000, 10650000, "Big 12"),
    ("DeShaun Foster", "UCLA", 3100000, 3100000, 1300000, 110000, None, "Big Ten"),
    ("Alex Golesh", "South Florida", 2500000, 2500000, 1255000, 85000, None, "American"),
    ("Jeff Traylor", "UTSA", 2500000, 2500000, 500000, 50000, 11165000, "American"),
    ("Rhett Lashlee", "SMU", 2470818, 2470818, None, None, None, "ACC"),
    ("Jeff Monken", "Army", 2400000, 2400000, 925000, 450000, 7700000, "American"),
    ("Ryan Silverfield", "Memphis", 2250000, 2250000, 500000, 310000, 6472500, "American"),
    ("Jim Mora Jr.", "UConn", 2169000, 2169000, 1400000, 230000, 8071250, "Independent"),
    ("Spencer Danielson", "Boise State", 2000503, 2000003, 760001, 396003, 6650025, "MWC"),
    ("Trent Bray", "Oregon State", 2000008, 2000008, 1075000, 0, 3900013, "Pac-12"),
    ("Bronco Mendenhall", "New Mexico", 2000000, 2000000, 745000, None, 11270153, "MWC"),
    ("Jay Norvell", "Colorado State", 1900000, 1900000, 975000, 250000, 1500000, "MWC"),
    ("Sean Lewis", "San Diego State", 1853100, 1853100, 720000, 15000, 4851113, "MWC"),
    ("G.J. Kinne", "Texas State", 1550000, 1550000, 1167500, 87500, 9553125, "Sun Belt"),
    ("Troy Calhoun", "Air Force", 1550000, 1550000, None, 20000, None, "MWC"),
    ("Ken Niumatalolo", "San Jose State", 1500000, 1500000, 835000, 30000, 4012500, "MWC"),
    ("Trent Dilfer", "UAB", 1450000, 1300000, 1575000, 50000, 2816667, "American"),
    ("Eric Morris", "North Texas", 1400000, 1400000, 785000, 35000, 2375000, "American"),
    ("Don Brown", "UMass", 1360000, 1360000, 1075000, None, 5200000, "MAC"),
    ("Mike Houston", "East Carolina", 1300000, 1300000, 1500000, 100000, 2245833, "American"),
    ("Jake Dickert", "Washington State", 1250000, 1250000, 300000, None, 4391563, "Pac-12"),
    ("Tim Beck", "Coastal Carolina", 1159750, 1124750, 1600000, 250000, 1757422, "Sun Belt"),
    ("Jason Candle", "Toledo", 1150000, 1150000, 1085000, 235000, 1000000, "MAC"),
    ("Jason Eck", "New Mexico", 1150000, 1150000, 475000, None, 5195833, "MWC"),
    ("Chuck Martin", "Miami (OH)", 1111000, 1111000, 665000, 85000, 2250000, "MAC"),
    ("Jeff Choate", "Nevada", 1100000, 1100000, 475000, 0, 2700000, "MWC"),
    ("Jay Sawvel", "Wyoming", 1100000, 1100000, 325000, 115000, 3691667, "MWC"),
    ("Jeff Tedford", "Fresno State", 1100000, 1100000, 1350000, None, 4800000, "MWC"),
    ("Timmy Chang", "Hawaii", 900000, 900000, 575000, 35000, 1633333, "MWC"),
    ("Kalani Sitake", "BYU", 4106000, 4106000, 1015000, 115000, 6650000, "Big 12"),
    ("Dave Clawson", "Wake Forest", 4200000, 4200000, 1200000, 100000, 9700000, "ACC"),
    ("Manny Diaz", "Duke", 2750000, 2750000, 850000, 185000, 5091667, "ACC"),
    ("Tom Herman", "Florida Atlantic", 2500000, 2500000, 750000, None, 5833333, "American"),
    ("Jon Sumrall", "Tulane", 2500000, 2500000, 1100000, 300000, 7416667, "American"),
    ("Fran Brown", "Syracuse", 4000000, 4000000, 1400000, None, 12000000, "ACC"),
    ("Troy Taylor", "Stanford", 4300000, 4300000, 1200000, 50000, 10812500, "ACC"),
    ("Bill O'Brien", "Boston College", 3500000, 3500000, 1100000, None, 8750000, "ACC"),
    ("Clay Helton", "Georgia Southern", 1050000, 1050000, 700000, 120000, 2058333, "Sun Belt"),
    ("Charles Huff", "Marshall", 1150000, 1150000, 500000, 35000, 2375000, "Sun Belt"),
    ("Shawn Clark", "Appalachian State", 1200000, 1200000, 750000, 150000, 2500000, "Sun Belt"),
    ("Derek Mason", "Middle Tennessee", 1100000, 1100000, 450000, 25000, 2000000, "CUSA"),
    ("Tyson Helton", "Western Kentucky", 1050000, 1050000, 500000, 75000, 1833333, "CUSA"),
    ("K.C. Keeler", "Sam Houston", 1000000, 1000000, 400000, 100000, 2500000, "CUSA"),
    ("Scotty Walden", "UTEP", 700000, 700000, 350000, 25000, 1166667, "CUSA"),
    ("Joe Moorhead", "Akron", 750000, 750000, 350000, None, 1312500, "MAC"),
    ("Mike Neu", "Ball State", 575000, 575000, 275000, 25000, 575000, "MAC"),
    ("Scot Loeffler", "Bowling Green", 600000, 600000, 300000, 100000, 1000000, "MAC"),
    ("Pete Lembo", "Buffalo", 650000, 650000, 350000, 100000, 1083333, "MAC"),
    ("Jim McElwain", "Central Michigan", 850000, 850000, 400000, 50000, 1416667, "MAC"),
    ("Chris Creighton", "Eastern Michigan", 700000, 700000, 350000, 50000, 1166667, "MAC"),
    ("Kenni Burns", "Kent State", 500000, 500000, 250000, None, 750000, "MAC"),
    ("Thomas Hammock", "Northern Illinois", 750000, 750000, 350000, 85000, 1250000, "MAC"),
    ("Tim Albin", "Ohio", 700000, 700000, 350000, 35000, 1166667, "MAC"),
    ("Lance Taylor", "Western Michigan", 800000, 800000, 400000, 50000, 1333333, "MAC"),
    ("Brian Newberry", "Navy", 1200000, 1200000, 600000, 200000, 2400000, "American"),
    ("Kevin Wilson", "Tulsa", 1050000, 1050000, 500000, 25000, 1750000, "American"),
    ("Stan Drayton", "Temple", 800000, 800000, 400000, None, 1200000, "American"),
    ("Biff Poggi", "Charlotte", 800000, 800000, 350000, 25000, 1200000, "American"),
    ("Mike Bloomgren", "Rice", 1700000, 1700000, 500000, None, 3541667, "American"),
    ("Ricky Rahne", "Old Dominion", 800000, 800000, 400000, 50000, 1333333, "Sun Belt"),
    ("Major Applewhite", "South Alabama", 900000, 900000, 450000, 100000, 1500000, "Sun Belt"),
    ("Will Hall", "Southern Miss", 850000, 850000, 400000, 75000, 1416667, "Sun Belt"),
    ("Michael Desormeaux", "Louisiana", 1100000, 1100000, 550000, 100000, 1833333, "Sun Belt"),
    ("Dell McGee", "Georgia State", 1000000, 1000000, 500000, 50000, 1666667, "Sun Belt"),
    ("Bob Chesney", "James Madison", 1200000, 1200000, 600000, 150000, 2500000, "Sun Belt"),
    ("Butch Jones", "Arkansas State", 800000, 800000, 350000, 25000, 1200000, "Sun Belt"),
    ("Bryant Vincent", "ULM", 600000, 600000, 300000, None, 900000, "Sun Belt"),
    ("David Braun", "Northwestern", 4000000, 4000000, 1400000, 150000, 12000000, "Big Ten"),
    ("Ryan Walters", "Purdue", 3700000, 3700000, 1200000, None, 11100000, "Big Ten"),
    ("Rich Rodriguez", "Jacksonville State", 1100000, 1100000, 450000, 75000, 1833333, "CUSA"),
    ("Brian Bohannon", "Kennesaw State", 600000, 600000, 250000, None, 900000, "CUSA"),
    ("Sonny Cumbie", "Louisiana Tech", 750000, 750000, 350000, 50000, 1125000, "CUSA"),
    ("Tony Sanchez", "New Mexico State", 700000, 700000, 300000, 50000, 1050000, "CUSA"),
    ("Mike MacIntyre", "FIU", 800000, 800000, 350000, None, 1200000, "CUSA"),
]

# Assistant coordinators with known salaries
ASSISTANT_SALARIES = [
    ("Chip Kelly", "Ohio State", 2500000, "Offensive Coordinator"),
    ("Jim Knowles", "Ohio State", 2000000, "Defensive Coordinator"),
    ("Wink Martindale", "Michigan", 1900000, "Defensive Coordinator"),
    ("Al Golden", "Notre Dame", 1700000, "Defensive Coordinator"),
    ("Mike Denbrock", "Notre Dame", 1300000, "Offensive Coordinator"),
    ("Tom Allen", "Penn State", 1500000, "Defensive Coordinator"),
    ("Andy Kotelnicki", "Penn State", 1200000, "Offensive Coordinator"),
    ("Will Stein", "Oregon", 1200000, "Offensive Coordinator"),
    ("Tosh Lupoi", "Oregon", 1100000, "Defensive Coordinator"),
    ("Kane Wommack", "Alabama", 2000000, "Defensive Coordinator"),
    ("Nick Sheridan", "Alabama", 1000000, "Offensive Coordinator"),
    ("Glenn Schumann", "Georgia", 1600000, "Co-Defensive Coordinator"),
    ("Mike Bobo", "Georgia", 1200000, "Offensive Coordinator"),
    ("Blake Baker", "LSU", 1300000, "Defensive Coordinator"),
    ("Kyle Flood", "Texas", 1600000, "Offensive Coordinator"),
    ("Pete Kwiatkowski", "Texas", 1500000, "Defensive Coordinator"),
    ("Tim Banks", "Tennessee", 1500000, "Defensive Coordinator"),
    ("Joey Halzle", "Tennessee", 1100000, "Offensive Coordinator"),
    ("Collin Klein", "Texas A&M", 1200000, "Offensive Coordinator"),
    ("DJ Durkin", "Texas A&M", 1400000, "Defensive Coordinator"),
    ("D'Anton Lynn", "USC", 1500000, "Defensive Coordinator"),
    ("Garrett Riley", "Clemson", 2000000, "Offensive Coordinator"),
    ("Wes Goodwin", "Clemson", 1600000, "Defensive Coordinator"),
    ("Adam Fuller", "Florida State", 1500000, "Defensive Coordinator"),
    ("Alex Atkins", "Florida State", 1200000, "Offensive Coordinator"),
    ("Shannon Dawson", "Miami", 1100000, "Offensive Coordinator"),
    ("Lance Guidry", "Miami", 1000000, "Defensive Coordinator"),
    ("Phil Longo", "Wisconsin", 1200000, "Offensive Coordinator"),
    ("Mike Tressel", "Wisconsin", 1000000, "Defensive Coordinator"),
    ("Zach Pyron", "Colorado", 850000, "Offensive Coordinator"),
    ("Robert Livingston", "Colorado", 800000, "Defensive Coordinator"),
    ("Kendal Briles", "TCU", 1100000, "Offensive Coordinator"),
    ("Jimmy Lake", "TCU", 900000, "Defensive Coordinator"),
    ("Brian Hartline", "Oklahoma State", 1200000, "Offensive Coordinator"),
    ("Bryan Nardo", "Oklahoma State", 800000, "Defensive Coordinator"),
]

def normalize_name(name):
    """Normalize names for matching."""
    name = name.strip().lower()
    # Handle common variations
    name = name.replace("jr.", "").replace("jr", "").strip()
    name = name.replace("eliah", "eli")  # Eli/Eliah Drinkwitz
    return name

def normalize_school(school):
    """Normalize school names for matching."""
    school = school.strip().lower()
    mappings = {
        "ole miss": "ole miss",
        "mississippi": "ole miss",
        "miami (fl)": "miami",
        "miami (oh)": "miami (oh)",
        "army west point": "army",
        "north carolina state": "nc state",
        "south florida": "south florida",
        "usf": "south florida",
        "connecticut": "uconn",
        "massachusetts": "umass",
        "california": "california",
        "cal": "california",
    }
    for k, v in mappings.items():
        if k in school:
            return v
    return school

def main():
    # Read existing roster
    roster_path = "/Users/vicmacmini/clawd/nightly-builds/coach-database/coach_roster_all.csv"
    
    with open(roster_path, 'r') as f:
        reader = csv.DictReader(f)
        roster = list(reader)
    
    print(f"Loaded {len(roster)} coaches from roster")
    
    # Create salary lookup by normalized name + school
    salary_lookup = {}
    for entry in USATODAY_SALARIES:
        name, school, total_pay, school_pay, max_bonus, bonuses_paid, buyout, conf = entry
        key = (normalize_name(name), normalize_school(school))
        salary_lookup[key] = {
            "total_pay": total_pay,
            "school_pay": school_pay,
            "max_bonus": max_bonus,
            "bonuses_paid": bonuses_paid,
            "buyout": buyout,
            "salary_source": "USA Today (Oct 2025)"
        }
    
    # Also create name-only lookup for fuzzy matching
    name_lookup = {}
    for entry in USATODAY_SALARIES:
        name, school, total_pay, school_pay, max_bonus, bonuses_paid, buyout, conf = entry
        norm_name = normalize_name(name)
        if norm_name not in name_lookup:
            name_lookup[norm_name] = []
        name_lookup[norm_name].append({
            "school": school,
            "total_pay": total_pay,
            "school_pay": school_pay,
            "max_bonus": max_bonus,
            "bonuses_paid": bonuses_paid,
            "buyout": buyout,
            "salary_source": "USA Today (Oct 2025)"
        })
    
    # Create assistant salary lookup
    assistant_lookup = {}
    for name, school, salary, position in ASSISTANT_SALARIES:
        key = (normalize_name(name), normalize_school(school))
        assistant_lookup[key] = {
            "total_pay": salary,
            "school_pay": salary,
            "max_bonus": None,
            "bonuses_paid": None,
            "buyout": None,
            "salary_source": "USA Today Assistants (Oct 2025)"
        }
    
    # Merge salaries
    matched = 0
    unmatched = []
    sources = {}
    
    for coach in roster:
        name = coach["name"]
        school = coach["school"]
        position = coach["position"]
        
        norm_name = normalize_name(name)
        norm_school = normalize_school(school)
        
        # Try exact match first
        key = (norm_name, norm_school)
        salary_data = None
        
        if key in salary_lookup:
            salary_data = salary_lookup[key]
        elif key in assistant_lookup and "Coordinator" in position:
            salary_data = assistant_lookup[key]
        elif norm_name in name_lookup:
            # Try name-only match
            for entry in name_lookup[norm_name]:
                salary_data = entry
                break
        
        if salary_data:
            coach["total_pay"] = salary_data["total_pay"]
            coach["school_pay"] = salary_data["school_pay"]
            coach["max_bonus"] = salary_data["max_bonus"] if salary_data["max_bonus"] else ""
            coach["bonuses_paid"] = salary_data["bonuses_paid"] if salary_data["bonuses_paid"] else ""
            coach["buyout"] = salary_data["buyout"] if salary_data["buyout"] else ""
            coach["salary_source"] = salary_data["salary_source"]
            matched += 1
            
            # Track sources
            source = salary_data["salary_source"]
            if source not in sources:
                sources[source] = 0
            sources[source] += 1
        else:
            coach["total_pay"] = ""
            coach["school_pay"] = ""
            coach["max_bonus"] = ""
            coach["bonuses_paid"] = ""
            coach["buyout"] = ""
            coach["salary_source"] = ""
            if coach["position"] == "Head Coach" and coach["division"] == "FBS":
                unmatched.append((name, school, position))
    
    # Write updated roster
    output_path = "/Users/vicmacmini/clawd/nightly-builds/coach-database/coach_roster_all.csv"
    fieldnames = ["name", "position", "school", "conference", "division", 
                  "total_pay", "school_pay", "max_bonus", "bonuses_paid", "buyout", "salary_source"]
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(roster)
    
    print(f"\nResults:")
    print(f"  Matched: {matched} coaches with salary data")
    print(f"  Total roster: {len(roster)} coaches")
    print(f"  Coverage: {matched/len(roster)*100:.1f}%")
    
    print(f"\nSources used:")
    for source, count in sorted(sources.items()):
        print(f"  {source}: {count} coaches")
    
    print(f"\nUnmatched FBS Head Coaches:")
    for name, school, pos in unmatched[:20]:
        print(f"  {name} ({school})")
    if len(unmatched) > 20:
        print(f"  ... and {len(unmatched) - 20} more")
    
    # Write sources JSON
    sources_output = {
        "generated": datetime.now().isoformat(),
        "primary_source": "USA Today Sports Data (sportsdata.usatoday.com)",
        "data_date": "October 2025",
        "note": "Salaries represent total compensation including base pay and guaranteed amounts",
        "coverage": {
            "total_coaches": len(roster),
            "with_salary": matched,
            "coverage_pct": round(matched/len(roster)*100, 1)
        },
        "sources_breakdown": sources
    }
    
    with open("/Users/vicmacmini/clawd/nightly-builds/coach-database/salary_sources.json", 'w') as f:
        json.dump(sources_output, f, indent=2)
    
    print(f"\nSaved salary_sources.json")
    print(f"\nDone! Updated {output_path}")
    
    return matched, len(USATODAY_SALARIES)

if __name__ == "__main__":
    main()
