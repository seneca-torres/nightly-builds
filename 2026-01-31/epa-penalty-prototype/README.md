# EPA/Penalty Impact Chart Prototype

A visualization prototype showing how penalties impact a team's Expected Points Added (EPA) during a game.

## Features

- **Cumulative EPA Chart**: Shows both teams' EPA progression through the game
- **Penalty Markers**: Highlights where penalties occurred with color-coded severity
- **Interactive Tooltips**: Hover over penalty markers for details
- **Impact Table**: Summary of all penalties ranked by EPA impact

## Screenshot

Open `index.html` in a browser to see the visualization.

## How It Works

1. **EPA (Expected Points Added)**: Measures how much each play changes the expected points for the offense
2. **Penalty Impact**: Calculated as the EPA difference caused by the penalty (yards lost, down reset, etc.)
3. **Color Coding**:
   - 🔴 Red markers: Harmful penalties (>1 EPA impact)
   - 🟡 Yellow markers: Minor penalties (<1 EPA impact)

## Data Source

Currently using **sample data** to demonstrate the concept.

To use real data:
1. Get a CFBD API key from [collegefootballdata.com](https://collegefootballdata.com)
2. Fetch play-by-play data with EPA values
3. Replace the `generateSamplePlays()` function with API data

## CFBD API Endpoints Needed

```bash
# Get game plays with EPA
GET /plays?year=2024&week=1&team=Purdue

# Response includes:
# - play_number
# - play_type  
# - play_text
# - epa (Expected Points Added)
# - penalty_flag (boolean)
# - penalty_text
# - penalty_yards
```

## Next Steps

1. [ ] Add CFBD API integration
2. [ ] Game selector dropdown
3. [ ] Filter by penalty type
4. [ ] Win Probability overlay option
5. [ ] Export data as CSV

## Credits

Built with D3.js for Victor's sports analytics research.

---

*Prototype v0.1 - January 31, 2026*
