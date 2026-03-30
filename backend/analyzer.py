"""
analyzer.py
-----------
Runs compliance analysis for all 5 questions against a job's vectorstore.

Flow per question:
1. Retrieve top-k relevant chunks using the question's retrieval_query
2. Build prompt with requirement + chunks
3. Call Ollama (llama3)
4. Parse JSON response and validate with Pydantic
5. Retry once with a stricter prompt if parsing fails

Returns a serializable dict conforming to ComplianceReport schema.
"""

import json
import re
import logging
from typing import Any, Dict

from langchain_ollama import OllamaLLM

from vectorstore import get_vectorstore
from schemas import ComplianceResult, ComplianceReport
from prompts import COMPLIANCE_QUESTIONS, ANALYSIS_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)

OLLAMA_MODEL = "llama3"
TOP_K_CHUNKS = 6  # Chunks to retrieve per question

# Retry prompt — more explicit when the model returns bad JSON
RETRY_PROMPT_SUFFIX = """
IMPORTANT: Your previous response was not valid JSON. 
Respond with ONLY a raw JSON object. 
Start your response with {{ and end with }}.
Do not include any text before or after the JSON.
"""


def analyze_compliance(job_id: str) -> Dict[str, Any]:
    """
    Run compliance analysis for all questions for the given job_id.

    Returns:
        Serializable dict matching ComplianceReport schema.
    """
    vs = get_vectorstore(job_id)
    llm = OllamaLLM(model=OLLAMA_MODEL, temperature=0)

    results = []
    for question in COMPLIANCE_QUESTIONS:
        logger.info(f"Analyzing question {question['id']}: {question['title']}")
        result = _analyze_single_question(llm, vs, question, job_id)
        results.append(result)

    report = ComplianceReport(job_id=job_id, results=results)
    return report.to_dict()


def _analyze_single_question(
    llm: OllamaLLM,
    vs,
    question: Dict[str, Any],
    job_id: str,
) -> ComplianceResult:
    """
    Analyze one compliance question. Retries once on JSON parse failure.
    On second failure, returns a safe fallback result.
    """
    # Retrieve relevant chunks
    docs = vs.similarity_search(question["retrieval_query"], k=TOP_K_CHUNKS)
    context = _format_context(docs)

    prompt = ANALYSIS_PROMPT_TEMPLATE.format(
        requirement=question["requirement"],
        context=context,
    )

    # First attempt
    raw = llm.invoke(prompt)
    parsed = _try_parse_response(raw)

    # Retry on failure
    if parsed is None:
        logger.warning(f"Q{question['id']}: JSON parse failed, retrying...")
        retry_prompt = prompt + RETRY_PROMPT_SUFFIX
        raw = llm.invoke(retry_prompt)
        parsed = _try_parse_response(raw)

    # Fallback if retry also fails
    if parsed is None:
        logger.error(f"Q{question['id']}: Both attempts failed. Using fallback.")
        return ComplianceResult(
            question_id=question["id"],
            question_title=question["title"],
            compliance_state="Non-Compliant",
            confidence=0,
            relevant_quotes=[],
            rationale="Analysis failed: could not parse model response. Manual review required.",
        )

    # Validate with Pydantic
    try:
        return ComplianceResult(
            question_id=question["id"],
            question_title=question["title"],
            compliance_state=parsed.get("compliance_state", "Non-Compliant"),
            confidence=int(parsed.get("confidence", 50)),
            relevant_quotes=parsed.get("relevant_quotes", []),
            rationale=parsed.get("rationale", ""),
        )
    except Exception as e:
        logger.error(f"Q{question['id']}: Pydantic validation failed: {e}")
        return ComplianceResult(
            question_id=question["id"],
            question_title=question["title"],
            compliance_state="Non-Compliant",
            confidence=0,
            relevant_quotes=[],
            rationale=f"Validation error: {str(e)}. Manual review required.",
        )


def _try_parse_response(raw: str) -> Dict[str, Any] | None:
    """
    Attempt to parse the LLM's response as JSON.
    Handles common issues:
    - Markdown code fences (```json ... ```)
    - Leading/trailing prose before/after the JSON object
    """
    if not raw:
        return None

    # Strip markdown fences
    text = re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to extract just the JSON object via regex
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return None


def _format_context(docs) -> str:
    """
    Format retrieved documents into a readable context block for the prompt.
    Includes page number metadata so the model can reference sections.
    """
    parts = []
    for i, doc in enumerate(docs, 1):
        page = doc.metadata.get("page", "?")
        doc_type = doc.metadata.get("type", "text")
        label = f"Excerpt {i} (Page {page}, {doc_type})"
        parts.append(f"[{label}]\n{doc.page_content.strip()}")
    return "\n\n".join(parts)
