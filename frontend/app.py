import os
import re
import fitz  # PyMuPDF
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from elasticsearch import Elasticsearch, helpers
from sentence_transformers import SentenceTransformer
from transformers import pipeline
from typing import List, Dict

# === Config ===
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf"}
ES_HOST = "http://localhost:9200"
VECTOR_DIM = 384

# === Flask Setup ===
app = Flask(__name__, template_folder="templates")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# === Model & Elasticsearch ===
model = SentenceTransformer("all-MiniLM-L6-v2")
es = Elasticsearch(ES_HOST)
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")


# === Utility Functions ===
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def sanitize_index_name(name):
    name = name.lower()
    name = re.sub(r"[^a-z0-9_-]", "-", name)
    name = re.sub(r"-+", "-", name).strip("-")
    return name[:255]


def generate_summary(texts: List[str], max_length: int = 250) -> str:
    """Generate a summary from multiple text chunks."""
    # Combine all texts with proper spacing
    combined_text = " ".join(texts)
    
    # If text is too long, truncate it (BART has a max input length)
    if len(combined_text) > 1024:
        combined_text = combined_text[:1024]
    
    # Generate summary
    summary = summarizer(combined_text, max_length=max_length, min_length=30, do_sample=False)
    return summary[0]['summary_text']


# === Routes ===

@app.route("/")
def home():
    return render_template("upload.html")


@app.route("/search")
def search():
    return render_template("search.html")


@app.route("/hydrate", methods=["POST"])
def hydrate():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]

    if not file or not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)

    index_name = sanitize_index_name(os.path.splitext(filename)[0])

    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name, body={
            "mappings": {
                "properties": {
                    "content": {"type": "text"},
                    "vector": {
                        "type": "dense_vector",
                        "dims": VECTOR_DIM,
                        "index": False
                    }
                }
            }
        })

    doc = fitz.open(file_path)
    pages = [page.get_text() for page in doc]
    doc.close()

    actions = []
    for i, text in enumerate(pages):
        if text.strip():
            embedding = model.encode(text).tolist()
            actions.append({
                "_index": index_name,
                "_id": f"page-{i}",
                "_source": {
                    "content": text,
                    "vector": embedding
                }
            })

    helpers.bulk(es, actions)

    return jsonify({"message": f"✅ Indexed {len(actions)} pages to '{index_name}'", "index": index_name})


@app.route("/semantic-search", methods=["POST"])
def semantic_search():
    query = request.form.get("query")
    index = request.form.get("index")

    if not query or not index:
        return jsonify({"error": "Missing query or index"}), 400

    query_vector = model.encode(query).tolist()

    response = es.search(index=index, size=5, body={
        "query": {
            "script_score": {
                "query": {"match_all": {}},
                "script": {
                    "source": "cosineSimilarity(params.query_vector, 'vector') + 1.0",
                    "params": {"query_vector": query_vector}
                }
            }
        }
    })

    hits = [
        {
            "score": round(hit["_score"], 4),
            "text": hit["_source"]["content"][:500]
        }
        for hit in response["hits"]["hits"]
    ]

    # Generate summary from all hits
    if hits:
        summary = generate_summary([hit["text"] for hit in hits])
    else:
        summary = "No relevant information found."

    return render_template("results.html", 
                         query=query, 
                         index=index, 
                         results=hits,
                         summary=summary)


if __name__ == "__main__":
    app.run(debug=True)
