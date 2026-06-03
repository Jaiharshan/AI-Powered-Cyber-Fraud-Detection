from datetime import datetime
import json
import joblib
import pandas as pd
import streamlit as st
from utils import assess_url, evaluate_text_input, is_url
from core.config import METRICS_PATH, MODEL_PATH, VECTORIZER_PATH


@st.cache_resource
def load_assets():
    if not MODEL_PATH.exists() or not VECTORIZER_PATH.exists():
        return None, None
    return joblib.load(MODEL_PATH), joblib.load(VECTORIZER_PATH)


@st.cache_data
def load_training_metrics():
    if not METRICS_PATH.exists():
        return {}
    try:
        return json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def classify_input(raw_input, mode, model, vectorizer):
    text = raw_input.strip()
    detected_type = "URL" if mode == "URL" or (mode == "Auto" and is_url(text)) else "Text"

    if detected_type == "URL":
        result = assess_url(text)
        verdict = "Fraud" if result["risk_score"] >= 60 else "Safe"
        return {
            "input_type": "URL",
            "risk_score": result["risk_score"],
            "risk_band": result["risk_band"],
            "verdict": verdict,
            "signals": result["signals"],
            "model_probability": None,
            "model_score": None,
            "heuristic_score": result["risk_score"],
            "normalized_value": result["normalized_url"],
        }

    result = evaluate_text_input(text, model, vectorizer)
    return {
        "input_type": "Text",
        "risk_score": result["risk_score"],
        "risk_band": result["risk_band"],
        "verdict": result["verdict"],
        "signals": result["signals"],
        "model_probability": result["model_probability"],
        "model_score": result["model_score"],
        "heuristic_score": result["heuristic_score"],
        "normalized_value": text,
    }


def build_history_row(result):
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "input_type": result["input_type"],
        "risk_score": int(result["risk_score"]),
        "risk_band": result["risk_band"],
        "verdict": result["verdict"],
        "preview": result["normalized_value"][:120],
    }


def parse_uploaded_file(uploaded_file):
    lower_name = uploaded_file.name.lower()
    if lower_name.endswith(".txt"):
        content = uploaded_file.getvalue().decode("utf-8", errors="ignore")
        rows = [line.strip() for line in content.splitlines() if line.strip()]
        return pd.DataFrame({"content": rows})

    if lower_name.endswith(".csv"):
        return pd.read_csv(uploaded_file)

    return None


def pick_text_columns(frame):
    return [
        column
        for column in frame.columns
        if str(frame[column].dtype) == "object" or str(frame[column].dtype).startswith("string")
    ]


def run_batch_scan(source_frame, selected_column, model, vectorizer):
    rows = []
    inputs = source_frame[selected_column].fillna("").astype(str).tolist()
    for raw_text in inputs:
        candidate = raw_text.strip()
        if not candidate:
            continue
        result = classify_input(candidate, "Auto", model, vectorizer)
        rows.append(
            {
                "input": candidate,
                "input_type": result["input_type"],
                "risk_score": result["risk_score"],
                "risk_band": result["risk_band"],
                "verdict": result["verdict"],
                "signal_count": len(result["signals"]),
                "signals": " | ".join(result["signals"]),
            }
        )

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows).sort_values("risk_score", ascending=False).reset_index(drop=True)
