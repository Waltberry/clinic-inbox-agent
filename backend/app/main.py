# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import messages, triage

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Clinic Inbox Agent")

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}


# 🔑 NOTE: prefix="/api" *here*,
# and routers themselves use "/messages" and "/triage"
app.include_router(messages.router, prefix="/api")
app.include_router(triage.router, prefix="/api")
