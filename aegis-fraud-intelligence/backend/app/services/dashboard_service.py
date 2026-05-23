from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import FraudAlert, MuleEdge, SecurityLog, Transaction, User
from app.services.mule_engine import analyze_mule_accounts


def get_dashboard_stats(db: Session):
    total_alerts = db.query(FraudAlert).count()
    critical_alerts = db.query(FraudAlert).filter(FraudAlert.severity == "CRITICAL").count()
    blocked_transactions = (
        db.query(Transaction).filter(Transaction.status == "BLOCKED").count()
    )
    average_trust_score = db.query(func.avg(User.trust_score)).scalar() or 0
    suspicious_log_count = (
        db.query(SecurityLog).filter(SecurityLog.risk_score >= 50).count()
    )
    mule_accounts_count = len(analyze_mule_accounts(db))

    recent_alerts = [
        {
            "id": alert.id,
            "title": alert.title,
            "severity": alert.severity,
            "risk_score": alert.risk_score,
            "status": alert.status,
            "created_at": alert.created_at,
        }
        for alert in db.query(FraudAlert).order_by(FraudAlert.created_at.desc()).limit(5)
    ]
    recent_transactions = [
        {
            "id": tx.id,
            "user_id": tx.user_id,
            "to_account": tx.to_account,
            "amount": tx.amount,
            "status": tx.status,
            "risk_score": tx.risk_score,
            "created_at": tx.created_at,
        }
        for tx in db.query(Transaction).order_by(Transaction.created_at.desc()).limit(5)
    ]

    return {
        "total_alerts": total_alerts,
        "critical_alerts": critical_alerts,
        "blocked_transactions": blocked_transactions,
        "average_trust_score": round(float(average_trust_score), 2),
        "suspicious_log_count": suspicious_log_count,
        "mule_accounts_count": mule_accounts_count,
        "recent_alerts": recent_alerts,
        "recent_transactions": recent_transactions,
    }

