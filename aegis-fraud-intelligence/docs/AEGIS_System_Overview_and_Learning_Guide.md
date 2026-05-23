# AEGIS Fraud Intelligence - System Overview and Learning Guide

**A beginner-friendly walkthrough of the fraud intelligence platform from frontend to backend.**

Generated for the AEGIS Fraud Intelligence prototype.

## 1. Executive Summary

AEGIS Fraud Intelligence is a banking fraud and threat intelligence prototype. It shows how a bank can combine customer behavior, device information, location context, transaction patterns, security logs, and AI scoring to decide whether an action is safe, suspicious, or dangerous.

The project is designed for demos and learning. A customer can simulate banking actions, while analysts and admins can investigate alerts in a SOC-style dashboard. The system includes rule-based scoring, XGBoost fraud scoring, trust score changes, adaptive friction, mule detection, phishing message verification, brand protection, investigation cases, analyst notes, decision trail, and role-based access control.

> **What to say in presentation:** AEGIS is not only a transaction checker. It connects banking activity, cyber signals, customer trust, phishing prevention, external brand monitoring, and analyst investigation into one explainable fraud intelligence workflow.

> **Why it matters:** Fraud rarely has one signal. AEGIS shows how small signals can become strong evidence when combined.

## 2. Main Idea of the System

The core formula is: Behaviour + Device + Location + Transaction + Logs + AI = Risk Intelligence.

Behaviour means how the customer acts: normal login times, transaction habits, failed attempts, and verification behavior.

Device means whether the device is known, trusted, or new. A new device can be normal, but it becomes suspicious when combined with VPN, new country, or a large transaction.

Location means where a login or session happens. If a customer logs in from Albania and then Germany soon after, AEGIS treats that as impossible travel.

Transaction means the amount, recipient, beneficiary novelty, and velocity of money movement.

Logs mean security events such as SQL injection attempts, token reuse, suspicious endpoints, and brute force patterns.

AI means the XGBoost model and deterministic explanation layer. The model adds probability-based fraud scoring, while rule explanations keep the decision understandable.

## 3. System Architecture Overview

AEGIS follows a clean full-stack structure. The frontend is a React app. The backend is a FastAPI API. SQLAlchemy models define the SQLite database tables. Services and engines contain the main business logic.

The main pattern is: user action in the frontend -> API route -> controller -> service/engine -> database/model -> response back to frontend.

```text
Customer App / Analyst UI / Admin UI
        |
        v
React + Vite Frontend
        |
        v
FastAPI Backend (/api)
        |
        v
Routes -> Controllers -> Services / Engines
        |
        +--> SQLite Database
        +--> XGBoost ML Adapter
        +--> Brand Protection Detector
        +--> Verified Messages Checker
        |
        v
SOC Dashboard, Investigation Cases, Risk Transparency
```

> **How it works technically:** Routes receive HTTP requests. Controllers keep request/response orchestration thin. Services contain the actual fraud logic. Models represent database tables.

## 4. User Roles and RBAC

RBAC means role-based access control. It decides what each logged-in user is allowed to see or do. AEGIS uses JWT authentication and three roles: CUSTOMER, ANALYST, and ADMIN.

| Role | Can access | Cannot access |
| --- | --- | --- |
| CUSTOMER | Customer App, transfer simulation, Verified Bank Messages, phishing checker, own safety results | SOC dashboard, logs, analyst notes, admin panel, brand protection, risk transparency |
| ANALYST | SOC dashboard, alerts, investigation cases, notes, decision trail, logs, mule graph, brand protection, risk transparency, ML status | Admin-only user/rule management |
| ADMIN | Everything analyst can access plus Admin Panel, users, risk rules, model/config views | No practical restrictions in the prototype |

> **Why it matters:** A customer should never see internal analyst notes, security logs, or brand scan findings. RBAC protects sensitive operational data.

## 5. Frontend Overview

The frontend is the presentation layer. It makes the prototype easy to demo and shows different experiences for customers, analysts, and admins.

| Page | Role | Purpose | Main endpoints |
| --- | --- | --- | --- |
| Login | All | Authenticate and redirect users by role. | POST /api/auth/login, GET /api/auth/me |
| Customer App | CUSTOMER | Simulate banking activity and fraud scenarios. | /api/simulate/*, /api/users/{id} |
| Verified Messages | CUSTOMER, optional analyst/admin | Verify official bank messages and phishing attempts. | GET /api/messages/my, POST /api/messages/verify |
| SOC Dashboard | ANALYST, ADMIN | Monitor alerts, logs, mule graph, ML status, brand summary, and cases. | /api/dashboard/stats, /api/alerts, /api/logs, /api/graph/mule-network |
| Alert Details / Investigation Case | ANALYST, ADMIN | Investigate alerts, add notes, update status, generate incident reports. | /api/alerts/{id}, /api/alerts/{id}/notes, /api/alerts/{id}/decision-trail |
| Risk Transparency | ANALYST, ADMIN | Explain risk levels, rules, trust score, friction, and ML contribution. | /api/risk/rules, /api/risk/transparency |
| Brand Protection | ANALYST, ADMIN | Run passive brand scans for lookalike domains. | /api/brand-protection/* |
| Admin Panel | ADMIN | View users, rules, ML config, and brand config. | /api/admin/users, /api/admin/rules |
| Access Denied | All | Friendly page for blocked access. | Frontend route guard |

## 6. Backend Overview

The backend is a FastAPI application. It exposes REST endpoints under /api and uses SQLAlchemy with SQLite for local storage.

main.py creates the FastAPI app, enables CORS, creates tables on startup, and registers routers.

routes/ defines URL endpoints and RBAC dependencies. controllers/ calls service functions and shapes responses. services/ contains fraud logic, risk engines, ML adapters, message verification, brand protection, and dashboard logic. schemas/ defines Pydantic request/response validation. models/ defines database tables. core/ contains JWT security and RBAC. ml/ contains the XGBoost detector files. threat_intel/ contains the brand protection detector.

> **Route -> Controller -> Service -> Model/Database:** This separation keeps the code easier to test and explain. HTTP details stay near routes, business logic stays in services, and data structure stays in models.

## 7. Database and Main Models

AEGIS uses a local SQLite database. Each SQLAlchemy model represents a table. The database is created automatically on backend startup and seeded with demo data.

```text
User
 |-- Devices
 |-- Sessions
 |-- LoginEvents
 |-- Transactions
 |-- FraudAlerts
 |    |-- AnalystNotes
 |    +-- IncidentReport (generated response)
 |-- TrustScoreHistory
 |-- BankMessages
 +-- MessageVerificationChecks

BrandScanRun
 +-- BrandThreatFindings

RiskRule
 +-- Used by Risk Transparency and risk scoring explanation
```

| Model | What it stores | Why it matters |
| --- | --- | --- |
| User | Customer, analyst, and admin accounts | Main identity and trust-score anchor |
| Device | Known customer devices, OS, browser, trusted flag | Detects new or untrusted devices |
| Session | Session token hash, IP, country, active state | Supports token theft and session anomaly checks |
| LoginEvent | Login country, device, VPN/proxy, failed attempts, risk | Feeds login risk and impossible travel |
| Transaction | Transfers, amount, recipient, status, risk | Core banking activity being scored |
| SecurityLog | Suspicious app/security events | Connects application security to fraud intelligence |
| FraudAlert | Alerts generated from suspicious activity | Base record for investigation cases |
| TrustScoreHistory | Old/new trust scores and reasons | Explains trust changes over time |
| MuleEdge | Money movement between accounts | Builds mule graph patterns |
| RiskRule | Rule code, description, points, enabled flag | Supports transparency and explainability |
| BankMessage | Official simulated bank messages | Lets customers verify real bank communication |
| MessageVerificationCheck | Customer-submitted message checks | Shows phishing-report activity |
| BrandScanRun | Brand scan summary | Stores passive web threat intelligence runs |
| BrandThreatFinding | Lookalike domain findings | Stores safe metadata and risk indicators |
| AnalystNote | Notes, status changes, decisions | Creates decision trail for cases |

## 8. Risk Engine

The rule-based risk engine is deterministic. That means it follows fixed rules and can explain why a score changed.

Login risk can increase for a new device, VPN, proxy, new country, impossible travel, failed attempts, or unusual hour.

Transaction risk can increase for an amount spike, new beneficiary, transaction after suspicious login, fast transaction burst, flagged recipient, or VPN login before transfer.

Security log risk can increase for SQL injection patterns, brute force, suspicious endpoint access, and token reuse.

Token theft risk can increase if the same token appears from a different IP, country, device, or VPN/proxy context.

| Score range | Severity | Meaning |
| --- | --- | --- |
| 0-30 | LOW | Usually safe |
| 31-60 | MEDIUM | Needs extra verification |
| 61-80 | HIGH | Hold and review |
| 81-100 | CRITICAL | Block and alert immediately |

> **Why it matters:** Rules make the system explainable. During a demo, you can point to exact reasons instead of saying the system is a black box.

## 9. XGBoost ML Fraud Scoring

The XGBoost model is trained separately and integrated into AEGIS through an adapter. AEGIS does not need to retrain the model during normal app use.

fraud_detector.py loads fibank_fraud_model.ubj. ml_score_engine.py lazy-loads the detector and normalizes model output for the rest of AEGIS. ml_feature_builder.py converts user, login, device, security log, trust, and transaction context into model features.

The model returns fraud_probability, fraud_percentage or ml_score, fraud_flag, fraud_risk_band, and missing_features.

When ML is enabled, AEGIS combines the deterministic rule score and ML score with: final_score = rule_score * 0.65 + ml_score * 0.35.

If the model is unavailable and fail-open is enabled, AEGIS continues with rule-based scoring. This prevents the banking flow from breaking.

```text
Transaction
   |
   +--> Rule Engine ---------> rule_score
   |
   +--> Feature Builder -----> XGBoost model -----> ml_score
                                         |
                                         v
Combined final_score = 65% rule + 35% ML
   |
   v
Adaptive Friction: allow, 2FA, hold, or block
```

> **What to say in presentation:** The model improves risk intelligence, but AEGIS never depends blindly on it. The rule engine remains active, and missing ML gracefully falls back.

## 10. Adaptive Friction Engine

Adaptive friction means the bank does not treat every event the same. Low-risk activity stays smooth. Higher-risk activity gets extra verification, review, or blocking.

| Risk level | Action | Customer experience |
| --- | --- | --- |
| LOW | ALLOW | Transaction is allowed |
| MEDIUM | REQUIRE_2FA | Customer must complete extra verification |
| HIGH | HOLD_FOR_REVIEW | Transaction is held for analyst review |
| CRITICAL | BLOCK_AND_ALERT | Transaction is blocked and alert is created |

## 11. Trust Score Engine

The trust score is a number from 0 to 100 that represents customer trust context. It is not the same as the risk score. Risk score measures one event. Trust score measures the customer's longer-term safety profile.

Trust can decrease for new device, VPN, proxy, impossible travel, token theft, SQL injection, high-risk transaction, or mule connection.

Trust can increase for trusted-device normal login, normal transaction, or successful verification simulation.

Trust affects adaptive friction. A trusted customer may still need 2FA, while a low-trust customer can be escalated to review or blocking.

## 12. Fraud Alert and Investigation Case Flow

FraudAlert is the central alert record. AEGIS treats HIGH and CRITICAL alerts as investigation cases without adding a heavy new case-management system.

CRITICAL alerts become Priority 1 cases. HIGH alerts become Priority 2 cases. MEDIUM alerts are Priority 3. LOW alerts are monitored.

Analyst notes and status changes are saved as AnalystNote records. This creates the decision trail.

```text
Suspicious event
   |
   v
Risk score calculated
   |
   v
FraudAlert created
   |
   +-- HIGH / CRITICAL --> Investigation Case
                            |
                            v
                       Analyst opens case
                            |
                            v
                    Notes + status changes
                            |
                            v
                       Decision trail
                            |
                            v
                    Incident report generated
```

> **How it works technically:** PATCH /api/alerts/{id}/status updates the alert status and creates an AnalystNote entry. GET /api/alerts/{id}/decision-trail returns the chronological audit trail.

## 13. Verified Bank Messages / Phishing Verification

This feature helps a customer check whether a message claiming to be from the bank is official or suspicious.

The app shows official simulated bank messages. The customer can paste an email, SMS, or message into the checker. AEGIS compares it with official messages and checks phishing indicators.

Results can be VERIFIED_OFFICIAL, SUSPICIOUS, POSSIBLE_PHISHING, or UNKNOWN.

Phishing indicators include external links, urgency, requests for password/PIN/CVV/OTP, account blocked or suspended language, and messages not found in official messages.

```text
Customer pastes suspicious SMS/email
        |
        v
Compare with official simulated bank messages
        |
        v
Check phishing indicators
        |
        v
Result: VERIFIED_OFFICIAL, SUSPICIOUS,
        POSSIBLE_PHISHING, or UNKNOWN
        |
        v
Customer receives safety recommendation
```

> **Demo example:** Paste: URGENT: Your Fibank account has been blocked. Click http://fake-fibank-login.example to verify your password and OTP immediately. The system should flag possible phishing and explain why.

## 14. Brand Protection / Web Threat Intelligence

Brand Protection helps analysts/admins find possible lookalike or phishing domains impersonating Fibank.

The detector generates candidate domains, checks passive DNS resolution, fetches reachable public page metadata, looks for brand keywords and phishing signals, and stores findings.

This module is passive and manually triggered. It does not exploit websites, log in, submit forms, test vulnerabilities, or crawl deeply.

```text
Analyst starts quick brand scan
        |
        v
Generate Fibank-like candidate domains
        |
        v
Passive DNS resolution
        |
        v
Fetch public page metadata only
        |
        v
Score brand keywords + phishing signals
        |
        v
Store findings and show dashboard summary
```

> **Why it matters:** Fraud often starts before the bank transaction. A fake domain can steal credentials that later cause account takeover.

## 15. Mule Account Detection

A mule account is an account used to receive and move stolen or suspicious funds. AEGIS models account movement as graph edges.

A common pattern is fan-in: several unrelated accounts send to one account. Another pattern is pass-through: the receiving account quickly sends most of the money elsewhere.

```text
User A ----\
User B -----+----> Account X ----> External Account
User C ----/

Pattern: fan-in + fast pass-through = possible mule account
```

## 16. Token Theft Detection

A session token should normally stay tied to the same device, IP, and location context. If the same token appears from a different IP, device, or country, it may be stolen.

AEGIS can mark the session inactive, create a critical alert, reduce trust, and recommend re-authentication.

## 17. SQL Injection / Security Log Detection

AEGIS looks at security logs for suspicious payloads and endpoint access. Example indicators include SQL injection strings such as ' OR '1'='1 --, UNION SELECT, DROP TABLE, comments, script tags, and command-execution patterns.

This is defensive monitoring. It helps connect application attacks to fraud risk because attackers may use technical attacks to access accounts or systems.

## 18. Main Demo Scenarios

| Scenario | What to click | Backend behavior | Dashboard result | What to say |
| --- | --- | --- | --- | --- |
| Normal login and transfer | Customer App: normal login, normal transfer | Low rule risk, normal trust behavior | Low/no alert | Good customers should not be punished with unnecessary friction. |
| Impossible travel | Login from Albania, then Germany VPN login | Login risk increases for new country, VPN, impossible travel | HIGH/CRITICAL alert | AEGIS connects location and timing, not just password success. |
| Token theft | Token theft simulation | Same token appears from different IP/device/country | Critical alert and session invalidation | Token behavior is treated as a fraud signal. |
| High-risk transaction with ML | High-value transfer to new beneficiary | Rule score + XGBoost score combine | Held/blocked transaction and case | ML supports the decision, but rules keep it explainable. |
| SQL injection/security log | SQL injection attempt | Security log risk hits critical | Critical security alert | Cyber signals feed fraud intelligence. |
| Mule ring | Mule ring simulation | Mule edges created and graph updated | Mule graph shows suspicious account | Money movement patterns reveal mule behavior. |
| Verified Messages | Open Verified Messages and paste phishing SMS | Message checked against official messages and phishing indicators | Customer gets warning; analysts see activity | Prevention starts before account takeover. |
| Brand Protection | Run quick brand scan | Passive DNS/page metadata scoring | Findings table and SOC summary | External threat intelligence protects the bank brand. |
| Investigation Case | Open HIGH/CRITICAL alert, add note, change status | AnalystNote records created | Decision trail visible | Analyst work becomes auditable and explainable. |

## 19. End-to-End Flow: High-Risk Transaction

This is the main story for a live fraud demo. A customer initiates a transfer in the frontend. The frontend calls POST /api/simulate/transaction. The backend route receives the request, the controller delegates to the simulation service, and the service calls risk and ML engines.

The rule engine calculates rule_score. The feature builder creates ML features. XGBoost returns ml_score and risk band. AEGIS combines them into final risk, then the adaptive friction engine chooses ALLOW, REQUIRE_2FA, HOLD_FOR_REVIEW, or BLOCK_AND_ALERT.

The transaction is saved, trust may be updated, a fraud alert may be created, and the SOC dashboard shows the event. Analysts can open it as an investigation case, add notes, update status, and generate an incident report.

```text
Customer starts transfer
   |
   v
Frontend POST /api/simulate/transaction
   |
   v
Route -> Controller -> Simulation Service
   |
   v
Rule risk + ML score + trust context
   |
   v
Adaptive friction decides status
   |
   v
Transaction saved, trust updated, alert created
   |
   v
SOC dashboard shows case
   |
   v
Analyst adds notes and generates incident report
```

## 20. End-to-End Flow: Phishing Message Verification

The customer pastes a suspicious message into the Verified Messages page. The backend compares it against official simulated messages for that user. If it matches, the result is VERIFIED_OFFICIAL.

If it does not match, AEGIS checks phishing indicators such as suspicious links, urgency, password/OTP requests, and account-blocked wording. It returns a risk score, result, reasons, and recommendation. Analysts/admins can view recent verification activity.

## 21. End-to-End Flow: Brand Protection

An analyst/admin manually starts a quick scan. AEGIS generates candidate domains that look like Fibank, checks DNS resolution, fetches public page metadata for live domains, scores brand and phishing signals, stores findings, and shows a summary on the SOC dashboard.

```text
Analyst starts quick brand scan
        |
        v
Generate Fibank-like candidate domains
        |
        v
Passive DNS resolution
        |
        v
Fetch public page metadata only
        |
        v
Score brand keywords + phishing signals
        |
        v
Store findings and show dashboard summary
```

## 22. What Happens If Something Fails?

| Failure | AEGIS behavior |
| --- | --- |
| ML model missing | Rule-based scoring continues if fail-open is enabled |
| Backend unavailable | Frontend shows API error/loading feedback instead of crashing |
| No brand scan data | Dashboard shows empty state and prompts user to run scan |
| Missing optional fields | UI uses safe fallback text like Unknown, N/A, or empty state |
| Unauthorized access | Backend returns 403 and frontend can show Access Denied |

## 23. Security and Privacy Design

AEGIS uses JWT authentication and RBAC. Customers cannot access analyst/admin routes. Analysts and admins can investigate but customers only see their own customer-facing features.

The Verified Messages feature does not integrate with real email or SMS providers and does not read a customer's inbox. The customer manually pastes text for checking.

Brand Protection uses passive checks only. It does not exploit, submit forms, authenticate, or crawl deeply.

Device identifiers should be hashed, logs should be minimized, AI decisions should be explainable, and analyst decision trails support auditability.

## 24. API Overview

| Area | Endpoints |
| --- | --- |
| Auth | POST /api/auth/login; GET /api/auth/me |
| Simulation | POST /api/simulate/login; /transaction; /security-log; /token-theft; /mule-ring |
| Fraud/ML | GET /api/fraud/health; POST /api/fraud/score; POST /api/fraud/score-batch; GET /api/fraud/features |
| Alerts/Cases | GET /api/alerts; GET /api/alerts/{id}; PATCH /api/alerts/{id}/status; GET /incident-report; GET/POST /notes; GET /decision-trail |
| Messages | GET /api/messages/my; POST /api/messages/verify; GET /api/messages/checks |
| Brand Protection | POST /api/brand-protection/scan; GET /runs; GET /latest; GET /summary |
| Risk Transparency | GET /api/risk/rules; GET /api/risk/transparency |
| Admin | GET /api/admin/users; GET /api/admin/rules |

## 25. Glossary

| Term | Simple meaning |
| --- | --- |
| Fraud detection | Finding activity that may be unauthorized or criminal |
| Risk score | A number showing how suspicious one event is |
| Trust score | A longer-term score for customer/account trust |
| Adaptive friction | Adding verification or blocking only when risk requires it |
| XGBoost | A machine-learning model often used for tabular prediction |
| ML score | Fraud score returned by the machine-learning model |
| Rule score | Fraud score returned by deterministic rules |
| Token theft | A stolen session token used from a new IP/device/country |
| Mule account | An account used to receive and move suspicious funds |
| Phishing | Fake messages/sites that trick users into sharing secrets |
| Typosquatting | Registering lookalike domains with small spelling changes |
| Brand protection | Monitoring for external impersonation of the bank |
| SOC dashboard | Security operations view for analysts |
| RBAC | Role-based access control |
| JWT | A signed token used to prove who is logged in |
| API endpoint | A URL that frontend calls to perform an action |
| Controller | Backend layer that orchestrates request/response |
| Service | Backend layer containing business logic |
| Model | Python class representing a database table |
| Database table | Structured storage for records |
| Incident report | Generated investigation summary |
| Decision trail | Chronological record of analyst actions |

## 26. Presentation Talking Points

AEGIS solves the problem of fragmented fraud signals. Instead of looking only at transactions, it combines behavior, device, location, logs, trust, AI, phishing prevention, and brand threat intelligence.

It is better than simple fraud rules because rules are explainable and ML adds probability-based intelligence. Together they create a stronger decision.

ML is used safely: if it is unavailable, rule-based scoring continues. Analysts can also see model status and scoring details.

Customers are protected before fraud happens through Verified Bank Messages. They can check suspicious messages before clicking links or sharing OTPs.

Analysts investigate alerts as lightweight cases, add notes, change status, and generate incident reports. The decision trail supports auditability.

Brand Protection adds external threat intelligence by identifying lookalike domains and phishing indicators.

Privacy and explainability matter because fraud systems affect real customers. AEGIS shows why decisions happened and limits access by role.

## 27. Suggested Visuals

The diagrams in this guide are intentionally simple so they can be reused in slides or spoken explanations. For a hackathon demo, show the overall architecture first, then one complete transaction flow, then the analyst case workflow.

```text
Customer App / Analyst UI / Admin UI
        |
        v
React + Vite Frontend
        |
        v
FastAPI Backend (/api)
        |
        v
Routes -> Controllers -> Services / Engines
        |
        +--> SQLite Database
        +--> XGBoost ML Adapter
        +--> Brand Protection Detector
        +--> Verified Messages Checker
        |
        v
SOC Dashboard, Investigation Cases, Risk Transparency
```

```text
Transaction
   |
   +--> Rule Engine ---------> rule_score
   |
   +--> Feature Builder -----> XGBoost model -----> ml_score
                                         |
                                         v
Combined final_score = 65% rule + 35% ML
   |
   v
Adaptive Friction: allow, 2FA, hold, or block
```

```text
Suspicious event
   |
   v
Risk score calculated
   |
   v
FraudAlert created
   |
   +-- HIGH / CRITICAL --> Investigation Case
                            |
                            v
                       Analyst opens case
                            |
                            v
                    Notes + status changes
                            |
                            v
                       Decision trail
                            |
                            v
                    Incident report generated
```

```text
Customer pastes suspicious SMS/email
        |
        v
Compare with official simulated bank messages
        |
        v
Check phishing indicators
        |
        v
Result: VERIFIED_OFFICIAL, SUSPICIOUS,
        POSSIBLE_PHISHING, or UNKNOWN
        |
        v
Customer receives safety recommendation
```

```text
Analyst starts quick brand scan
        |
        v
Generate Fibank-like candidate domains
        |
        v
Passive DNS resolution
        |
        v
Fetch public page metadata only
        |
        v
Score brand keywords + phishing signals
        |
        v
Store findings and show dashboard summary
```

```text
User
 |-- Devices
 |-- Sessions
 |-- LoginEvents
 |-- Transactions
 |-- FraudAlerts
 |    |-- AnalystNotes
 |    +-- IncidentReport (generated response)
 |-- TrustScoreHistory
 |-- BankMessages
 +-- MessageVerificationChecks

BrandScanRun
 +-- BrandThreatFindings

RiskRule
 +-- Used by Risk Transparency and risk scoring explanation
```
