# app/routers/triage.py
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..deps import get_db
from ..services.llm import triage_message_with_llm

router = APIRouter(
    prefix="/triage",
    tags=["triage"],
)


@router.post("/", response_model=schemas.TriageResponse)
def triage_message(
    payload: schemas.TriageRequest,
    db: Session = Depends(get_db),
):
    # 1) Look up the message by ID
    msg = (
        db.query(models.Message)
        .filter(models.Message.id == payload.message_id)
        .first()
    )
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    # 2) Call LLM service (fake or real)
    (
        urgency,
        route,
        confidence,
        model_name,
        prompt,
        raw_response,
    ) = triage_message_with_llm(subject=msg.subject, body=msg.body)

    # 3) Store AgentRun
    agent_run = models.AgentRun(
        message_id=msg.id,
        model_name=model_name,
        prompt=prompt,
        raw_response=raw_response,
        confidence=confidence,
    )
    db.add(agent_run)
    db.flush()  # assign agent_run.id without full commit

    # 4) Store TriageAction
    triage = models.TriageAction(
        message_id=msg.id,
        agent_run_id=agent_run.id,
        urgency=urgency,
        route=route,
        suggested_summary=f"[{urgency.upper()}] {route} — {msg.subject}",
        suggested=True,
        status="pending",
    )
    db.add(triage)

    # 5) Update message status and commit everything
    msg.status = "triaged"
    db.commit()
    db.refresh(msg)
    db.refresh(agent_run)
    db.refresh(triage)

    # 6) Return structured response
    return schemas.TriageResponse(
        message=msg,
        triage=triage,
        agent_run=agent_run,
    )


@router.post("/{triage_id}/confirm", response_model=schemas.TriageActionRead)
def confirm_triage(triage_id: int, db: Session = Depends(get_db)):
    triage = (
        db.query(models.TriageAction)
        .filter(models.TriageAction.id == triage_id)
        .first()
    )
    if not triage:
        raise HTTPException(status_code=404, detail="Triage action not found")

    triage.status = "confirmed"
    triage.resolved_at = datetime.utcnow()
    triage.suggested = False
    db.commit()
    db.refresh(triage)
    return triage


@router.post("/{triage_id}/override", response_model=schemas.TriageActionRead)
def override_triage(
    triage_id: int,
    override: schemas.TriageActionBase,
    db: Session = Depends(get_db),
):
    triage = (
        db.query(models.TriageAction)
        .filter(models.TriageAction.id == triage_id)
        .first()
    )
    if not triage:
        raise HTTPException(status_code=404, detail="Triage action not found")

    triage.urgency = override.urgency
    triage.route = override.route
    triage.suggested_summary = override.suggested_summary
    triage.status = "overridden"
    triage.resolved_at = datetime.utcnow()
    triage.suggested = False
    db.commit()
    db.refresh(triage)
    return triage
