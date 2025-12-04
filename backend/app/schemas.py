# app/schemas.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

# -------------------------------------------------
# Patient
# -------------------------------------------------


class PatientBase(BaseModel):
    full_name: str
    email: Optional[str] = None


class PatientCreate(PatientBase):
    pass


class PatientRead(PatientBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------
# Message
# -------------------------------------------------


class MessageBase(BaseModel):
    subject: str
    body: str
    channel: str = "email"
    patient_id: Optional[int] = None


class MessageCreate(MessageBase):
    pass


class MessageRead(MessageBase):
    id: int
    received_at: datetime
    status: str

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------
# AgentRun & TriageAction
# -------------------------------------------------


class AgentRunRead(BaseModel):
    id: int
    model_name: str
    confidence: Optional[float]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TriageActionBase(BaseModel):
    urgency: str      # low / medium / high
    route: str        # billing / scheduling / clinical / other
    suggested_summary: Optional[str] = None


class TriageActionRead(TriageActionBase):
    id: int
    status: str       # pending / confirmed / overridden
    suggested: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------
# Combined view for frontend
# -------------------------------------------------


class MessageWithTriage(MessageRead):
    latest_triage: Optional[TriageActionRead] = None
    latest_agent_run: Optional[AgentRunRead] = None


# -------------------------------------------------
# Triage request / response
# -------------------------------------------------


class TriageRequest(BaseModel):
    """
    User clicks 'Ask agent' on a specific message.
    """
    message_id: int


class TriageResponse(BaseModel):
    """
    What the frontend gets back after triage.
    """
    message: MessageRead
    triage: TriageActionRead
    agent_run: AgentRunRead
