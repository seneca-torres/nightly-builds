#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEMO_FILE="$ROOT_DIR/demo.html"

if [[ ! -f "$DEMO_FILE" ]]; then
  echo "FAIL: demo.html not found at $DEMO_FILE"
  exit 1
fi

if ! command -v node >/dev/null 2>&1; then
  echo "FAIL: node is required to run verification."
  exit 1
fi

node - "$DEMO_FILE" <<'EOF_NODE'
const fs = require("fs");

const filePath = process.argv[2];
const html = fs.readFileSync(filePath, "utf8");
const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/i);
if (!scriptMatch) {
  fail("No inline <script> found in demo.html");
}

const localStore = {
  "victor-portfolio-theme": "light"
};

const root = {
  attrs: { "data-theme": "light" },
  setAttribute(name, value) {
    this.attrs[name] = value;
  },
  getAttribute(name) {
    return this.attrs[name] || null;
  }
};

const toggleButton = {
  attrs: {},
  textContent: "",
  listeners: {},
  setAttribute(name, value) {
    this.attrs[name] = value;
  },
  addEventListener(event, cb) {
    this.listeners[event] = cb;
  }
};

const status = {
  textContent: ""
};

global.document = {
  documentElement: root,
  getElementById(id) {
    if (id === "themeToggle") return toggleButton;
    if (id === "themeStatus") return status;
    return null;
  }
};

global.window = {
  matchMedia() {
    return { matches: false };
  }
};

global.localStorage = {
  getItem(key) {
    return Object.prototype.hasOwnProperty.call(localStore, key) ? localStore[key] : null;
  },
  setItem(key, val) {
    localStore[key] = String(val);
  }
};

function fail(message) {
  console.error("FAIL:", message);
  process.exit(1);
}

try {
  eval(scriptMatch[1]);
} catch (err) {
  fail("Inline script threw an error: " + err.message);
}

if (root.getAttribute("data-theme") !== "light") {
  fail("Expected startup theme to be light from localStorage.");
}

if (toggleButton.textContent !== "Switch to dark mode") {
  fail("Expected startup button label to target dark mode.");
}

if (typeof toggleButton.listeners.click !== "function") {
  fail("Toggle button click listener not attached.");
}

toggleButton.listeners.click();

if (root.getAttribute("data-theme") !== "dark") {
  fail("Expected theme to switch to dark on click.");
}

if (localStore["victor-portfolio-theme"] !== "dark") {
  fail("Expected localStorage preference to be updated to dark.");
}

if (status.textContent !== "Dark mode is active") {
  fail("Expected status text to indicate dark mode.");
}

console.log("PASS: toggle initializes and updates theme/localStorage correctly.");
EOF_NODE
