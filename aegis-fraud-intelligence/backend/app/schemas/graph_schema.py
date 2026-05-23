from pydantic import BaseModel


class GraphNode(BaseModel):
    id: str
    label: str
    node_type: str
    risk_score: int = 0
    suspicious: bool = False


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    amount: float
    risk_score: int = 0


class MuleGraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]

