# Systems Dashboard

Single-page dashboard showing cron jobs, service status, nightly build history, project inventory, and health metrics.

## Files
- `index.html` — dashboard UI (embedded CSS/JS)
- `data.sh` — generates JSON payload for the UI

## Usage
1. Generate data:
   ```bash
   ./data.sh > data.json
   ```
2. Serve the folder:
   ```bash
   python3 -m http.server 8080
   ```
3. Open: `http://localhost:8080/index.html`

## Auto-refresh
The UI refreshes every 60s. To keep data fresh, run the data script on a schedule, for example:
```bash
*/1 * * * * /home/victorres11/clawd/nightly-builds/2026-01-28/data.sh > /home/victorres11/clawd/nightly-builds/2026-01-28/data.json
```

## Notes
- Cron job last run/next run timestamps are not available from cron by default; the dashboard shows `unknown` unless you add logging.
- CPU temperature reads from `/sys/class/thermal/thermal_zone0/temp`, with a `vcgencmd` fallback if available.
