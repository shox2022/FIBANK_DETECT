from collections import defaultdict
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import FraudAlert, MuleEdge, User
from app.services.explanation_engine import generate_explanation
from app.services.trust_engine import update_trust_score


def create_mule_ring(db: Session, mule_account: str, amount: float = 500.0):
    source_accounts = [
        "AL472091000000000002",
        "AL472091000000000003",
        "AL472091000000000004",
    ]
    created_edges = []
    for index, account in enumerate(source_accounts):
        edge = MuleEdge(
            from_account=account,
            to_account=mule_account,
            amount=amount + (index * 75),
            risk_score=85,
        )
        db.add(edge)
        created_edges.append(edge)

    outbound = MuleEdge(
        from_account=mule_account,
        to_account="AL472091000000008888",
        amount=(amount * len(source_accounts)) * 0.85,
        risk_score=92,
    )
    db.add(outbound)
    created_edges.append(outbound)

    explanation = generate_explanation(
        "MULE_RING",
        92,
        "CRITICAL",
        ["Mule connection", "fan-in", "pass-through"],
    )
    alert = FraudAlert(
        user_id=None,
        alert_type="MULE_RING",
        severity="CRITICAL",
        risk_score=92,
        title="Potential mule ring detected",
        explanation=explanation["summary"],
        recommended_action=explanation["recommended_action"],
        status="OPEN",
    )
    db.add(alert)
    db.commit()
    return {"edges": created_edges, "alert": alert, "graph": get_mule_graph(db)}


def analyze_mule_accounts(db: Session):
    edges = db.query(MuleEdge).all()
    incoming = defaultdict(list)
    outgoing = defaultdict(list)
    for edge in edges:
        incoming[edge.to_account].append(edge)
        outgoing[edge.from_account].append(edge)

    suspicious = set()
    for account, inbound_edges in incoming.items():
        unique_sources = {edge.from_account for edge in inbound_edges}
        received = sum(edge.amount for edge in inbound_edges)
        sent = sum(edge.amount for edge in outgoing.get(account, []))
        if len(unique_sources) >= 3:
            suspicious.add(account)
        if received and sent / received >= 0.8:
            suspicious.add(account)

    return suspicious


def get_mule_graph(db: Session):
    edges = db.query(MuleEdge).order_by(MuleEdge.created_at.asc()).all()
    suspicious = analyze_mule_accounts(db)
    accounts = set()
    for edge in edges:
        accounts.add(edge.from_account)
        accounts.add(edge.to_account)

    nodes = [
        {
            "id": account,
            "label": account,
            "node_type": "mule_candidate" if account in suspicious else "account",
            "risk_score": 90 if account in suspicious else 20,
            "suspicious": account in suspicious,
        }
        for account in sorted(accounts)
    ]
    graph_edges = [
        {
            "id": str(edge.id),
            "source": edge.from_account,
            "target": edge.to_account,
            "amount": edge.amount,
            "risk_score": edge.risk_score,
        }
        for edge in edges
    ]
    return {"nodes": nodes, "edges": graph_edges}

