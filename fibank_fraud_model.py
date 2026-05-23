"""
fibank Fraud Detection — Synthetic Dataset + XGBoost Model
------------------------------------------------------------
Generates a realistic synthetic dataset from the fibank schema,
engineers features, trains an XGBoost classifier, and reports
probability of fraud per transaction.

USAGE
-----
  # First run or force retrain:
  python fibank_fraud_model.py --retrain

  # Subsequent runs (loads saved model, skips retraining):
  python fibank_fraud_model.py

  # Predict a single transaction (JSON string):
  python fibank_fraud_model.py --predict '{"amount": 5000, "recipient_is_new": true, ...}'

OUTPUT FILES
------------
  fibank_fraud_model.ubj                  — Saved XGBoost model (binary)
  fibank_model_meta.json                  — Feature list + column docs (for integrators)
  transactions_with_fraud_scores.csv      — All transactions with fraud_probability column
  feature_importance.csv                  — Feature importance ranking
  synthetic_users.csv                     — Generated user table
  synthetic_transactions.csv              — Generated raw transaction table
"""

import os
import json
import argparse
import warnings

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from faker import Faker
from sklearn.model_selection import train_test_split
from sklearn.metrics import (roc_auc_score, classification_report,
                             average_precision_score)
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb

warnings.filterwarnings("ignore")

fake = Faker()
rng = np.random.default_rng(42)

# ── File paths ────────────────────────────────────────────────────────────────

# All output files go into an "outputs/" subfolder next to this script.
_HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(_HERE, "outputs")
MODEL_PATH = os.path.join(OUT_DIR, "fibank_fraud_model.ubj")
META_PATH = os.path.join(OUT_DIR, "fibank_model_meta.json")

# ── Constants ─────────────────────────────────────────────────────────────────

N_USERS = 500
N_DEVICES = 800
N_SESSIONS = 3000
N_LOGIN_EVENTS = 4000
N_TRANSACTIONS = 10_000
FRAUD_RATE = 0.06
FRAUD_THRESHOLD = 0.35  # probability cut-off for fraud_flag

COUNTRIES = ["AL", "DE", "IT", "FR", "GB", "US", "TR", "MK", "GR", "RS"]
CITIES = {
    "AL": ["Tirana", "Durrës", "Vlorë", "Shkodër", "Elbasan"],
    "DE": ["Berlin", "Munich", "Hamburg", "Frankfurt", "Cologne"],
    "IT": ["Rome", "Milan", "Naples", "Turin", "Florence"],
    "FR": ["Paris", "Lyon", "Marseille", "Nice", "Bordeaux"],
    "GB": ["London", "Manchester", "Birmingham", "Leeds", "Glasgow"],
    "US": ["New York", "Los Angeles", "Chicago", "Houston", "Miami"],
    "TR": ["Istanbul", "Ankara", "Izmir", "Bursa", "Antalya"],
    "MK": ["Skopje", "Bitola", "Kumanovo"],
    "GR": ["Athens", "Thessaloniki", "Patras"],
    "RS": ["Belgrade", "Novi Sad", "Niš"],
}
BROWSERS = ["Chrome", "Firefox", "Safari", "Edge", "Opera", "Unknown"]
OS_TYPES = ["Windows", "macOS", "iOS", "Android", "Linux", "Unknown"]
CURRENCIES = ["ALL", "EUR", "USD", "GBP", "CHF"]
TX_STATUSES = ["ALLOWED", "REQUIRE_2FA", "HELD", "BLOCKED"]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FEATURE CATALOGUE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# Every feature fed to the XGBoost model is documented below.
# When calling predict_single(), supply a dict with these keys.
# Missing keys default to 0 (safe fallback, but provide as many as possible).
#
# SOURCE KEY
#   TX  = comes from Transaction row directly
#   USR = comes from User profile
#   DEV = aggregated from Device table for that user
#   SES = aggregated from Session table for that user
#   LOG = aggregated from LoginEvent table for that user
#   SEC = aggregated from SecurityLog table for that user
#   TSH = aggregated from TrustScoreHistory for that user
#   ENG = engineered / derived at feature-engineering time

FEATURE_DOCS = {
    # ── Amount features ───────────────────────────────────────────────────────
    "amount": {
        "source": "TX",
        "type": "float",
        "desc": "Raw transaction amount in the transaction's currency.",
        "fraud_signal": "Unusually high amounts vs the user's historical average are a strong signal.",
    },
    "amount_log": {
        "source": "ENG",
        "type": "float",
        "desc": "log1p(amount). Compresses the heavy-tailed distribution for the model.",
        "fraud_signal": "Works alongside 'amount' to capture both small probe txs and large spikes.",
    },
    "amount_ratio": {
        "source": "ENG",
        "type": "float",
        "desc": "amount / user's average_transaction_amount. Values >> 1 mean the tx is far above normal.",
        "fraud_signal": "> 5× the user's average is flagged as is_large_spike.",
    },
    "amount_vs_balance": {
        "source": "ENG",
        "type": "float",
        "desc": "amount / user's account balance. High ratio means the tx nearly drains the account.",
        "fraud_signal": "Account-draining transfers are a classic takeover pattern.",
    },
    "is_tiny_probe": {
        "source": "ENG",
        "type": "int (0/1)",
        "desc": "1 if amount < 2.0 (ANY currency). Fraudsters send micro-txs to verify account is live.",
        "fraud_signal": "A tiny probe followed by a large tx on the same account is a red flag.",
    },
    "is_large_spike": {
        "source": "ENG",
        "type": "int (0/1)",
        "desc": "1 if amount_ratio > 5. The current transaction is 5× the user's normal spend.",
        "fraud_signal": "High-value outlier relative to the user's own history.",
    },

    # ── Time features ─────────────────────────────────────────────────────────
    "tx_hour": {
        "source": "ENG",
        "type": "int (0–23)",
        "desc": "Hour of day (local server time) when the transaction was created.",
        "fraud_signal": "Fraud clusters in night hours (23:00–05:00); captured by is_night.",
    },
    "tx_dow": {
        "source": "ENG",
        "type": "int (0=Mon … 6=Sun)",
        "desc": "Day of week of the transaction.",
        "fraud_signal": "Weekend transactions have slightly higher fraud rates in this dataset.",
    },
    "is_night": {
        "source": "ENG",
        "type": "int (0/1)",
        "desc": "1 if tx_hour is between 23:00 and 05:59 inclusive.",
        "fraud_signal": "Most users don't transfer money at 3 AM.",
    },
    "is_weekend": {
        "source": "ENG",
        "type": "int (0/1)",
        "desc": "1 if the transaction falls on Saturday or Sunday.",
        "fraud_signal": "Support staff are reduced on weekends, fraudsters exploit this.",
    },
    "user_age_days": {
        "source": "ENG",
        "type": "int",
        "desc": "Days between the user account creation date and the transaction date.",
        "fraud_signal": "New accounts (< 30 days) committing large transfers are high risk.",
    },

    # ── Recipient features ────────────────────────────────────────────────────
    "recipient_is_new": {
        "source": "TX",
        "type": "int (0/1)",
        "desc": "1 if this is the first time this user has sent money to this recipient.",
        "fraud_signal": "The #1 ranked feature. Fraudsters always transfer to new/unknown accounts.",
    },
    "beneficiary_tx_count": {
        "source": "ENG",
        "type": "int",
        "desc": (
            "How many prior transactions this user has sent to the same to_account "
            "(cumulative count up to this transaction, sorted by created_at). "
            "0 = brand new beneficiary."
        ),
        "fraud_signal": "The lower this is, the more novel the recipient.",
    },

    # ── User financial profile ────────────────────────────────────────────────
    "trust_score": {
        "source": "USR",
        "type": "float (0–100)",
        "desc": (
            "Platform-computed trust score for the user (stored in User.trust_score). "
            "Updated by TrustScoreHistory events. 100 = fully trusted."
        ),
        "fraud_signal": "Compromised accounts tend to have erratic or declining trust scores.",
    },
    "average_transaction_amount": {
        "source": "USR",
        "type": "float",
        "desc": "The user's long-run average transaction amount, stored on the User record.",
        "fraud_signal": "Used as the denominator in amount_ratio.",
    },
    "balance": {
        "source": "USR",
        "type": "float",
        "desc": "Current account balance at time of feature engineering.",
        "fraud_signal": "Used in amount_vs_balance.",
    },

    # ── Velocity ──────────────────────────────────────────────────────────────
    "user_tx_count_24h": {
        "source": "ENG",
        "type": "int",
        "desc": (
            "Approximate cumulative transaction count for this user "
            "(expanding window sorted by timestamp, not a strict 24h rolling window). "
            "Replace with a true rolling window when connected to a live DB."
        ),
        "fraud_signal": "Burst of transactions in a short window = account takeover pattern.",
    },

    # ── Login event aggregates ────────────────────────────────────────────────
    "login_failed_attempts_total": {
        "source": "LOG",
        "type": "int",
        "desc": "Sum of all LoginEvent.failed_attempts for this user across all login events.",
        "fraud_signal": "High failed attempt total suggests brute-force credential attack.",
    },
    "login_vpn_count": {
        "source": "LOG",
        "type": "int",
        "desc": "Number of LoginEvents where LoginEvent.is_vpn = True for this user.",
        "fraud_signal": "VPN usage can mask geographic origin of attacker.",
    },
    "login_proxy_count": {
        "source": "LOG",
        "type": "int",
        "desc": "Number of LoginEvents where LoginEvent.is_proxy = True for this user.",
        "fraud_signal": "Proxy usage is a stronger anonymisation signal than VPN.",
    },
    "login_risk_score_mean": {
        "source": "LOG",
        "type": "float (0–1)",
        "desc": "Mean of LoginEvent.risk_score across all login events for this user.",
        "fraud_signal": "Persistently high login risk scores precede fraudulent transactions.",
    },
    "login_success_rate": {
        "source": "LOG",
        "type": "float (0–1)",
        "desc": "Fraction of LoginEvents where LoginEvent.success = True.",
        "fraud_signal": "A low success rate means many failed logins — credential stuffing.",
    },
    "login_country_nunique": {
        "source": "LOG",
        "type": "int",
        "desc": "Number of distinct countries seen in LoginEvent.country for this user.",
        "fraud_signal": "Logging in from many countries is impossible-travel behaviour.",
    },

    # ── Device features ───────────────────────────────────────────────────────
    "device_count": {
        "source": "DEV",
        "type": "int",
        "desc": "Total number of Device records associated with this user.",
        "fraud_signal": "Sudden spike in device count = attacker registering new devices.",
    },
    "trusted_device_count": {
        "source": "DEV",
        "type": "int",
        "desc": "Number of devices where Device.is_trusted = True for this user.",
        "fraud_signal": "Low trusted count means most activity is from unrecognised devices.",
    },
    "os_nunique": {
        "source": "DEV",
        "type": "int",
        "desc": "Number of distinct Device.os values seen for this user.",
        "fraud_signal": "A single user logging in from Windows, Android, Linux, iOS simultaneously is suspicious.",
    },
    "browser_nunique": {
        "source": "DEV",
        "type": "int",
        "desc": "Number of distinct Device.browser values seen for this user.",
        "fraud_signal": "Similar to os_nunique — excessive browser diversity is unusual.",
    },
    "untrusted_device_ratio": {
        "source": "ENG",
        "type": "float (0–1)",
        "desc": "1 - (trusted_device_count / device_count). Fraction of untrusted devices.",
        "fraud_signal": "1.0 means ALL devices are untrusted — very high risk.",
    },

    # ── Location / session ────────────────────────────────────────────────────
    "session_country_mismatch": {
        "source": "ENG",
        "type": "int (0/1)",
        "desc": (
            "1 if the country of the user's most recent Session differs from "
            "User.home_country. Proxies 'is the user transacting from abroad?'"
        ),
        "fraud_signal": "Impossible travel or account takeover from a foreign country.",
    },

    # ── Security log aggregates ───────────────────────────────────────────────
    "seclog_count": {
        "source": "SEC",
        "type": "int",
        "desc": "Total SecurityLog events for this user.",
        "fraud_signal": "Many security events mean the account has already triggered alerts.",
    },
    "seclog_risk_mean": {
        "source": "SEC",
        "type": "float (0–1)",
        "desc": "Mean SecurityLog.risk_score across all security log entries for this user.",
        "fraud_signal": "Persistently elevated security risk precedes fraud.",
    },
    "seclog_critical_count": {
        "source": "SEC",
        "type": "int",
        "desc": "Number of SecurityLog entries with severity = 'CRITICAL' for this user.",
        "fraud_signal": "Critical alerts are rare and highly predictive of fraud.",
    },
    "seclog_high_count": {
        "source": "SEC",
        "type": "int",
        "desc": "Number of SecurityLog entries with severity = 'HIGH' for this user.",
        "fraud_signal": "Second tier alert severity; combined with CRITICAL gives full picture.",
    },

    # ── Trust dynamics ────────────────────────────────────────────────────────
    "trust_delta_mean": {
        "source": "TSH",
        "type": "float",
        "desc": (
            "Net change in trust score: last TrustScoreHistory.new_score minus "
            "first TrustScoreHistory.new_score for this user. Negative = declining trust."
        ),
        "fraud_signal": "A sharply declining trust score indicates recent bad behaviour.",
    },
    "trust_change_count": {
        "source": "TSH",
        "type": "int",
        "desc": "Number of TrustScoreHistory records for this user.",
        "fraud_signal": "Many changes = volatile trust history, often tied to fraud events.",
    },

    # ── Transaction status & currency ─────────────────────────────────────────
    "status_blocked": {
        "source": "TX",
        "type": "int (0/1)",
        "desc": "1 if Transaction.status = 'BLOCKED'.",
        "fraud_signal": "The rule engine already flagged this transaction.",
    },
    "status_held": {
        "source": "TX",
        "type": "int (0/1)",
        "desc": "1 if Transaction.status = 'HELD'.",
        "fraud_signal": "On hold for manual review — moderate risk signal.",
    },
    "status_2fa": {
        "source": "TX",
        "type": "int (0/1)",
        "desc": "1 if Transaction.status = 'REQUIRE_2FA'.",
        "fraud_signal": "System requested a second factor — moderate risk signal.",
    },
    "currency_foreign": {
        "source": "TX",
        "type": "int (0/1)",
        "desc": "1 if Transaction.currency != 'ALL' (Albanian Lek). Foreign currency transaction.",
        "fraud_signal": "Cross-currency transfers are used to obscure money movement.",
    },

    # ── Encoded categoricals ──────────────────────────────────────────────────
    "home_country_enc": {
        "source": "ENG",
        "type": "int",
        "desc": "Label-encoded User.home_country (sklearn LabelEncoder, fit on training data).",
        "fraud_signal": "Indirect; model learns country-level fraud rates.",
    },
    "session_country_enc": {
        "source": "ENG",
        "type": "int",
        "desc": "Label-encoded country of the user's most recent Session.",
        "fraud_signal": "Certain session origin countries have higher fraud rates.",
    },
    "role_enc": {
        "source": "ENG",
        "type": "int",
        "desc": "Label-encoded User.role (CUSTOMER=0, ANALYST=1, ADMIN=2 — order may vary).",
        "fraud_signal": "Admin/analyst roles transacting large amounts is anomalous.",
    },
}

FEATURE_COLS = list(FEATURE_DOCS.keys())


# ── Helper utilities ──────────────────────────────────────────────────────────

def rand_datetime(start_days_ago=365, end_days_ago=0):
    delta = rng.integers(end_days_ago * 86400, start_days_ago * 86400)
    return datetime.now() - timedelta(seconds=int(delta))


def rand_country():
    return rng.choice(COUNTRIES, p=[0.55, 0.07, 0.06, 0.06, 0.05, 0.05, 0.04, 0.04, 0.04, 0.04])


def rand_city(country):
    return rng.choice(CITIES[country])


def account_number():
    return "AL" + "".join([str(rng.integers(0, 10)) for _ in range(16)])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DATA GENERATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generate_users(n=N_USERS):
    rows = []
    for i in range(n):
        country = rand_country()
        avg_tx = round(float(rng.lognormal(5.5, 1.2)), 2)
        trust = round(float(rng.beta(5, 2) * 100), 1)
        created = rand_datetime(730, 30)
        rows.append({
            "id": i + 1,
            "name": fake.name(),
            "email": fake.email(),
            "password_hash": fake.sha256(),
            "role": rng.choice(["CUSTOMER", "ANALYST", "ADMIN"], p=[0.95, 0.04, 0.01]),
            "home_country": country,
            "home_city": rand_city(country),
            "trust_score": trust,
            "average_transaction_amount": avg_tx,
            "account_number": account_number(),
            "balance": round(float(rng.lognormal(7, 1.5)), 2),
            "created_at": created,
            "updated_at": created + timedelta(days=int(rng.integers(0, 200))),
        })
    return pd.DataFrame(rows)


def generate_devices(users, n=N_DEVICES):
    rows = []
    user_ids = users["id"].tolist()
    for i in range(n):
        uid = int(rng.choice(user_ids))
        first_seen = rand_datetime(365, 30)
        rows.append({
            "id": i + 1,
            "user_id": uid,
            "device_hash": fake.sha1(),
            "device_label": rng.choice(["Personal Laptop", "Work PC", "iPhone", "Android Phone", "Tablet", "Unknown"]),
            "browser": rng.choice(BROWSERS),
            "os": rng.choice(OS_TYPES),
            "is_trusted": bool(rng.choice([True, False], p=[0.75, 0.25])),
            "first_seen_at": first_seen,
            "last_seen_at": first_seen + timedelta(days=int(rng.integers(0, 200))),
            "created_at": first_seen,
        })
    return pd.DataFrame(rows)


def generate_sessions(users, devices, n=N_SESSIONS):
    rows = []
    for i in range(n):
        uid = int(rng.choice(users["id"]))
        country = rand_country()
        created = rand_datetime(180, 0)
        rows.append({
            "id": i + 1,
            "user_id": uid,
            "session_token_hash": fake.sha256(),
            "device_hash": fake.sha1(),
            "ip_address": fake.ipv4_public(),
            "country": country,
            "city": rand_city(country),
            "is_active": bool(rng.choice([True, False], p=[0.2, 0.8])),
            "created_at": created,
            "last_seen_at": created + timedelta(minutes=int(rng.integers(1, 300))),
        })
    return pd.DataFrame(rows)


def generate_login_events(users, n=N_LOGIN_EVENTS):
    rows = []
    for i in range(n):
        uid = int(rng.choice(users["id"]))
        is_fraud_attempt = rng.random() < 0.08
        country = rand_country()
        rows.append({
            "id": i + 1,
            "user_id": uid,
            "device_hash": fake.sha1(),
            "ip_address": fake.ipv4_public(),
            "country": country,
            "city": rand_city(country),
            "is_vpn": bool(rng.random() < (0.4 if is_fraud_attempt else 0.05)),
            "is_proxy": bool(rng.random() < (0.3 if is_fraud_attempt else 0.02)),
            "success": bool(rng.random() > (0.5 if is_fraud_attempt else 0.02)),
            "failed_attempts": int(rng.integers(0, 10 if is_fraud_attempt else 2)),
            "risk_score": round(float(rng.uniform(0.6, 1.0) if is_fraud_attempt else rng.uniform(0, 0.3)), 3),
            "created_at": rand_datetime(180, 0),
        })
    return pd.DataFrame(rows)


def generate_transactions(users, devices, n=N_TRANSACTIONS):
    rows = []
    user_accounts = dict(zip(users["id"], users["account_number"]))
    user_avg_tx = dict(zip(users["id"], users["average_transaction_amount"]))
    all_accounts = list(user_accounts.values())

    for i in range(n):
        uid = int(rng.choice(users["id"]))
        is_fraud = rng.random() < FRAUD_RATE
        from_acct = user_accounts[uid]
        to_acct = rng.choice(all_accounts)
        while to_acct == from_acct:
            to_acct = rng.choice(all_accounts)

        avg = user_avg_tx[uid]
        if is_fraud:
            amount = round(float(rng.choice([
                rng.uniform(avg * 3, avg * 20),
                rng.uniform(0.5, 2.0),
            ])), 2)
        else:
            amount = round(float(abs(rng.normal(avg, avg * 0.4))), 2)
            amount = max(0.01, amount)

        created = rand_datetime(365, 0)
        rows.append({
            "id": i + 1,
            "user_id": uid,
            "from_account": from_acct,
            "to_account": to_acct,
            "amount": amount,
            "currency": rng.choice(CURRENCIES, p=[0.6, 0.25, 0.08, 0.04, 0.03]),
            "recipient_name": fake.name(),
            "recipient_is_new": bool(rng.random() < (0.85 if is_fraud else 0.15)),
            "status": rng.choice(TX_STATUSES,
                                 p=[0.1, 0.3, 0.2, 0.4] if is_fraud else [0.85, 0.08, 0.04, 0.03]),
            "risk_score": round(float(rng.uniform(0.6, 1.0) if is_fraud else rng.uniform(0, 0.35)), 3),
            "created_at": created,
            "_is_fraud": int(is_fraud),
        })
    return pd.DataFrame(rows)


def generate_security_logs(users, n=2000):
    event_types = ["FAILED_LOGIN", "RATE_LIMIT", "BLOCKED_IP", "VPN_DETECTED",
                   "NEW_DEVICE", "UNUSUAL_AMOUNT", "MULTIPLE_SESSIONS"]
    rows = []
    for i in range(n):
        rows.append({
            "id": i + 1,
            "user_id": int(rng.choice(users["id"])),
            "event_type": rng.choice(event_types),
            "endpoint": rng.choice(["/login", "/transfer", "/api/transactions", "/2fa"]),
            "ip_address": fake.ipv4_public(),
            "risk_score": round(float(rng.uniform(0, 1)), 3),
            "severity": rng.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"], p=[0.5, 0.3, 0.15, 0.05]),
            "created_at": rand_datetime(180, 0),
        })
    return pd.DataFrame(rows)


def generate_trust_score_history(users, n=1500):
    rows = []
    for i in range(n):
        old = round(float(rng.uniform(30, 95)), 1)
        rows.append({
            "id": i + 1,
            "user_id": int(rng.choice(users["id"])),
            "old_score": old,
            "new_score": round(float(np.clip(old + rng.normal(0, 10), 0, 100)), 1),
            "reason": rng.choice(["FAILED_LOGIN", "FRAUD_ALERT", "MANUAL_REVIEW",
                                  "GOOD_BEHAVIOUR", "DEVICE_ADDED"]),
            "created_at": rand_datetime(365, 0),
        })
    return pd.DataFrame(rows)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FEATURE ENGINEERING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def engineer_features(transactions, users, devices, sessions,
                      login_events, security_logs, trust_history):
    df = transactions.copy()

    # User base features
    u = users[["id", "home_country", "home_city", "trust_score",
               "average_transaction_amount", "balance", "created_at", "role"]].copy()
    u = u.rename(columns={"id": "user_id", "created_at": "user_created_at"})
    df = df.merge(u, on="user_id", how="left")

    # Amount features
    df["amount_ratio"] = df["amount"] / (df["average_transaction_amount"] + 1e-6)
    df["amount_log"] = np.log1p(df["amount"])
    df["amount_vs_balance"] = df["amount"] / (df["balance"] + 1e-6)
    df["is_tiny_probe"] = (df["amount"] < 2.0).astype(int)
    df["is_large_spike"] = (df["amount_ratio"] > 5).astype(int)

    # Time features
    df["tx_hour"] = pd.to_datetime(df["created_at"]).dt.hour
    df["tx_dow"] = pd.to_datetime(df["created_at"]).dt.dayofweek
    df["is_night"] = ((df["tx_hour"] >= 23) | (df["tx_hour"] <= 5)).astype(int)
    df["is_weekend"] = (df["tx_dow"] >= 5).astype(int)
    df["user_age_days"] = (
            pd.to_datetime(df["created_at"]) - pd.to_datetime(df["user_created_at"])
    ).dt.days.clip(lower=0)

    # Beneficiary history
    beneficiary_counts = (
        df.sort_values("created_at")
        .groupby(["user_id", "to_account"])
        .cumcount()
    )
    df["beneficiary_tx_count"] = beneficiary_counts.values

    # Velocity (cumulative expanding — replace with real rolling window in production)
    df["created_at_ts"] = pd.to_datetime(df["created_at"]).astype(np.int64) // 10 ** 9
    df["user_tx_count_24h"] = (
        df.groupby("user_id")["created_at_ts"]
        .transform(lambda s: s.expanding().count())
        .astype(int)
    )

    # Login event aggregates
    le_agg = login_events.groupby("user_id").agg(
        login_failed_attempts_total=("failed_attempts", "sum"),
        login_vpn_count=("is_vpn", "sum"),
        login_proxy_count=("is_proxy", "sum"),
        login_risk_score_mean=("risk_score", "mean"),
        login_success_rate=("success", "mean"),
        login_country_nunique=("country", "nunique"),
    ).reset_index()
    df = df.merge(le_agg, on="user_id", how="left")

    # Device aggregates
    dev_agg = devices.groupby("user_id").agg(
        device_count=("id", "count"),
        trusted_device_count=("is_trusted", "sum"),
        os_nunique=("os", "nunique"),
        browser_nunique=("browser", "nunique"),
    ).reset_index()
    df = df.merge(dev_agg, on="user_id", how="left")
    df["untrusted_device_ratio"] = 1 - df["trusted_device_count"] / (df["device_count"] + 1e-6)

    # Session location
    sess_latest = (
        sessions.sort_values("created_at")
        .groupby("user_id").last()[["country", "city"]]
        .reset_index()
        .rename(columns={"country": "session_country", "city": "session_city"})
    )
    df = df.merge(sess_latest, on="user_id", how="left")
    df["session_country_mismatch"] = (df["session_country"] != df["home_country"]).astype(int)

    # Security log aggregates
    sl_agg = security_logs.groupby("user_id").agg(
        seclog_count=("id", "count"),
        seclog_risk_mean=("risk_score", "mean"),
        seclog_critical_count=("severity", lambda s: (s == "CRITICAL").sum()),
        seclog_high_count=("severity", lambda s: (s == "HIGH").sum()),
    ).reset_index()
    df = df.merge(sl_agg, on="user_id", how="left")

    # Trust score dynamics
    th_agg = trust_history.groupby("user_id").agg(
        trust_delta_mean=pd.NamedAgg("new_score",
                                     lambda s: s.iloc[-1] - s.iloc[0] if len(s) > 1 else 0),
        trust_change_count=("id", "count"),
    ).reset_index()
    df = df.merge(th_agg, on="user_id", how="left")

    # Encoding
    df["recipient_is_new"] = df["recipient_is_new"].astype(int)
    df["status_blocked"] = (df["status"] == "BLOCKED").astype(int)
    df["status_held"] = (df["status"] == "HELD").astype(int)
    df["status_2fa"] = (df["status"] == "REQUIRE_2FA").astype(int)
    df["currency_foreign"] = (df["currency"] != "ALL").astype(int)

    for col in ["home_country", "session_country", "role"]:
        le = LabelEncoder()
        df[col + "_enc"] = le.fit_transform(df[col].fillna("UNKNOWN"))

    return df


def build_feature_matrix(df):
    X = df[FEATURE_COLS].fillna(0)
    y = df["_is_fraud"]
    return X, y


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MODEL TRAINING & PERSISTENCE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def train_model(X, y):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()

    model = xgb.XGBClassifier(
        n_estimators=400,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        eval_metric="aucpr",
        use_label_encoder=False,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    proba = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, proba)
    ap = average_precision_score(y_test, proba)

    print(f"\n{'═' * 55}")
    print(f"  XGBoost Fraud Model — Evaluation")
    print(f"{'═' * 55}")
    print(f"  ROC-AUC : {auc:.4f}")
    print(f"  Avg Prec: {ap:.4f}  (area under PR curve)")
    preds = (proba >= FRAUD_THRESHOLD).astype(int)
    print(f"\n  Classification report (threshold={FRAUD_THRESHOLD}):")
    print(classification_report(y_test, preds,
                                target_names=["Legitimate", "Fraud"], digits=3))
    return model


def save_model(model):
    """Persist the trained model and feature metadata to disk."""
    os.makedirs(OUT_DIR, exist_ok=True)
    model.save_model(MODEL_PATH)
    print(f"  ✅  Model saved → {MODEL_PATH}")

    # Save feature metadata as JSON for integrators
    meta = {
        "model_path": MODEL_PATH,
        "feature_cols": FEATURE_COLS,
        "fraud_threshold": FRAUD_THRESHOLD,
        "trained_at": datetime.now().isoformat(),
        "features": FEATURE_DOCS,
    }
    with open(META_PATH, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"  ✅  Feature metadata saved → {META_PATH}")


def load_model():
    """Load a previously saved model from disk."""
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"No saved model found at '{MODEL_PATH}'. "
            "Run with --retrain to train from scratch."
        )
    model = xgb.XGBClassifier()
    model.load_model(MODEL_PATH)
    print(f"  ✅  Loaded existing model from {MODEL_PATH}")
    return model


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SINGLE-TRANSACTION INFERENCE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def predict_single(model, transaction: dict) -> dict:
    """
    Score ONE transaction for fraud probability.

    Parameters
    ----------
    model       : loaded or freshly trained XGBClassifier
    transaction : dict with any subset of FEATURE_COLS as keys.
                  Missing keys default to 0. For best accuracy, populate
                  as many features as possible using the FEATURE_DOCS catalogue.

    Returns
    -------
    dict with:
        fraud_probability  float  — 0.0 (clean) to 1.0 (certain fraud)
        fraud_flag         int    — 1 if probability >= FRAUD_THRESHOLD else 0
        fraud_risk_band    str    — "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
        feature_vector     dict   — the exact values fed to the model
        missing_features   list   — features that were defaulted to 0
    """
    # Build a row with zeros for every missing feature
    row = {col: 0 for col in FEATURE_COLS}
    missing = []
    for col in FEATURE_COLS:
        if col in transaction:
            row[col] = transaction[col]
        else:
            missing.append(col)

    X = pd.DataFrame([row])[FEATURE_COLS]
    prob = float(model.predict_proba(X)[0, 1])

    if prob < 0.15:
        band = "LOW"
    elif prob < 0.35:
        band = "MEDIUM"
    elif prob < 0.65:
        band = "HIGH"
    else:
        band = "CRITICAL"

    return {
        "fraud_probability": round(prob, 4),
        "fraud_flag": int(prob >= FRAUD_THRESHOLD),
        "fraud_risk_band": band,
        "feature_vector": row,
        "missing_features": missing,
    }


def print_prediction(result: dict):
    """Pretty-print a single prediction result to the console."""
    print(f"\n{'─' * 50}")
    print(f"  FRAUD PREDICTION RESULT")
    print(f"{'─' * 50}")
    print(f"  Probability : {result['fraud_probability']:.4f}")
    print(f"  Flag        : {'🚨 FRAUD' if result['fraud_flag'] else '✅ LEGITIMATE'}")
    print(f"  Risk band   : {result['fraud_risk_band']}")
    if result["missing_features"]:
        print(f"\n  ⚠  {len(result['missing_features'])} features defaulted to 0:")
        for f in result["missing_features"]:
            print(f"       • {f}  ({FEATURE_DOCS[f]['desc'][:60]}…)")
    print(f"{'─' * 50}\n")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# IMPORTABLE API  —  use this from another file in your application
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# QUICKSTART (in any other .py file):
#
#   from fibank_fraud_model import FraudDetector
#
#   detector = FraudDetector()          # loads saved model automatically
#
#   result = detector.score({
#       "amount"          : 5000,
#       "recipient_is_new": 1,
#       "login_vpn_count" : 2,
#       "trust_score"     : 30,
#   })
#
#   print(result["fraud_probability"])  # e.g. 0.9231
#   print(result["fraud_flag"])         # 1 = fraud, 0 = legitimate
#   print(result["fraud_risk_band"])    # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
#
# The detector accepts any partial dict — missing features default to 0.
# See FEATURE_DOCS for the full list of supported keys and their meaning.

class FraudDetector:
    """
    Thin wrapper around the saved XGBoost model for use in other modules.

    Parameters
    ----------
    model_path : str, optional
        Path to the .ubj model file. Defaults to the outputs/ folder that sits
        next to this script. Pass an explicit path if the model lives elsewhere:

            detector = FraudDetector(r"C:/myapp/models/fibank_fraud_model.ubj")

    Usage example (not a runnable doctest — requires a trained model on disk)
    --------------------------------------------------------------------------
        from fibank_fraud_model import FraudDetector

        detector = FraudDetector()   # or FraudDetector("path/to/model.ubj")

        result = detector.score({
            "amount"          : 15000,
            "recipient_is_new": 1,
            "login_vpn_count" : 2,
        })
        # result["fraud_probability"]  ->  float  e.g. 0.9231
        # result["fraud_flag"]         ->  1 = fraud, 0 = legitimate
        # result["fraud_risk_band"]    ->  "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    """

    def __init__(self, model_path: str = MODEL_PATH):
        if not os.path.isfile(model_path):
            raise FileNotFoundError(
                f"\n\n  Model file not found: {model_path}"
                f"\n  Run the training script first:"
                f"\n      python fibank_fraud_model.py --retrain"
                f"\n  Then move or copy 'outputs/fibank_fraud_model.ubj' to the expected location,"
                f"\n  or pass the path explicitly: FraudDetector(\'path/to/fibank_fraud_model.ubj\')"
            )
        self._model = xgb.XGBClassifier()
        self._model.load_model(model_path)

    def score(self, transaction: dict) -> dict:
        """
        Score a single transaction.

        Parameters
        ----------
        transaction : dict
            Keys should match FEATURE_COLS (see FEATURE_DOCS for descriptions).
            Any missing key defaults to 0 — supply as many as you have.

        Returns
        -------
        dict with keys:
            fraud_probability  float        0.0-1.0
            fraud_flag         int          1 = fraud, 0 = legitimate
            fraud_risk_band    str          "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
            feature_vector     dict         exact values fed to the model
            missing_features   list[str]    features that defaulted to 0
        """
        return predict_single(self._model, transaction)

    def score_batch(self, transactions: list) -> list:
        """
        Score a list of transactions. Returns a list of result dicts
        in the same order as the input.
        """
        return [self.score(tx) for tx in transactions]

    @staticmethod
    def feature_docs() -> dict:
        """Return the full FEATURE_DOCS catalogue (source, type, desc, fraud_signal)."""
        return FEATURE_DOCS

    @staticmethod
    def feature_names() -> list:
        """Return the ordered list of feature column names."""
        return FEATURE_COLS


# ── Feature catalogue printer ─────────────────────────────────────────────────

def print_feature_catalogue():
    print(f"\n{'━' * 72}")
    print(f"  FEATURE CATALOGUE  ({len(FEATURE_COLS)} features)")
    print(f"{'━' * 72}")
    for col in FEATURE_COLS:
        doc = FEATURE_DOCS[col]
        print(f"\n  {col}")
        print(f"    source : {doc['source']}")
        print(f"    type   : {doc['type']}")
        print(f"    desc   : {doc['desc']}")
        print(f"    signal : {doc['fraud_signal']}")
    print(f"\n{'━' * 72}\n")


# ── Output dataframe builder ──────────────────────────────────────────────────

def build_output_df(transactions, X, model):
    proba_all = model.predict_proba(X)[:, 1]
    out = transactions[["id", "user_id", "from_account", "to_account",
                        "amount", "currency", "recipient_name",
                        "recipient_is_new", "status", "risk_score",
                        "created_at", "_is_fraud"]].copy()
    out = out.rename(columns={"_is_fraud": "actual_fraud_label"})
    out["fraud_probability"] = np.round(proba_all, 4)
    out["fraud_flag"] = (out["fraud_probability"] >= FRAUD_THRESHOLD).astype(int)
    out["fraud_risk_band"] = pd.cut(
        out["fraud_probability"],
        bins=[0, 0.15, 0.35, 0.65, 1.001],
        labels=["LOW", "MEDIUM", "HIGH", "CRITICAL"],
        right=True,
    )
    return out.sort_values("fraud_probability", ascending=False).reset_index(drop=True)


def feature_importance_df(model):
    imp = pd.DataFrame({
        "feature": FEATURE_COLS,
        "importance": model.feature_importances_,
    }).sort_values("importance", ascending=False).reset_index(drop=True)
    print("\n  Top 15 most important features:")
    print(imp.head(15).to_string(index=False))
    return imp


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main():
    parser = argparse.ArgumentParser(description="fibank XGBoost Fraud Detector")
    parser.add_argument("--retrain", action="store_true",
                        help="Force retrain even if a saved model exists.")
    parser.add_argument("--predict", type=str, default=None,
                        help=(
                            "Score a single transaction. Accepts either:\n"
                            "  (a) a path to a JSON file:  --predict tx.json\n"
                            "  (b) a raw JSON string (Linux/macOS only — "
                            "on Windows use --predict-file instead)."
                        ))
    parser.add_argument("--predict-file", type=str, default=None,
                        help=(
                            "Path to a JSON file containing one transaction dict. "
                            "Recommended on Windows (avoids PowerShell quoting issues). "
                            "Example: --predict-file transaction.json"
                        ))
    parser.add_argument("--catalogue", action="store_true",
                        help="Print the full feature catalogue and exit.")
    args = parser.parse_args()

    if args.catalogue:
        print_feature_catalogue()
        return

    # ── Single transaction prediction mode ────────────────────────────────────
    predict_input = args.predict_file or args.predict
    if predict_input:
        model = load_model()

        # Resolve input: file path takes priority, then try JSON string
        tx = None
        if os.path.isfile(predict_input):
            # Input is a file path
            with open(predict_input, "r", encoding="utf-8") as fh:
                tx = json.load(fh)
            print(f"  📄  Loaded transaction from file: {predict_input}")
        else:
            # Try to parse as a raw JSON string
            try:
                tx = json.loads(predict_input)
            except json.JSONDecodeError:
                print(
                    "\n  ❌  ERROR: Could not parse the --predict value as JSON or find it as a file.\n"
                    "\n"
                    "  On Windows / PowerShell, pass a JSON file instead:\n"
                    "      1. Save your transaction to a file, e.g. tx.json\n"
                    "      2. Run:  python fibank_fraud_model.py --predict-file tx.json\n"
                    "\n"
                    "  Example tx.json:\n"
                    '  {\n'
                    '    "amount": 5000,\n'
                    '    "recipient_is_new": 1,\n'
                    '    "login_vpn_count": 2\n'
                    '  }\n'
                )
                raise SystemExit(1)

        result = predict_single(model, tx)
        print_prediction(result)
        return

    # ── Training / evaluation mode ────────────────────────────────────────────
    should_train = args.retrain or not os.path.exists(MODEL_PATH)

    if should_train:
        print("Generating synthetic banking data …")
        users = generate_users()
        devices = generate_devices(users)
        sessions = generate_sessions(users, devices)
        login_events = generate_login_events(users)
        transactions = generate_transactions(users, devices)
        security_logs = generate_security_logs(users)
        trust_history = generate_trust_score_history(users)

        print(f"  Users={len(users)}, Devices={len(devices)}, "
              f"Sessions={len(sessions)}, LoginEvents={len(login_events)}, "
              f"Transactions={len(transactions)}")
        print(f"  Fraud rate: {transactions['_is_fraud'].mean():.2%}")

        print("\nEngineering features …")
        df_feat = engineer_features(
            transactions, users, devices, sessions,
            login_events, security_logs, trust_history
        )
        X, y = build_feature_matrix(df_feat)

        print("Training XGBoost model …")
        model = train_model(X, y)
        save_model(model)

        imp = feature_importance_df(model)

        print("\nBuilding output dataframe …")
        output_df = build_output_df(transactions, X, model)

        os.makedirs(OUT_DIR, exist_ok=True)
        output_df.to_csv(os.path.join(OUT_DIR, "transactions_with_fraud_scores.csv"), index=False)
        users.to_csv(os.path.join(OUT_DIR, "synthetic_users.csv"), index=False)
        transactions.to_csv(os.path.join(OUT_DIR, "synthetic_transactions.csv"), index=False)
        imp.to_csv(os.path.join(OUT_DIR, "feature_importance.csv"), index=False)

        print(f"\n{'═' * 55}")
        print("  Sample — highest-risk transactions:")
        print(output_df[["id", "user_id", "amount", "currency", "recipient_is_new",
                         "status", "fraud_probability", "fraud_risk_band",
                         "actual_fraud_label"]].head(10).to_string(index=False))

        print("\n  ✅  Output files saved to outputs/")
        print("      transactions_with_fraud_scores.csv")
        print("      synthetic_users.csv")
        print("      synthetic_transactions.csv")
        print("      feature_importance.csv")
        print("      fibank_fraud_model.ubj   ← XGBoost binary model")
        print("      fibank_model_meta.json   ← Feature docs for integrators")

    else:
        print(f"  ℹ  Saved model found at '{MODEL_PATH}'. Skipping retrain.")
        print(f"     Pass --retrain to force a fresh training run.")
        model = load_model()

    # ── Demo: score a single suspicious transaction ───────────────────────────
    print("\n── Demo: scoring a single suspicious transaction ─────────────")
    suspicious_tx = {
        "amount": 15000.0,
        "amount_log": np.log1p(15000.0),
        "amount_ratio": 12.0,  # 12× the user's average
        "amount_vs_balance": 0.95,  # nearly drains the account
        "is_tiny_probe": 0,
        "is_large_spike": 1,
        "tx_hour": 3,  # 3 AM
        "tx_dow": 6,  # Sunday
        "is_night": 1,
        "is_weekend": 1,
        "user_age_days": 12,  # very new account
        "recipient_is_new": 1,  # never sent to this person before
        "beneficiary_tx_count": 0,
        "trust_score": 28.0,  # low trust
        "average_transaction_amount": 1200.0,
        "balance": 15800.0,
        "user_tx_count_24h": 8,  # burst of activity
        "login_failed_attempts_total": 14,
        "login_vpn_count": 3,
        "login_proxy_count": 2,
        "login_risk_score_mean": 0.82,
        "login_success_rate": 0.4,
        "login_country_nunique": 5,
        "device_count": 4,
        "trusted_device_count": 0,
        "os_nunique": 4,
        "browser_nunique": 3,
        "untrusted_device_ratio": 1.0,
        "session_country_mismatch": 1,
        "seclog_count": 9,
        "seclog_risk_mean": 0.88,
        "seclog_critical_count": 3,
        "seclog_high_count": 4,
        "trust_delta_mean": -22.0,  # trust dropped sharply
        "trust_change_count": 6,
        "status_blocked": 1,
        "status_held": 0,
        "status_2fa": 0,
        "currency_foreign": 1,
        "home_country_enc": 0,
        "session_country_enc": 3,
        "role_enc": 0,
    }
    result = predict_single(model, suspicious_tx)
    print_prediction(result)

    print("\n── Demo: scoring a clean low-risk transaction ────────────────")
    clean_tx = {
        "amount": 120.0,
        "amount_log": np.log1p(120.0),
        "amount_ratio": 0.9,
        "amount_vs_balance": 0.01,
        "is_tiny_probe": 0,
        "is_large_spike": 0,
        "tx_hour": 11,
        "tx_dow": 1,
        "is_night": 0,
        "is_weekend": 0,
        "user_age_days": 740,
        "recipient_is_new": 0,  # known recipient
        "beneficiary_tx_count": 14,
        "trust_score": 88.5,
        "average_transaction_amount": 135.0,
        "balance": 9200.0,
        "user_tx_count_24h": 2,
        "login_failed_attempts_total": 1,
        "login_vpn_count": 0,
        "login_proxy_count": 0,
        "login_risk_score_mean": 0.08,
        "login_success_rate": 0.99,
        "login_country_nunique": 1,
        "device_count": 2,
        "trusted_device_count": 2,
        "os_nunique": 1,
        "browser_nunique": 1,
        "untrusted_device_ratio": 0.0,
        "session_country_mismatch": 0,
        "seclog_count": 1,
        "seclog_risk_mean": 0.05,
        "seclog_critical_count": 0,
        "seclog_high_count": 0,
        "trust_delta_mean": 5.0,
        "trust_change_count": 2,
        "status_blocked": 0,
        "status_held": 0,
        "status_2fa": 0,
        "currency_foreign": 0,
        "home_country_enc": 0,
        "session_country_enc": 0,
        "role_enc": 0,
    }
    result2 = predict_single(model, clean_tx)
    print_prediction(result2)


if __name__ == "__main__":
    main()
