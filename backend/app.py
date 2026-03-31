import uuid
import os
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

from redis_store import get_job, set_job
from tasks import process_contract
from vectorstore import get_vectorstore

app = Flask(__name__, template_folder=os.path.join('..', 'frontend'))
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    """
    Accepts a PDF file upload.
    Saves it, initialises job state in Redis, and enqueues a Celery task.
    Returns job_id immediately — the heavy lifting happens in the worker.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are supported"}), 400

    job_id = str(uuid.uuid4())
    pdf_path = os.path.join(UPLOAD_FOLDER, f"{job_id}.pdf")
    file.save(pdf_path)

    # Initialise job state before enqueuing so /status can respond immediately
    set_job(job_id, {"status": "queued", "result": None, "error": None})

    # Fire-and-forget — Celery worker picks this up asynchronously
    process_contract.delay(job_id, pdf_path)

    return jsonify({"job_id": job_id}), 202


@app.route("/status/<job_id>", methods=["GET"])
def status(job_id):
    """
    Poll this endpoint to check job progress.
    Returns status + result when done, sourced from Redis.
    """
    job = get_job(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job), 200


@app.route("/vectorstore_preview/<job_id>", methods=["GET"])
def vectorstore_preview(job_id):
    """
    Returns a limited preview of the vectorstore for a given job_id.
    Shows first N chunks and their metadata to verify build_vectorstore.
    """
    N = 5
    try:
        vs = get_vectorstore(job_id)
    except KeyError:
        return jsonify({"error": f"No vectorstore found for job_id {job_id}"}), 404

    preview_data = vs._collection.get(
        include=["documents", "metadatas", "embeddings"],
        limit=N
    )
    embedding_dims = [len(e) for e in preview_data["embeddings"]]

    return jsonify({
        "job_id": job_id,
        "preview_chunks": preview_data["documents"],
        "preview_metadata": preview_data["metadatas"],
        "embedding_dims": embedding_dims
    }), 200


@app.route("/chat/<job_id>", methods=["GET", "POST"])
def chat(job_id):
    """
    Combined route:
    - Renders the HTML page if accessed without 'question'.
    - Returns JSON answer if 'question' is provided (GET or POST).
    """
    job = get_job(job_id)
    if not job or job.get("status") != "done":
        return "Document not ready or not found", 400

    question = ""
    if request.method == "POST":
        data = request.get_json()
        question = data.get("question", "").strip() if data else ""
    else:
        question = request.args.get("question", "").strip()

    if not question:
        return render_template("chat.html", job_id=job_id)

    try:
        vs = get_vectorstore(job_id)
        docs = vs.similarity_search(question, k=4)
        context = "\n\n".join(d.page_content for d in docs)

        from langchain_ollama import OllamaLLM
        llm = OllamaLLM(model="llama3")
        prompt = (
            f"You are a contract analyst. Answer the question using ONLY the excerpts below.\n\n"
            f"Excerpts:\n{context}\n\n"
            f"Question: {question}\n\nAnswer:"
        )
        answer = llm.invoke(prompt)
        return jsonify({"answer": answer}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)