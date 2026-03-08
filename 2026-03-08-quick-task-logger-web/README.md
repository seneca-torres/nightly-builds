# Quick Task Logger (stdlib only)

A minimal local web app to quickly log notes into daily markdown files.

## Features

- Textarea for quick entry
- Optional category: `event`, `idea`, `todo`
- Saves to `~/clawd/memory/daily/YYYY-MM-DD.md`
- Shows recent entries in the UI
- Python standard library only (no Flask)

## Files

- `server.py` - HTTP server + API + static file serving
- `index.html` - UI
- `style.css` - styling

## Run

```bash
python3 server.py
```

Open: `http://localhost:8080`

## API

- `POST /log`
  - JSON body:
    ```json
    {"text":"Buy milk","category":"todo"}
    ```
  - `category` is optional.
- `GET /entries`
  - Returns recent entries as JSON.