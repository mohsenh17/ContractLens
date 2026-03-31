ContractLens Documentation
==========================

Welcome to the documentation for **ContractLens**, a system for automated compliance analysis of PDF contracts.

This project parses PDF contracts, builds a vectorstore of their contents, and runs compliance analysis using a language model (Ollama / llama3) with pre-defined compliance rules.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules/vectorstore
   modules/analyzer
   modules/parser
   modules/schemas
   modules/tasks
   modules/app
   modules/redis_store
   modules/prompts

Getting Started
---------------

**Requirements:**

- Python >= 3.11
- Redis server running locally
- Celery for background task processing
- PDFplumber, langchain-ollama, chromadb, flask, pydantic

**Installation:**

.. code-block:: bash

    pip install -r requirements.txt

**Running the project:**

.. code-block:: bash

    # Start Redis
    redis-server

    # Start Celery worker
    celery -A celery_app worker --loglevel=info

    # Start Flask backend
    flask run --port=5000

Then open your browser at http://localhost:5000

---

Project Structure
-----------------

The repository has two main components: **backend** and **frontend**.

- backend/
    - analyzer.py      → Runs compliance analysis using LLM and vectorstore
    - app.py           → Flask API for upload, status, and chat
    - celery_app.py    → Celery configuration
    - parser.py        → Parses PDF pages and tables
    - prompts.py       → Defines compliance questions and analysis prompt template
    - redis_store.py   → Simple Redis-based job store
    - schemas.py       → Pydantic models for validation
    - tasks.py         → Celery tasks for end-to-end pipeline
    - vectorstore.py   → Builds Chroma vectorstore from PDF text and tables
- frontend/
    - index.html       → File upload page
    - chat.html        → Chat interface to query contract

---

API Overview
------------

The backend exposes the following endpoints:

- ``GET /`` → Returns the upload page
- ``POST /upload`` → Upload a PDF, returns a `job_id`
- ``GET /status/<job_id>`` → Check status (`queued`, `parsing`, `indexing`, `analyzing`, `done`)
- ``GET /vectorstore_preview/<job_id>`` → Preview first chunks of the vectorstore
- ``GET/POST /chat/<job_id>`` → Ask questions about a processed contract

---

Modules
-------

.. toctree::
   :maxdepth: 2

   modules/vectorstore
   modules/analyzer
   modules/parser
   modules/schemas
   modules/tasks
   modules/app
   modules/redis_store
   modules/prompts
