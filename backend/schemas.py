"""
schemas.py
----------
Pydantic models for validating and serializing the compliance analysis output.
"""

from typing import List, Literal
from pydantic import BaseModel, Field, field_validator


ComplianceState = Literal["Fully Compliant", "Partially Compliant", "Non-Compliant"]


class ComplianceResult(BaseModel):
    question_id: int = Field(..., description="Compliance question number (1-5)")
    question_title: str = Field(..., description="Short title of the compliance area")
    compliance_state: ComplianceState
    confidence: int = Field(..., ge=0, le=100, description="Confidence score 0-100")
    relevant_quotes: List[str] = Field(default_factory=list)
    rationale: str

    @field_validator("compliance_state", mode="before")
    @classmethod
    def normalize_state(cls, v: str) -> str:
        """
        Be lenient with LLM output — normalize common variants before
        strict validation kicks in.
        """
        if not isinstance(v, str):
            raise ValueError("compliance_state must be a string")
        v = v.strip()
        mapping = {
            "fully compliant": "Fully Compliant",
            "fully_compliant": "Fully Compliant",
            "partial": "Partially Compliant",
            "partially compliant": "Partially Compliant",
            "partially_compliant": "Partially Compliant",
            "non-compliant": "Non-Compliant",
            "non_compliant": "Non-Compliant",
            "noncompliant": "Non-Compliant",
            "not compliant": "Non-Compliant",
        }
        return mapping.get(v.lower(), v)


class ComplianceReport(BaseModel):
    job_id: str
    results: List[ComplianceResult]

    def to_dict(self):
        return self.model_dump()
