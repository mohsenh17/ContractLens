Tasks Module
============

`tasks.py` defines Celery tasks for asynchronous contract processing.

- **process_contract(job_id, pdf_path)**

  1. Parse PDF
  2. Build vectorstore
  3. Run compliance analysis
  4. Updates job state in Redis at each step for frontend polling