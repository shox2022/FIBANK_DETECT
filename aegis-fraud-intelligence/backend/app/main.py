from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routes import (
    admin_routes,
    alert_routes,
    analyst_note_routes,
    auth_routes,
    brand_protection_routes,
    dashboard_routes,
    graph_routes,
    log_routes,
    message_routes,
    ml_routes,
    risk_routes,
    simulate_routes,
    user_routes,
)
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="AEGIS Fraud Intelligence API",
    description="Adaptive Engine for Guarded Intelligence & Security",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router, prefix="/api/auth", tags=["auth"])
app.include_router(
    brand_protection_routes.router,
    prefix="/api/brand-protection",
    tags=["brand-protection"],
)
app.include_router(simulate_routes.router, prefix="/api/simulate", tags=["simulation"])
app.include_router(dashboard_routes.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(alert_routes.router, prefix="/api/alerts", tags=["alerts"])
app.include_router(analyst_note_routes.router, prefix="/api", tags=["analyst-notes"])
app.include_router(user_routes.router, prefix="/api/users", tags=["users"])
app.include_router(graph_routes.router, prefix="/api/graph", tags=["graph"])
app.include_router(log_routes.router, prefix="/api/logs", tags=["logs"])
app.include_router(message_routes.router, prefix="/api/messages", tags=["messages"])
app.include_router(ml_routes.router, prefix="/api/fraud", tags=["fraud-ml"])
app.include_router(risk_routes.router, prefix="/api/risk", tags=["risk-transparency"])
app.include_router(admin_routes.router, prefix="/api/admin", tags=["admin"])


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "AEGIS Fraud Intelligence API",
        "phase": "backend-phase-1",
    }

