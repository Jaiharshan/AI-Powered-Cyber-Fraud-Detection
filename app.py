import json
import pandas as pd
import streamlit as st
from core.analysis import (
    build_history_row,
    classify_input,
    load_assets,
    load_training_metrics,
    parse_uploaded_file,
    pick_text_columns,
    run_batch_scan,
)
from core.config import ACTION_BY_RISK, MAX_HISTORY_ROWS, RISK_THEME
from core.incidents import create_incident, queue_to_frame, resolve_incidents, upsert_incident
from core.styles import GLOBAL_STYLE

st.set_page_config(
    page_title="FraudShield Console",
    page_icon=":shield:",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(GLOBAL_STYLE, unsafe_allow_html=True)


def render_result(result):
    theme = RISK_THEME[result["risk_band"]]
    st.markdown(
        f"""
        <div class="result-card" style="background:{theme['surface']}; border-left:7px solid {theme['accent']};">
            <h3 class="result-title" style="color:{theme['accent']};">{result['risk_band']} Risk</h3>
            <p class="result-subtitle">{result['verdict']} classification for {result['input_type']} input</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Risk Score", f"{result['risk_score']}%")
    col2.metric("Verdict", result["verdict"])
    col3.metric("Signals", str(len(result["signals"])))

    if result["model_probability"] is None:
        col4.metric("Model Signal", "N/A")
    else:
        col4.metric("Model Signal", f"{result['model_probability'] * 100:.1f}%")

    st.progress(result["risk_score"] / 100)
    st.write(ACTION_BY_RISK[result["risk_band"]])

    if result["signals"]:
        st.subheader("Why this was flagged")
        for signal in result["signals"]:
            st.write(f"- {signal}")
    else:
        st.success("No significant suspicious signals were detected.")


model, vectorizer = load_assets()
training_metrics = load_training_metrics()

if "scan_history" not in st.session_state:
    st.session_state.scan_history = []

if "incident_queue" not in st.session_state:
    st.session_state.incident_queue = []

st.markdown(
    """
    <div class="hero">
        <h1>FraudShield Console</h1>
        <p>Operational cyber-fraud screening for messages, URLs, and bulk communication datasets.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if model is None or vectorizer is None:
    st.error("Model artifacts are missing. Run train_model.py to generate model.pkl and vectorizer.pkl.")
    st.stop()

with st.sidebar:
    st.header("System Snapshot")
    if training_metrics:
        st.metric("Model Accuracy", f"{training_metrics.get('accuracy', 0) * 100:.2f}%")
        st.metric("F1 Score", f"{training_metrics.get('f1_score', 0) * 100:.2f}%")
        st.metric("ROC-AUC", f"{training_metrics.get('roc_auc', 0) * 100:.2f}%")
        st.caption(f"Last Training: {training_metrics.get('trained_at_utc', 'Unknown')}")

    st.metric("Session Scans", str(len(st.session_state.scan_history)))
    open_incident_count = sum(1 for row in st.session_state.incident_queue if row.get("status") == "Open")
    st.metric("Open Incidents", str(open_incident_count))

    alert_threshold = st.slider("Auto Escalation Threshold", min_value=45, max_value=85, value=60, step=5)

    if st.button("Clear Session History", use_container_width=True):
        st.session_state.scan_history = []

    if st.button("Clear Incident Queue", use_container_width=True):
        st.session_state.incident_queue = []

scan_tab, batch_tab, ops_tab = st.tabs(["Live Scanner", "Batch Scanner", "Ops Center"])

with scan_tab:
    mode = st.radio("Input Mode", options=["Auto", "Text", "URL"], horizontal=True)
    user_input = st.text_area(
        "Enter message, email body, or URL",
        height=170,
        placeholder="Paste a suspicious message or URL to analyze...",
    )

    if st.button("Run Fraud Scan", use_container_width=True, type="primary"):
        if not user_input.strip():
            st.warning("Enter text to scan.")
        else:
            result = classify_input(user_input, mode, model, vectorizer)
            render_result(result)

            st.session_state.scan_history.insert(0, build_history_row(result))
            st.session_state.scan_history = st.session_state.scan_history[:MAX_HISTORY_ROWS]

            incident = create_incident(result, source="Live", threshold=alert_threshold)
            if incident:
                action = upsert_incident(st.session_state.incident_queue, incident)
                if action == "created":
                    st.error(f"Incident escalated as {incident['priority']} and added to Ops Center.")
                else:
                    st.warning("Incident queue updated for repeated suspicious activity.")

with batch_tab:
    uploaded = st.file_uploader("Upload CSV or TXT", type=["csv", "txt"])
    if uploaded:
        source_frame = parse_uploaded_file(uploaded)

        if source_frame is None:
            st.error("Unsupported file type. Use CSV or TXT.")
        else:
            text_columns = pick_text_columns(source_frame)
            if not text_columns:
                st.error("No text-like column was found in the uploaded file.")
            else:
                selected_column = st.selectbox("Choose column to scan", options=text_columns)

                if st.button("Analyze Batch", use_container_width=True, type="primary"):
                    with st.spinner("Analyzing uploaded rows..."):
                        batch_results = run_batch_scan(source_frame, selected_column, model, vectorizer)

                    if batch_results.empty:
                        st.warning("No valid rows were found for analysis.")
                    else:
                        high_risk_count = int((batch_results["risk_score"] >= 60).sum())
                        escalated_count = int((batch_results["risk_score"] >= alert_threshold).sum())

                        metric1, metric2, metric3, metric4 = st.columns(4)
                        metric1.metric("Rows Scanned", str(len(batch_results)))
                        metric2.metric("High/Critical", str(high_risk_count))
                        metric3.metric("Auto Escalated", str(escalated_count))
                        metric4.metric("Average Risk", f"{batch_results['risk_score'].mean():.1f}%")

                        st.dataframe(batch_results, use_container_width=True)
                        st.download_button(
                            "Download Results CSV",
                            data=batch_results.to_csv(index=False).encode("utf-8"),
                            file_name="fraud_scan_results.csv",
                            mime="text/csv",
                            use_container_width=True,
                        )

                        for row in batch_results.itertuples(index=False):
                            result_stub = {
                                "input_type": row.input_type,
                                "risk_score": int(row.risk_score),
                                "risk_band": row.risk_band,
                                "verdict": row.verdict,
                                "normalized_value": row.input,
                            }
                            st.session_state.scan_history.insert(0, build_history_row(result_stub))

                            incident = create_incident(result_stub, source="Batch", threshold=alert_threshold)
                            if incident:
                                upsert_incident(st.session_state.incident_queue, incident)

                        st.session_state.scan_history = st.session_state.scan_history[:MAX_HISTORY_ROWS]

with ops_tab:
    st.subheader("Incident Queue")
    queue_frame = queue_to_frame(st.session_state.incident_queue)

    if queue_frame.empty:
        st.info("No incidents escalated yet.")
    else:
        open_count = int((queue_frame["status"] == "Open").sum())
        resolved_count = int((queue_frame["status"] == "Resolved").sum())
        critical_open = int(((queue_frame["status"] == "Open") & (queue_frame["risk_band"] == "Critical")).sum())

        m1, m2, m3 = st.columns(3)
        m1.metric("Open", str(open_count))
        m2.metric("Resolved", str(resolved_count))
        m3.metric("Critical Open", str(critical_open))

        open_ids = queue_frame.loc[queue_frame["status"] == "Open", "incident_id"].tolist()
        selected_to_resolve = st.multiselect("Mark incidents as resolved", options=open_ids)
        if st.button("Resolve Selected", use_container_width=True):
            resolved_now = resolve_incidents(st.session_state.incident_queue, selected_to_resolve)
            if resolved_now:
                st.success(f"Resolved {resolved_now} incident(s).")
                st.rerun()
            else:
                st.info("No incident was updated.")

        st.dataframe(queue_frame, use_container_width=True)

        left_download, right_download = st.columns(2)
        left_download.download_button(
            "Download Queue CSV",
            data=queue_frame.to_csv(index=False).encode("utf-8"),
            file_name="incident_queue.csv",
            mime="text/csv",
            use_container_width=True,
        )
        right_download.download_button(
            "Download Queue JSON",
            data=json.dumps(st.session_state.incident_queue, indent=2),
            file_name="incident_queue.json",
            mime="application/json",
            use_container_width=True,
        )

    st.subheader("Model Performance")
    if training_metrics:
        metrics_frame = pd.DataFrame(
            [
                {"Metric": "Accuracy", "Value": training_metrics.get("accuracy", 0)},
                {"Metric": "Precision", "Value": training_metrics.get("precision", 0)},
                {"Metric": "Recall", "Value": training_metrics.get("recall", 0)},
                {"Metric": "F1 Score", "Value": training_metrics.get("f1_score", 0)},
                {"Metric": "ROC-AUC", "Value": training_metrics.get("roc_auc", 0)},
            ]
        )
        st.dataframe(metrics_frame, use_container_width=True)
    else:
        st.info("Training metrics file not found. Run train_model.py to generate metrics.")

    st.subheader("Session Scan Trends")
    if not st.session_state.scan_history:
        st.info("No session scans available yet.")
    else:
        history_frame = pd.DataFrame(st.session_state.scan_history)
        distribution = history_frame["risk_band"].value_counts().rename_axis("risk_band").reset_index(name="count")

        left, right = st.columns(2)
        left.dataframe(
            history_frame[["timestamp", "input_type", "risk_score", "risk_band", "verdict", "preview"]],
            use_container_width=True,
        )
        right.dataframe(distribution, use_container_width=True)

        chart_frame = history_frame[["timestamp", "risk_score"]].copy()
        chart_frame["timestamp"] = pd.to_datetime(chart_frame["timestamp"])
        chart_frame = chart_frame.sort_values("timestamp").set_index("timestamp")
        st.line_chart(chart_frame)
