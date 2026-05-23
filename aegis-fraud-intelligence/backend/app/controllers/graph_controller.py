from sqlalchemy.orm import Session

from app.services.mule_engine import get_mule_graph


def mule_network(db: Session):
    return get_mule_graph(db)

