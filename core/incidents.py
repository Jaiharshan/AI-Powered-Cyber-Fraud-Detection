import hashlib
from datetime import datetime
import pandas as pd
from core.config import ACTION_BY_RISK, PRIORITY_BY_RISK, RISK_ORDER


def _risk_band_max(current, candidate):
    if RISK_ORDER[candidate] > RISK_ORDER[current]:
        return candidate
    return current


def create_incident(result, source, threshold):
    if int(result["risk_score"]) < int(threshold):
        return None

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    normalized = result["normalized_value"].strip().lower()
    fingerprint = hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:12]

    return {
        "incident_id": f"INC-{now.replace('-', '').replace(':', '').replace(' ', '-')}-{fingerprint[:4]}",
        "fingerprint": fingerprint,
        "first_seen": now,
        "last_seen": now,
        "source": source,
        "input_type": result["input_type"],
        "risk_score": int(result["risk_score"]),
        "risk_band": result["risk_band"],
        "priority": PRIORITY_BY_RISK[result["risk_band"]],
        "status": "Open",
        "hits": 1,
        "recommended_action": ACTION_BY_RISK[result["risk_band"]],
        "preview": result["normalized_value"][:120],
    }


def upsert_incident(queue, incident):
    for row in queue:
        if row["fingerprint"] == incident["fingerprint"] and row["status"] == "Open":
            row["hits"] = int(row["hits"]) + 1
            row["last_seen"] = incident["last_seen"]
            row["risk_score"] = max(int(row["risk_score"]), int(incident["risk_score"]))
            row["risk_band"] = _risk_band_max(row["risk_band"], incident["risk_band"])
            row["priority"] = PRIORITY_BY_RISK[row["risk_band"]]
            row["recommended_action"] = ACTION_BY_RISK[row["risk_band"]]
            if incident["source"] not in row["source"].split(", "):
                row["source"] = f"{row['source']}, {incident['source']}"
            return "updated"

    queue.insert(0, incident)
    return "created"


def resolve_incidents(queue, incident_ids):
    if not incident_ids:
        return 0

    resolved_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    resolved_count = 0

    for row in queue:
        if row["incident_id"] in incident_ids and row["status"] == "Open":
            row["status"] = "Resolved"
            row["resolved_at"] = resolved_at
            resolved_count += 1

    return resolved_count


def queue_to_frame(queue, status="all"):
    if not queue:
        return pd.DataFrame()

    frame = pd.DataFrame(queue)

    if status == "open":
        frame = frame[frame["status"] == "Open"]
    elif status == "resolved":
        frame = frame[frame["status"] == "Resolved"]

    if frame.empty:
        return frame

    priority_order = {"P1": 1, "P2": 2, "P3": 3, "P4": 4}
    frame["priority_rank"] = frame["priority"].map(priority_order).fillna(5)
    frame = frame.sort_values(["priority_rank", "risk_score", "last_seen"], ascending=[True, False, False])
    frame = frame.drop(columns=["priority_rank", "fingerprint"], errors="ignore")
    return frame.reset_index(drop=True)
