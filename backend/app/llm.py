# app/llm.py
from dataclasses import dataclass
from typing import Literal

Urgency = Literal["low", "medium", "high"]
Category = Literal["billing", "scheduling", "clinical", "other"]


@dataclass
class TriageResult:
    urgency: Urgency
    category: Category
    suggested_action: str
    confidence: float
    raw_reasoning: str


def classify_message_rule_based(content: str) -> TriageResult:
    """
    Tiny rule-based classifier to simulate an LLM.
    Later you can swap this with a real OpenAI call.
    """
    text = content.lower()

    # --- Category heuristics ---
    if any(k in text for k in ["bill", "billing", "invoice", "payment", "pay", "refund"]):
        category: Category = "billing"
    elif any(k in text for k in ["appointment", "schedule", "reschedule", "booking", "cancel", "follow-up", "follow up"]):
        category = "scheduling"
    elif any(k in text for k in ["pain", "bleeding", "fever", "chest", "dizzy", "medication", "dose", "prescription"]):
        category = "clinical"
    else:
        category = "other"

    # --- Urgency heuristics ---
    if any(k in text for k in ["chest pain", "shortness of breath", "cant breathe", "confused",
                               "fainted", "severe pain", "bleeding", "very sick"]):
        urgency: Urgency = "high"
    elif any(k in text for k in ["worsening", "getting worse", "not improving",
                                 "still in pain", "urgent", "today"]):
        urgency = "medium"
    else:
        urgency = "low"

    # --- Suggested action ---
    if category == "billing":
        suggested_action = "Send billing clarification template / route to billing queue"
    elif category == "scheduling":
        if urgency == "high":
            suggested_action = "Call patient and offer earliest same-day / next-day slot"
        else:
            suggested_action = "Offer next available follow-up and confirm preferred time window"
    elif category == "clinical":
        if urgency == "high":
            suggested_action = (
                "Escalate to on-call clinician immediately and advise patient to seek urgent care if needed"
            )
        else:
            suggested_action = "Route to clinician for review within 24–48 hours"
    else:
        suggested_action = "Route to general admin queue for manual review"

    confidence = 0.9 if category in ["billing", "scheduling", "clinical"] else 0.7
    reasoning = f"Category={category}, Urgency={urgency}, Confidence={confidence:.2f}"

    return TriageResult(
        urgency=urgency,
        category=category,
        suggested_action=suggested_action,
        confidence=confidence,
        raw_reasoning=reasoning,
    )
