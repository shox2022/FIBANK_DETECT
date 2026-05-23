# AEGIS Fraud Intelligence

AEGIS means Adaptive Engine for Guarded Intelligence & Security.

This repository is being built in controlled phases. Phase 1 contains only the backend foundation: FastAPI app setup, stable SQLite configuration, SQLAlchemy models, automatic table creation, an idempotent seed command, and a health endpoint.

## Phase 1 Backend Setup

```powershell
cd aegis-fraud-intelligence\backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env
python -m app.seed
uvicorn app.main:app --reload --port 8000
```

On Linux or macOS, activate the virtual environment with:

```bash
source venv/bin/activate
```

## Phase 1 Verification

The SQLite database is created at:

```text
backend/aegis.sqlite
```

The database path is resolved from the backend directory, so it does not depend on the terminal working directory.

Verify the backend:

- Health endpoint: http://localhost:8000/api/health
- Swagger docs: http://localhost:8000/docs

The seed command is safe to run multiple times:

```powershell
python -m app.seed
```

It upserts demo users and risk rules instead of duplicating them.

## Phase 1 Demo Users

All seeded demo users use the password:

```text
password123
```

| Email | Role |
| --- | --- |
| customer@aegis.test | CUSTOMER |
| analyst@aegis.test | ANALYST |
| admin@aegis.test | ADMIN |

## Phase 5 Frontend Setup

The React frontend expects the FastAPI backend at:

```text
http://localhost:8000
```

To override this, create `frontend/.env` from `frontend/.env.example` and set:

```text
VITE_API_BASE_URL=http://localhost:8000
```

Run the frontend:

```powershell
cd aegis-fraud-intelligence\frontend
npm install
npm run dev
```

Open:

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs

Build check:

```powershell
npm run build
```
## ML Integration

AEGIS can integrate the fibank XGBoost fraud detector through `backend/app/services/ml_score_engine.py`.
The runtime detector files live in:

```text
backend/app/ml/fraud_detector.py
backend/app/ml/fibank_fraud_model.py
backend/app/ml/outputs/fibank_fraud_model.ubj
```

Place the trained model artifact at:

```text
backend/app/ml/outputs/fibank_fraud_model.ubj
```

The backend supports fail-open behavior. If the model file or ML dependencies are unavailable and `FRAUD_ML_FAIL_OPEN=true`, banking flows continue with rule-based scoring and return controlled ML fallback metadata.

Environment settings:

```text
FRAUD_MODEL_PATH=app/ml/outputs/fibank_fraud_model.ubj
FRAUD_ML_ENABLED=true
FRAUD_ML_FAIL_OPEN=true
```

Required ML dependencies are listed in `backend/requirements.txt`:

```text
xgboost
pandas
numpy
scikit-learn
```

Integration flow:

1. Customer initiates a transaction.
2. The rule engine calculates deterministic fraud risk.
3. The ML feature builder maps AEGIS data into the XGBoost feature vector.
4. The XGBoost adapter returns fraud probability and risk band.
5. AEGIS combines `rule_score` and `ml_score` using `65% rule + 35% ML` when ML is enabled.
6. The Adaptive Friction Engine decides `ALLOW`, `REQUIRE_2FA`, `HOLD_FOR_REVIEW`, or `BLOCK_AND_ALERT`.

Get an analyst or admin token first:

```powershell
$token = (Invoke-RestMethod -Method Post http://localhost:8010/api/auth/login -ContentType "application/json" -Body '{"email":"analyst@aegis.test","password":"password123"}').access_token
```

Health check:

```powershell
Invoke-RestMethod http://localhost:8010/api/fraud/health -Headers @{Authorization="Bearer $token"}
```

Score one transaction:

```powershell
Invoke-RestMethod -Method Post http://localhost:8010/api/fraud/score `
  -Headers @{Authorization="Bearer $token"} `
  -ContentType "application/json" `
  -Body '{"transaction":{"amount":5000.0,"recipient_is_new":1,"login_vpn_count":2,"trust_score":30.0},"include_explanation":true}'
```

Score a batch:

```powershell
Invoke-RestMethod -Method Post http://localhost:8010/api/fraud/score-batch `
  -Headers @{Authorization="Bearer $token"} `
  -ContentType "application/json" `
  -Body '{"transactions":[{"amount":5000.0,"recipient_is_new":1,"login_vpn_count":2,"trust_score":30.0},{"amount":120.0,"recipient_is_new":0,"login_vpn_count":0,"trust_score":88.0}],"include_explanation":true}'
```

Feature names:

```powershell
Invoke-RestMethod http://localhost:8010/api/fraud/features -Headers @{Authorization="Bearer $token"}
```

Smoke test:

```powershell
cd backend
python -m app.dev_smoke_ml
```

## Viewing XGBoost ML Integration in Frontend

The React frontend makes the ML integration visible in the main demo flows:

- Customer transaction results show rule score, XGBoost ML score, ML probability, ML risk band, model version, fallback status, and the final combined risk.
- SOC Dashboard shows ML model health for analysts and admins.
- SOC Dashboard includes a small direct ML scoring test panel for analyst/admin demo checks.
- Admin Panel shows XGBoost model configuration, full model path, threshold, feature count, fallback error, and feature names.

If the model or ML dependencies are unavailable, the UI shows that ML fallback is active and the banking flow continues with rule-based scoring.

## Verified Bank Messages / Phishing Verification

AEGIS includes a simulated Communication Trust Center for defensive customer education and phishing prevention. It does not connect to real email or SMS providers, does not read a user's inbox, and only checks text that the user manually pastes into the app.

Customer flow:

1. Log in as `customer@aegis.test`.
2. Open `http://localhost:5173/messages`.
3. Review official simulated bank messages generated by AEGIS.
4. Paste a message into the checker.
5. View whether it is `VERIFIED_OFFICIAL`, `SUSPICIOUS`, `POSSIBLE_PHISHING`, or `UNKNOWN`.
6. Follow the displayed safety recommendation.

Analyst/admin visibility:

- SOC Dashboard and Admin Panel show recent message verification activity.
- Customers can only see their own official messages.
- Analysts and admins can review verification checks for demo investigation.

API endpoints:

```text
GET  /api/messages/my
POST /api/messages/verify
GET  /api/messages/checks
GET  /api/messages/all
```

Backend smoke test:

```powershell
cd backend
python -m app.dev_smoke_messages
```

Presentation demo:

1. Login as the customer.
2. Open Verified Messages.
3. Show official simulated bank messages.
4. Use the official quick-fill sample and verify it.
5. Use the phishing SMS sample:
   `URGENT: Your Fibank account has been blocked. Click http://fake-fibank-login.example to verify your password and OTP immediately.`
6. Show the phishing result, reasons, and recommendation.
7. Explain that this helps prevent account takeover before fraudulent transactions happen.

## Brand Protection Intelligence

AEGIS includes an analyst/admin-only Brand Protection module for defensive web threat intelligence. It checks possible Fibank lookalike and typosquatting domains with passive DNS resolution and normal HTTP/HTTPS metadata fetching.

Safety boundaries:

- No vulnerability testing, exploitation, authentication bypass, credential submission, or deep crawling.
- Scans run only when an analyst/admin manually starts one.
- AEGIS stores safe metadata only: domain, URL, status code, title, redirect target, favicon presence, and matched indicators.
- Customers cannot access `/api/brand-protection/*` endpoints or the frontend page.

Configuration is controlled by `.env`:

```text
BRAND_PROTECTION_ENABLED=true
BRAND_TARGET_DOMAIN=fibank.al
BRAND_TARGET_NAME=fibank
BRAND_TARGET_URL=https://www.fibank.al
BRAND_SCAN_QUICK_DEFAULT=true
BRAND_SCAN_MAX_CANDIDATES=300
BRAND_SCAN_REQUEST_TIMEOUT=8
BRAND_SCAN_REQUEST_DELAY=0.5
```

API endpoints:

```text
POST /api/brand-protection/scan
GET  /api/brand-protection/runs
GET  /api/brand-protection/runs/{scan_id}
GET  /api/brand-protection/latest
GET  /api/brand-protection/summary
GET  /api/brand-protection/config
```

Backend smoke test:

```powershell
cd backend
python -m app.dev_smoke_brand_protection
```

Frontend demo:

1. Login as `analyst@aegis.test` or `admin@aegis.test`.
2. Open `http://localhost:5173/brand-protection`.
3. Run a quick brand scan with a small candidate limit for live demos.
4. Show the findings table with risk score, risk level, matched brand keywords, and phishing signals.
5. Return to the SOC dashboard and show the Brand Protection summary card.

## Investigation Cases, Analyst Notes, and Risk Transparency

AEGIS treats every `HIGH` or `CRITICAL` fraud alert as a lightweight investigation case. It does not create a separate case-management workflow; the existing `FraudAlert` remains the case record, and analyst work is captured as notes and decision-trail entries.

Case behavior:

- `CRITICAL` alerts are `P1` investigation cases.
- `HIGH` alerts are `P2` investigation cases.
- `MEDIUM` alerts are `P3` alerts.
- `LOW` alerts are monitored.
- Status remains the existing alert status: `OPEN`, `INVESTIGATING`, `RESOLVED`, or `FALSE_POSITIVE`.

Analyst notes and decision trail:

- Analysts/admins can add notes on `/alerts/:alertId`.
- Status changes automatically create decision-trail entries.
- Resolving or marking false positive is recorded with a specific action type.
- Customers cannot access analyst notes or decision-trail endpoints.

Risk Transparency explains:

- Risk score bands and severity.
- Adaptive friction outcomes.
- Trust score impacts.
- XGBoost ML contribution and fail-open fallback.
- Enabled/disabled risk rules and their point values.

Routes and pages:

```text
GET  /api/alerts/{alert_id}/notes
POST /api/alerts/{alert_id}/notes
GET  /api/alerts/{alert_id}/decision-trail
GET  /api/risk/rules
GET  /api/risk/transparency

Frontend:
/alerts/:alertId
/risk-transparency
```

Backend smoke test:

```powershell
cd backend
python -m app.dev_smoke_cases_notes
```

Presentation demo:

1. Login as `analyst@aegis.test`.
2. Open the SOC Dashboard.
3. Open a HIGH or CRITICAL alert as an Investigation Case.
4. Add an analyst note.
5. Change status to `INVESTIGATING` with a short note.
6. Show the Decision Trail entry created by the status change.
7. Open Risk Transparency and explain rules, trust score, adaptive friction, and XGBoost contribution.

