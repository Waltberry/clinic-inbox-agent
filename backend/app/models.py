# app/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from .database import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True, unique=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship("Message", back_populates="patient")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    channel = Column(String(50), nullable=False, default="email")  # email/sms/portal
    received_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="new")  # new/triaged/closed

    patient = relationship("Patient", back_populates="messages")
    triage_actions = relationship("TriageAction", back_populates="message")
    agent_runs = relationship("AgentRun", back_populates="message")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    model_name = Column(String(100), nullable=False)
    prompt = Column(Text, nullable=False)
    raw_response = Column(Text, nullable=False)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    message = relationship("Message", back_populates="agent_runs")
    triage_action = relationship("TriageAction", back_populates="agent_run", uselist=False)


class TriageAction(Base):
    __tablename__ = "triage_actions"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    agent_run_id = Column(Integer, ForeignKey("agent_runs.id"), nullable=False)

    urgency = Column(String(20), nullable=False)  # low/medium/high
    route = Column(String(50), nullable=False)    # billing/scheduling/clinical/other
    suggested_summary = Column(Text, nullable=True)

    suggested = Column(Boolean, default=True)
    status = Column(String(20), default="pending")  # pending/confirmed/overridden
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    message = relationship("Message", back_populates="triage_actions")
    agent_run = relationship("AgentRun", back_populates="triage_action")
