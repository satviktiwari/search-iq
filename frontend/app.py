import os
import re
import fitz  # PyMuPDF
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from elasticsearch import Elasticsearch, helpers
from sentence_transformers import SentenceTransformer
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# === Utility Functions ===
def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def sanitize_index_name(filename: str) -> str:
    """Convert filename to valid Elasticsearch index name."""
    # Remove file extension and convert to lowercase
    name = os.path.splitext(filename)[0].lower()
    # Replace invalid characters with hyphens
    name = re.sub(r'[^a-z0-9-]', '-', name)
    # Remove multiple consecutive hyphens
    name = re.sub(r'-+', '-', name)
    # Remove leading/trailing hyphens
    name = name.strip('-')
    return name

# === Routes ===
@app.route("/")
def index():
    return render_template("search.html")

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
    logger.info(f"Processing file: {filename} for index: {index_name}")

    try:
        # Create index with basic mapping
        if not es.indices.exists(index=index_name):
            logger.info(f"Creating new index: {index_name}")
            es.indices.create(index=index_name, body={
                "mappings": {
                    "properties": {
                        "content": {
                            "type": "text",
                            "analyzer": "standard"
                        },
                        "vector": {
                            "type": "dense_vector",
                            "dims": VECTOR_DIM,
                            "index": False
                        },
                        "page_number": {
                            "type": "integer"
                        }
                    }
                }
            })

        # Process PDF
        doc = fitz.open(file_path)
        actions = []
        
        for i, page in enumerate(doc):
            text = page.get_text()
            if text.strip():
                embedding = model.encode(text).tolist()
                actions.append({
                    "_index": index_name,
                    "_id": f"page-{i}",
                    "_source": {
                        "content": text,
                        "vector": embedding,
                        "page_number": i + 1
                    }
                })
                logger.info(f"Processed page {i+1}")

        doc.close()

        # Bulk index
        success, failed = helpers.bulk(es, actions, stats_only=True)
        logger.info(f"Indexed {success} pages, {failed} failed")
        return jsonify({
            "message": f"✅ Successfully indexed {success} pages to '{index_name}'",
            "failed": failed,
            "index": index_name
        })

    except Exception as e:
        logger.error(f"Error during hydration: {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    finally:
        # Clean up the uploaded file
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass

@app.route("/semantic-search", methods=["POST"])
def semantic_search():
    query = request.form.get("query")
    index = request.form.get("index")

    if not query or not index:
        return jsonify({"error": "Missing query or index"}), 400

    try:
        # Encode query
        query_vector = model.encode(query).tolist()

        # Search
        response = es.search(
            index=index,
            body={
                "query": {
                    "script_score": {
                        "query": {"match_all": {}},
                        "script": {
                            "source": "cosineSimilarity(params.query_vector, 'vector') + 1.0",
                            "params": {"query_vector": query_vector}
                        }
                    }
                },
                "size": 10
            }
        )

        # Format results
        hits = []
        for hit in response["hits"]["hits"]:
            hits.append({
                "score": hit["_score"],
                "text": hit["_source"]["content"],
                "page": hit["_source"]["page_number"]
            })

        return render_template("results.html", query=query, results=hits)

    except Exception as e:
        logger.error(f"Error during search: {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
