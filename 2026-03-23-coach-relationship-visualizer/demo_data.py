#!/usr/bin/env python3
"""
Demo data generator for Coach Relationship Visualizer.
Creates sample broadcaster notes for testing.
"""

import os
import yaml
from datetime import datetime
from pathlib import Path

def create_demo_notes(output_dir="demo_notes"):
    """Create sample broadcaster notes for testing."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    demo_notes = [
        {
            "filename": "alabama_coaching_2024.md",
            "content": """---
title: "Alabama Coaching Staff Analysis 2024"
date: "2024-08-15"
coaches: ["Kalen DeBoer", "Nick Sheridan", "Kane Wommack", "JaMarcus Shephard"]
schools: ["Alabama", "Washington", "Indiana", "Purdue"]
tags: ["SEC", "coaching changes", "offensive scheme"]
---
# Alabama Coaching Staff 2024

Following Nick Saban's retirement, Alabama hired **Kalen DeBoer** from Washington. DeBoer brings his offensive coordinator **Nick Sheridan** and defensive coordinator **Kane Wommack**.

## Key Observations:
- DeBoer had tremendous success at Washington, going 25-3 in two seasons
- Sheridan worked with DeBoer at Indiana before Washington
- Wommack was previously head coach at South Alabama
- JaMarcus Shephard joins as WR coach from Washington

This staff represents a significant philosophical shift from the Saban era.
"""
        },
        {
            "filename": "michigan_transition_2024.md",
            "content": """---
title: "Michigan Coaching Transition"
date: "2024-01-30"
coaches: ["Sherrone Moore", "Jim Harbaugh", "Jesse Minter", "Mike Macdonald"]
schools: ["Michigan", "Los Angeles Chargers", "Baltimore Ravens"]
tags: ["Big Ten", "NFL", "defensive scheme"]
---
# Michigan's Coaching Transition

With Jim Harbaugh leaving for the NFL, **Sherrone Moore** was promoted to head coach. Moore served as interim coach during Harbaugh's 2023 suspension.

## Defensive Staff Changes:
- **Jesse Minter** followed Harbaugh to the Chargers as DC
- **Mike Macdonald** (former Michigan DC) is now head coach of the Seahawks
- New DC expected to come from Baltimore Ravens tree

Moore retains most offensive staff but needs to rebuild defensive side.
"""
        },
        {
            "filename": "sec_coaching_moves_2023.md",
            "content": """---
title: "SEC Coaching Moves 2023"
date: "2023-12-10"
coaches: ["Billy Napier", "Hugh Freeze", "Zach Arnett", "Kevin Steele"]
schools: ["Florida", "Auburn", "Mississippi State", "Alabama"]
tags: ["SEC", "offensive struggles", "defensive coordinators"]
---
# SEC Coaching Changes 2023

Several SEC programs made coordinator changes after disappointing seasons.

## Florida:
- **Billy Napier** under pressure after 5-7 season
- Considering offensive coordinator change
- Defense improved under **Austin Armstrong**

## Auburn:
- **Hugh Freeze** completes first season 6-6
- Made defensive staff changes
- Offense showed flashes with Payton Thorne

## Mississippi State:
- **Zach Arnett** fired after one season
- Program searching for new identity post-Leach
"""
        },
        {
            "filename": "big_12_offensive_coordinators.md",
            "content": """---
title: "Big 12 Offensive Coordinators 2024"
date: "2024-03-01"
coaches: ["Jeff Lebby", "Brennan Marion", "Josh Gattis", "Phil Longo"]
schools: ["Oklahoma State", "UNLV", "Maryland", "Wisconsin", "Mississippi State"]
tags: ["Big 12", "offensive innovation", "air raid", "spread"]
---
# Big 12 Offensive Coordinator Landscape

The Big 12 continues to be a conference of offensive innovation.

## Notable Hires:
- **Jeff Lebby** from Mississippi State to Oklahoma State as HC
- **Brennan Marion** from UNLV to Oklahoma State as OC
- **Josh Gattis** at Maryland after Wisconsin stint
- **Phil Longo** brings air raid to Wisconsin

The conference features diverse offensive schemes from air raid to pro-style.
"""
        },
        {
            "filename": "pac_12_final_season.md",
            "content": """---
title: "PAC-12 Final Season Coaching Notes"
date: "2023-11-20"
coaches: ["Dan Lanning", "Kyle Whittingham", "Jonathan Smith", "Lincoln Riley"]
schools: ["Oregon", "Utah", "Michigan State", "USC", "Oregon State"]
tags: ["PAC-12", "conference realignment", "defensive excellence"]
---
# PAC-12's Final Season

With conference realignment, 2023 was the final season of the PAC-12 as we know it.

## Standout Coaches:
- **Dan Lanning** has Oregon competing for championships
- **Kyle Whittingham** continues defensive excellence at Utah
- **Jonathan Smith** leaves Oregon State for Michigan State
- **Lincoln Riley**'s offense still potent at USC

These coaches will be scattered across Big Ten, Big 12, and ACC in 2024.
"""
        }
    ]
    
    created_files = []
    for note in demo_notes:
        filepath = output_path / note["filename"]
        with open(filepath, 'w') as f:
            f.write(note["content"])
        created_files.append(filepath)
    
    return created_files

def generate_graph_from_demo():
    """Generate graph JSON from demo notes."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    
    # Import and use the parser
    from parser import RelationshipParser
    
    print("Creating demo notes...")
    demo_files = create_demo_notes()
    
    print(f"Created {len(demo_files)} demo note files")
    
    # Parse the demo notes
    parser = RelationshipParser()
    for filepath in demo_files:
        parser.parse_markdown_file(filepath)
    
    # Generate graph JSON
    graph_data = parser.to_graph_json()
    
    # Save to file
    output_file = Path(__file__).parent / "data" / "demo_graph.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        import json
        json.dump(graph_data, f, indent=2)
    
    print(f"\nGraph data saved to: {output_file}")
    print(f"Total coaches: {len(parser.coaches)}")
    print(f"Total schools: {len(parser.schools)}")
    print(f"Total relationships: {len(parser.relationships)}")
    
    # Also save web version
    web_file = Path(__file__).parent / "visualizer" / "web_graph.json"
    with open(web_file, 'w') as f:
        json.dump(graph_data, f)
    
    print(f"Web version: {web_file}")
    
    return graph_data

if __name__ == "__main__":
    print("🎮 Coach Relationship Visualizer - Demo Data Generator")
    print("=" * 60)
    
    data = generate_graph_from_demo()
    
    print("\n✅ Demo data generated successfully!")
    print("\nNext steps:")
    print("1. Start web server: python3 -m http.server 8000")
    print("2. Open browser: http://localhost:8000/visualizer/")
    print("3. Explore the relationships!")
    
    # Show sample of what was generated
    print("\n📊 Sample data generated:")
    print(f"  Nodes: {len(data['nodes'])} (coaches: {len([n for n in data['nodes'] if n['type'] == 'coach'])}, schools: {len([n for n in data['nodes'] if n['type'] == 'school'])})")
    print(f"  Edges: {len(data['edges'])} relationships")