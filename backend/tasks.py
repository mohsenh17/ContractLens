from celery_app import celery
from redis_store import set_job, get_job
from parser import parse_pdf
from vectorstore import build_vectorstore
from analyzer import analyze_compliance


@celery.task(bind=True, max_retries=0)
def process_contract(self, job_id: str, pdf_path: str):
    """
    Runs the full contract processing pipeline:
      1. Parse PDF
      2. Build vectorstore
      3. Run compliance analysis

    Updates Redis-backed job state at each step so the frontend
    can reflect real-time progress via /status/<job_id>.
    """
    try:
        # ── Step 1: Parse ──────────────────────────────────────────────
        set_job(job_id, {"status": "parsing", "result": None, "error": None})
        pages = parse_pdf(pdf_path)
        print(f"[{job_id}] ✓ parsed {len(pages)} pages")

        # ── Step 2: Index ──────────────────────────────────────────────
        set_job(job_id, {"status": "indexing", "result": None, "error": None})
        print(f"[{job_id}] starting build_vectorstore...")
        build_vectorstore(job_id, pages)
        print(f"[{job_id}] ✓ vectorstore done")

        # ── Step 3: Analyze ────────────────────────────────────────────
        set_job(job_id, {"status": "analyzing", "result": None, "error": None})
        results = analyze_compliance(job_id)

        # ── Done ───────────────────────────────────────────────────────
        set_job(job_id, {"status": "done", "result": results, "error": None})

    except Exception as exc:
        set_job(job_id, {"status": "error", "result": None, "error": str(exc)})
        raise  # re-raise so Celery marks task as FAILURE in its own backend too