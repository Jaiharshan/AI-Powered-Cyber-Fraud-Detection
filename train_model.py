from datetime import datetime, timezone
from pathlib import Path
import json
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split

DATASET_PATH = Path("dataset/spam.csv")
MODEL_PATH = Path("model.pkl")
VECTORIZER_PATH = Path("vectorizer.pkl")
METRICS_PATH = Path("artifacts/training_metrics.json")


def load_dataset(path):
    frame = pd.read_csv(path, encoding="latin-1", usecols=["v1", "v2"])
    frame = frame.rename(columns={"v1": "label", "v2": "message"})
    frame["label"] = frame["label"].map({"ham": 0, "spam": 1})
    frame["message"] = frame["message"].astype(str).str.strip()
    frame = frame.dropna(subset=["label", "message"])
    frame = frame[frame["message"].str.len() > 0]
    frame = frame.drop_duplicates(subset=["message"]).reset_index(drop=True)
    return frame


def train():
    data = load_dataset(DATASET_PATH)

    x_train, x_test, y_train, y_test = train_test_split(
        data["message"],
        data["label"],
        test_size=0.2,
        random_state=42,
        stratify=data["label"],
    )

    vectorizer = TfidfVectorizer(
        lowercase=True,
        strip_accents="unicode",
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.98,
        sublinear_tf=True,
    )

    x_train_vec = vectorizer.fit_transform(x_train)
    x_test_vec = vectorizer.transform(x_test)

    model = LogisticRegression(
        max_iter=2500,
        class_weight="balanced",
        C=2.0,
        solver="liblinear",
        random_state=42,
    )

    model.fit(x_train_vec, y_train)

    y_pred = model.predict(x_test_vec)
    y_prob = model.predict_proba(x_test_vec)[:, 1]

    metrics = {
        "dataset_rows": int(len(data)),
        "train_rows": int(len(x_train)),
        "test_rows": int(len(x_test)),
        "spam_ratio": float(data["label"].mean()),
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred)),
        "recall": float(recall_score(y_test, y_pred)),
        "f1_score": float(f1_score(y_test, y_pred)),
        "roc_auc": float(roc_auc_score(y_test, y_prob)),
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
    }

    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    VECTORIZER_PATH.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(model, MODEL_PATH)
    joblib.dump(vectorizer, VECTORIZER_PATH)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print(json.dumps(metrics, indent=2))
    print(f"Saved model to {MODEL_PATH.resolve()}")
    print(f"Saved vectorizer to {VECTORIZER_PATH.resolve()}")
    print(f"Saved metrics to {METRICS_PATH.resolve()}")


if __name__ == "__main__":
    train()
