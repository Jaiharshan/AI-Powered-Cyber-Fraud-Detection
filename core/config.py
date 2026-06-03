from pathlib import Path

MODEL_PATH = Path("model.pkl")
VECTORIZER_PATH = Path("vectorizer.pkl")
METRICS_PATH = Path("artifacts/training_metrics.json")
MAX_HISTORY_ROWS = 500

RISK_THEME = {
    "Low": {"accent": "#1f7a5c", "surface": "#ecf8f3"},
    "Medium": {"accent": "#9f5a00", "surface": "#fff3e3"},
    "High": {"accent": "#b94110", "surface": "#ffede6"},
    "Critical": {"accent": "#8f1636", "surface": "#ffe8ee"},
}

ACTION_BY_RISK = {
    "Low": "No immediate red flags found. Continue with standard caution.",
    "Medium": "Verify the sender and destination through an official channel before acting.",
    "High": "Do not click links or share credentials. Escalate this case for analyst review.",
    "Critical": "Block and report immediately. Treat this as active fraud in progress.",
}

PRIORITY_BY_RISK = {
    "Low": "P4",
    "Medium": "P3",
    "High": "P2",
    "Critical": "P1",
}

RISK_ORDER = {
    "Low": 1,
    "Medium": 2,
    "High": 3,
    "Critical": 4,
}
