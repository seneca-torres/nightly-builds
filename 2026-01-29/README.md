# Session Cost Dashboard

A clean, dark-themed dashboard for visualizing API usage costs.

## Features

- **Current Session Card** - Shows active session cost with budget progress bar
- **Daily/Weekly Totals** - Cost summaries with trend indicators
- **7-Day Bar Chart** - Visual breakdown of daily spending
- **Model Breakdown** - Cost per model (Opus, Sonnet, Grok)
- **Token Usage** - Input/output token counts
- **Rate Limits** - 5-hour and weekly quota status
- **Auto-refresh indicator** - Simulated live updates

## Screenshot

```
┌─────────────────────────────────────────────────┐
│ 📊 Session Cost Dashboard     ● Auto-refresh    │
├───────────────┬───────────────┬─────────────────┤
│ Current       │ Today's Cost  │ This Week       │
│ ⚡ $2.47      │ 📅 $8.42      │ 📈 $54.18       │
│ ████░░░░ 18% │ ↓23% vs yest  │ Avg: $7.74/day  │
├───────────────┴───────────────┴─────────────────┤
│ Daily Cost (Last 7 Days)                        │
│ ▓▓▓  ▓▓   ▓▓▓▓  ▓▓   ▓▓▓  ▓    ▓▓             │
│ Mon  Tue  Wed   Thu  Fri  Sat  Sun              │
└─────────────────────────────────────────────────┘
```

## How to Use

1. Open `index.html` in a browser
2. View your (mock) API costs at a glance

## Customization

To integrate with real data:

1. Replace the `dailyData` array in the `<script>` section with actual cost data
2. Update the card values by fetching from `session_status` or a cost tracking API
3. Adjust the model breakdown to match your actual usage

## Tech Stack

- Pure HTML/CSS/JS (no dependencies)
- CSS Grid/Flexbox for responsive layout
- CSS animations for live indicators
- Dark theme with navy/slate palette

## Notes

This is a **mock dashboard** showing sample data. It demonstrates the UI/UX for tracking API costs. To make it functional:

- Add a backend to aggregate session_status data over time
- Store daily costs in a JSON file or simple database
- Update the JavaScript to fetch real data periodically

---

*Built during Nightly Build 2026-01-29 by Seneca*
