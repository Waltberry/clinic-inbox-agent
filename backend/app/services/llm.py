# app/services/llm.py
from functools import lru_cache
from typing import Tuple

from pydantic_settings import BaseSettings

from app.llm import classify_message_rule_based


class LLMSettings(BaseSettings):
    openai_api_key: str | None = None
    llm_model: str = "gpt-4o-mini"
    llm_fake: bool = False  # if True, use rule-based instead of real API

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_llm_settings() -> LLMSettings:
    return LLMSettings()


def parse_llm_output(text: str) -> Tuple[str, str, float, str]:
    """
    Very simple parser for the real LLM response.
    Expected style (you can refine prompt to enforce):

        urgency: high
        route: clinical
        confidence: 0.85
        summary: One-sentence summary here...

    Returns: (urgency, route, confidence, summary)
    """
    urgency = "medium"
    route = "clinical"
    confidence = 0.7
    summary = text.strip()

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines:
        lower = line.lower()
        if lower.startswith("urgency"):
            if "high" in lower:
                urgency = "high"
            elif "low" in lower:
                urgency = "low"
            else:
                urgency = "medium"
        elif lower.startswith("route"):
            if "billing" in lower:
                route = "billing"
            elif "scheduling" in lower:
                route = "scheduling"
            elif "clinical" in lower:
                route = "clinical"
            else:
                route = "other"
        elif lower.startswith("confidence"):
            for token in lower.split():
                try:
                    confidence = float(token)
                    break
                except ValueError:
                    continue
        elif lower.startswith("summary"):
            # e.g. "summary: text..."
            parts = line.split(":", 1)
            if len(parts) == 2:
                summary = parts[1].strip()

    return urgency, route, confidence, summary


def triage_message_with_llm(subject: str, body: str) -> tuple[str, str, float, str, str, str]:
    """
    Returns:
        urgency, route, confidence, model_name, prompt, raw_response
    """
    settings = get_llm_settings()

    prompt = (
        "You are an AI triage assistant for a medical clinic.\n"
        "Given an incoming patient message, respond in the following format:\n"
        "urgency: low|medium|high\n"
        "route: billing|scheduling|clinical|other\n"
        "confidence: float between 0 and 1\n"
        "summary: one-sentence summary of the situation\n\n"
        f"Subject: {subject}\n\n"
        f"Body:\n{body}\n"
    )

    # -------------------------------------------------
    # Fake mode: use rule-based classifier
    # -------------------------------------------------
    if settings.llm_fake or not settings.openai_api_key:
        combined = f"{subject}\n\n{body}"
        triage = classify_message_rule_based(combined)

        fake_response = (
            f"urgency: {triage.urgency}\n"
            f"route: {triage.category}\n"
            f"confidence: {triage.confidence:.2f}\n"
            f"summary: {triage.suggested_action}\n"
        )

        return (
            triage.urgency,
            triage.category,
            triage.confidence,
            settings.llm_model,
            prompt,
            fake_response,
        )

    # -------------------------------------------------
    # Real OpenAI call
    # -------------------------------------------------
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)

    completion = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": "You are an AI triage assistant for a medical clinic."},
            {"role": "user", "content": prompt},
        ],
    )

    raw_text = completion.choices[0].message.content or ""
    urgency, route, confidence, summary = parse_llm_output(raw_text)

    # We don't strictly need 'summary' for DB because we currently store suggested_summary
    # in TriageAction, but we keep it in the raw text for transparency.
    return urgency, route, confidence, settings.llm_model, prompt, raw_text
