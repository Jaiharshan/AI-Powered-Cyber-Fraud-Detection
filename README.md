CyberFraudDetection

Overview
This project is a Streamlit-based fraud detection console for screening suspicious text messages, emails, and URLs. It combines ML scoring with rule-based signals and now includes a real-time incident queue for security operations.

Special Feature Added
Real-time Incident Queue with Auto Escalation
- Every scan with risk score above your selected threshold is automatically escalated.
- Repeated detections of the same payload are merged and tracked with hit count.
- Each incident gets a priority level (P1-P4), status, and recommended response action.
- Incidents can be resolved inside the Ops Center and exported as CSV or JSON.

Primary Use Cases
1. SOC triage for phishing and fraud reports:
   Analysts paste suspicious emails/URLs and instantly get a risk band, signals, and next action.
2. Fraud checks for customer support workflows:
   Support teams can scan incoming customer messages before responding.
3. Batch screening for campaign monitoring:
   Teams upload CSV/TXT communication logs and quickly identify high-risk rows.

How to Use in Real Time
1. Start the app and open Live Scanner.
2. Paste incoming suspicious message/URL from chat, email, or ticket.
3. Run scan and review risk signals.
4. High-risk items are auto-added to Ops Center Incident Queue.
5. Use Ops Center to prioritize response, resolve incidents, and export queue for reporting.

Run Commands (Windows PowerShell)
1. Create and activate virtual environment:
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

2. Install dependencies:
   pip install -r requirements.txt

3. Train model artifacts (first run or retraining):
   python train_model.py

4. Launch application:
   streamlit run app.py

Expected Local URL
http://localhost:8501

Project Structure
- app.py: Streamlit UI and workflow wiring
- core/config.py: Paths, risk themes, action mapping, priority map
- core/styles.py: Centralized UI theme and CSS styling
- core/analysis.py: Asset loading, input classification, batch scanning
- core/incidents.py: Incident creation, queue upsert, resolution, exports
- utils.py: Fraud heuristics and text/url scoring helpers
- train_model.py: Model training and metrics generation
- artifacts/training_metrics.json: Latest training metrics
- dataset/spam.csv: Training dataset
