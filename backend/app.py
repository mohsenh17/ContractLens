import uuid
import os
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

from parser import parse_pdf
from vectorstore import build_vectorstore, get_vectorstore
from analyzer import analyze_compliance

app = Flask(__name__, template_folder=os.path.join('..', 'frontend'))
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# In-memory job store: { job_id: { status, result, error } }
jobs = {}

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    """
    Accepts a PDF file upload.
    Saves it, parses it, builds a vectorstore, kicks off compliance analysis.
    Returns a job_id immediately.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are supported"}), 400

    job_id = str(uuid.uuid4())
    pdf_path = os.path.join(UPLOAD_FOLDER, f"{job_id}.pdf")
    file.save(pdf_path)

    jobs[job_id] = {"status": "parsing", "result": None, "error": None, "parsed_pages": None}

    # we should migrate to celery and redis (see if time permits)
    try:
        # Step 1: Parse PDF
        jobs[job_id]["status"] = "parsing"
        pages = parse_pdf(pdf_path)
        #jobs[job_id]["parsed_pages"] = pages

        # Step 2: Build vectorstore
        jobs[job_id]["status"] = "indexing"
        build_vectorstore(job_id, pages)

        # Step 3: Run compliance analysis
        jobs[job_id]["status"] = "analyzing"
        results = analyze_compliance(job_id)

        jobs[job_id]["status"] = "done"
        jobs[job_id]["result"] = results

    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)

    return jsonify({"job_id": job_id}), 202

@app.route("/status/<job_id>", methods=["GET"])
def status(job_id):
    """
    Poll this endpoint to check job progress.
    Returns status + result when done.
    """
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job), 200

@app.route("/parsed/<job_id>", methods=["GET"])
def parsed(job_id):
    """
    Get the parsed content for a specific job.
    """
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    # Return the parsed content (if available)
    if job.get("parsed_pages") is None:
        return jsonify({"error": "Parsing not done yet"}), 202

    return jsonify({"parsed_pages": job["parsed_pages"]}), 200



@app.route("/vectorstore_preview/<job_id>", methods=["GET"])
def vectorstore_preview(job_id):
    """
    Returns a limited preview of the vectorstore for a given job_id.
    Shows first N chunks and their metadata to verify build_vectorstore.
    """
    N = 5  # number of chunks to preview
    try:
        vs = get_vectorstore(job_id)  # retrieve the Chroma instance
    except KeyError:
        return jsonify({"error": f"No vectorstore found for job_id {job_id}"}), 404

    # Access the texts and metadata stored in Chroma
    # Chroma API: vs._collection.get(include=["documents","metadatas"]) returns dict
    preview_data = vs._collection.get(
        include=["documents", "metadatas", "embeddings"], 
        limit=N
    )

    # Include embedding dimension in response
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
    if job_id not in jobs or jobs[job_id]["status"] != "done":
        return "Document not ready or not found", 400

    # Determine if user submitted a question (GET query or POST JSON)
    question = ""
    if request.method == "POST":
        data = request.get_json()
        question = data.get("question", "").strip() if data else ""
    else:  # GET
        question = request.args.get("question", "").strip()

    # If no question, render the page
    if not question:
        return render_template("chat.html", job_id=job_id)

    # Process question and return JSON answer
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
