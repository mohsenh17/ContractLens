Schemas Module
==============

`schemas.py` defines Pydantic models for validating compliance results.

Models
------

- **ComplianceResult**
  - Fields: `question_id`, `question_title`, `compliance_state`, `confidence`, `relevant_quotes`, `rationale`
  - Normalizes compliance states (e.g., "noncompliant" → "Non-Compliant")

- **ComplianceReport**
  - Fields: `job_id`, `results` (list of ComplianceResult)
  - Method: `to_dict()` → Returns serialized dict