import ipaddress
import re
from urllib.parse import parse_qs, urlparse

URL_KEYWORD_WEIGHTS = {
    "login": 10,
    "verify": 11,
    "account": 8,
    "security": 9,
    "update": 8,
    "wallet": 10,
    "bank": 9,
    "secure": 8,
    "recover": 9,
    "password": 12,
    "invoice": 9,
    "payment": 11,
}

TEXT_KEYWORD_WEIGHTS = {
    "urgent": 11,
    "immediately": 9,
    "verify": 9,
    "suspended": 10,
    "lottery": 12,
    "prize": 11,
    "winner": 10,
    "reward": 9,
    "gift": 8,
    "bank": 8,
    "payment": 10,
    "invoice": 9,
    "click": 7,
    "password": 12,
    "otp": 12,
    "pin": 11,
    "crypto": 8,
}

TEXT_REGEX_RULES = [
    (r"\b(act now|limited time|last chance)\b", 12, "Pressure language is present"),
    (r"\b(confirm your account|verify your account|reset your password)\b", 13, "Credential request phrasing is present"),
    (r"\b(win|won|claim)\b.{0,20}\b(prize|reward|cash|gift)\b", 14, "Prize-bait phrasing is present"),
    (r"\b(call now|contact support now)\b", 8, "Push-to-call phrasing is present"),
    (r"\b(payment failed|account locked|account suspended)\b", 12, "Threat-style account warning is present"),
]

SHORTENER_DOMAINS = {
    "bit.ly",
    "tinyurl.com",
    "t.co",
    "goo.gl",
    "ow.ly",
    "rb.gy",
    "cutt.ly",
    "is.gd",
}

SUSPICIOUS_TLDS = {
    "top",
    "xyz",
    "click",
    "gq",
    "ml",
    "work",
    "zip",
}


def clamp(value, min_value=0, max_value=100):
    return max(min_value, min(max_value, int(round(value))))


def risk_band(score):
    if score >= 80:
        return "Critical"
    if score >= 60:
        return "High"
    if score >= 35:
        return "Medium"
    return "Low"


def normalize_url(url):
    cleaned = url.strip()
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+\-.]*://", cleaned):
        cleaned = f"http://{cleaned}"
    return cleaned


def is_url(text):
    if not text or " " in text.strip():
        return False
    candidate = normalize_url(text)
    parsed = urlparse(candidate)
    return bool(parsed.netloc and "." in parsed.netloc)


def _dedupe_in_order(items):
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def extract_url_features(url):
    return assess_url(url)["signals"]


def assess_url(url):
    normalized = normalize_url(url)
    parsed = urlparse(normalized)
    host = (parsed.hostname or "").lower()
    full_url_lower = normalized.lower()
    signals = []
    score = 0

    if parsed.scheme != "https":
        score += 12
        signals.append("URL does not use HTTPS")

    if "@" in normalized:
        score += 16
        signals.append("URL contains an @ symbol")

    if len(normalized) > 80:
        score += 10
        signals.append("URL length is unusually high")

    host_parts = [part for part in host.split(".") if part]
    if len(host_parts) >= 4:
        score += 10
        signals.append("Domain has many nested subdomains")

    if "-" in host:
        score += 6
        signals.append("Domain uses hyphenation often seen in spoofing")

    if host.startswith("xn--"):
        score += 12
        signals.append("Domain uses punycode")

    try:
        ipaddress.ip_address(host)
        score += 20
        signals.append("Domain is an IP address")
    except ValueError:
        pass

    tld = host_parts[-1] if host_parts else ""
    if tld in SUSPICIOUS_TLDS:
        score += 8
        signals.append(f"Top-level domain .{tld} has elevated abuse rates")

    query_params = parse_qs(parsed.query, keep_blank_values=True)
    if len(query_params) >= 5:
        score += 8
        signals.append("URL contains many query parameters")

    if normalized.count("%") >= 3:
        score += 5
        signals.append("URL contains heavy encoding")

    keyword_hits = [word for word in URL_KEYWORD_WEIGHTS if word in full_url_lower]
    if keyword_hits:
        keyword_score = min(25, sum(URL_KEYWORD_WEIGHTS[word] for word in keyword_hits))
        score += keyword_score
        joined_hits = ", ".join(keyword_hits[:5])
        signals.append(f"Sensitive trigger words found: {joined_hits}")

    if parsed.path.count("/") >= 6:
        score += 6
        signals.append("URL path depth is unusually high")

    final_score = clamp(score)
    return {
        "normalized_url": normalized,
        "domain": host,
        "risk_score": final_score,
        "risk_band": risk_band(final_score),
        "signals": _dedupe_in_order(signals),
    }


def extract_text_reasons(text):
    return score_text_signals(text)["signals"]


def _extract_url_candidates(text):
    pattern = re.compile(r"https?://[^\s]+")
    return pattern.findall(text)


def score_text_signals(text):
    lower = text.lower()
    score = 0
    signals = []

    keyword_hits = []
    for word, weight in TEXT_KEYWORD_WEIGHTS.items():
        if re.search(rf"\b{re.escape(word)}\b", lower):
            keyword_hits.append(word)
            score += weight

    if keyword_hits:
        score += min(20, len(keyword_hits) * 2)
        hit_text = ", ".join(keyword_hits[:7])
        signals.append(f"Risk keywords detected: {hit_text}")

    for pattern, weight, description in TEXT_REGEX_RULES:
        if re.search(pattern, lower):
            score += weight
            signals.append(description)

    if len(text) >= 250:
        score += 6
        signals.append("Message length is unusually long")

    if text.count("!") >= 4:
        score += 4
        signals.append("Message uses excessive exclamation")

    if re.search(r"\b\d{6}\b", text):
        score += 6
        signals.append("Contains 6-digit code pattern")

    url_candidates = _extract_url_candidates(text)
    if url_candidates:
        score += 8
        signals.append("Contains embedded URL")
        for candidate in url_candidates:
            parsed = urlparse(candidate)
            domain = (parsed.hostname or "").lower()
            if domain in SHORTENER_DOMAINS:
                score += 8
                signals.append("Uses a URL shortener")
                break

    final_score = clamp(score)
    return {
        "risk_score": final_score,
        "risk_band": risk_band(final_score),
        "signals": _dedupe_in_order(signals),
    }


def evaluate_text_input(text, model, vectorizer):
    transformed = vectorizer.transform([text])
    if hasattr(model, "predict_proba"):
        spam_probability = float(model.predict_proba(transformed)[0][1])
    else:
        raw_score = float(model.decision_function(transformed)[0])
        spam_probability = 1 / (1 + pow(2.718281828, -raw_score))

    model_score = clamp(spam_probability * 100)
    signal_result = score_text_signals(text)
    heuristic_score = signal_result["risk_score"]
    blended_score = clamp((model_score * 0.72) + (heuristic_score * 0.28))
    verdict = "Fraud" if blended_score >= 60 else "Safe"

    return {
        "risk_score": blended_score,
        "risk_band": risk_band(blended_score),
        "model_probability": spam_probability,
        "model_score": model_score,
        "heuristic_score": heuristic_score,
        "verdict": verdict,
        "signals": signal_result["signals"],
    }
