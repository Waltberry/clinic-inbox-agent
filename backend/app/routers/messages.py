# app/routers/messages.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..deps import get_db

router = APIRouter(
    prefix="/messages",
    tags=["messages"],
)


@router.post("/", response_model=schemas.MessageRead)
def create_message(payload: schemas.MessageCreate, db: Session = Depends(get_db)):
    msg = models.Message(
        subject=payload.subject,
        body=payload.body,
        channel=payload.channel,
        patient_id=payload.patient_id,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


@router.get("/", response_model=list[schemas.MessageWithTriage])
def list_messages(db: Session = Depends(get_db)):
    messages = db.query(models.Message).order_by(models.Message.received_at.desc()).all()
    result: list[schemas.MessageWithTriage] = []

    for m in messages:
        latest_triage = (
            sorted(m.triage_actions, key=lambda t: t.created_at, reverse=True)[0]
            if m.triage_actions else None
        )
        latest_agent = (
            sorted(m.agent_runs, key=lambda a: a.created_at, reverse=True)[0]
            if m.agent_runs else None
        )

        result.append(
            schemas.MessageWithTriage(
                id=m.id,
                subject=m.subject,
                body=m.body,
                channel=m.channel,
                patient_id=m.patient_id,
                received_at=m.received_at,
                status=m.status,
                latest_triage=latest_triage,
                latest_agent_run=latest_agent,
            )
        )

    return result
