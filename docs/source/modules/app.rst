App Module
==========

`app.py` provides Flask endpoints for file upload, job status, vectorstore preview, and chat interface.

Endpoints
---------

- `/` → Upload page
- `/upload` → Accepts PDF, enqueues Celery task
- `/status/<job_id>` → Returns job status and results
- `/vectorstore_preview/<job_id>` → Preview vectorstore
- `/chat/<job_id>` → Chat with contract data