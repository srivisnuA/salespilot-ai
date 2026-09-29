from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models  # noqa: F401 — register models
from .database import Base, engine, SessionLocal
from .config import CORS_ORIGINS
from .routers import leads, emails, deals, analytics, automations, settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    from .seed import run_seed
    try:
        created = run_seed()
        if created:
            print("[salespilot] database seeded with demo data")
    except Exception as exc:  # never block boot on seeding
        print(f"[salespilot] seed skipped/failed: {exc}")
    yield


app = FastAPI(title="SalesPilot AI API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "salespilot-ai"}


app.include_router(leads.router)
app.include_router(emails.router)
app.include_router(deals.router)
app.include_router(analytics.router)
app.include_router(automations.router)
app.include_router(settings.router)
