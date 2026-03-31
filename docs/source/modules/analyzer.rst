Analyzer Module
===============

`analyzer.py` runs compliance analysis over a vectorstore of contract pages.

Workflow per question:

1. Retrieve top-k chunks from the vectorstore.
2. Build a prompt using requirement + context.
3. Call Ollama (llama3) to generate JSON response.
4. Parse and validate the response using Pydantic.
5. Retry once if parsing fails.

Key Functions
-------------

- **analyze_compliance(job_id)** → Returns serialized ComplianceReport for all 5 questions.
- **_analyze_single_question(llm, vs, question, job_id)** → Internal, runs analysis for a single question.
- **_try_parse_response(raw)** → Cleans JSON output and parses it.
- **_format_context(docs)** → Formats retrieved chunks into prompt context.