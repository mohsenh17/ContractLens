import uuid
import os
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

from parser import parse_pdf
from vectorstore import build_vectorstore
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

    jobs[job_id] = {"status": "parsing", "result": None, "error": None}

    # we should migrate to celery and redis (see if time permits)
    try:
        # Step 1: Parse PDF
        jobs[job_id]["status"] = "parsing"
        pages = parse_pdf(pdf_path)

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

if __name__ == "__main__":
    app.run(debug=True, port=5000)
