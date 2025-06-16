import os
import re
import fitz  # PyMuPDF
from flask import Flask, request, jsonify, render_template, session
from werkzeug.utils import secure_filename
from elasticsearch import Elasticsearch, helpers
from sentence_transformers import SentenceTransformer
import logging
from datetime import datetime
import json

# === Config ===
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf"}
ES_HOST = "http://localhost:9200"
VECTOR_DIM = 384
MAX_SEARCH_HISTORY = 10

# === Logging ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Flask Setup ===
app = Flask(__name__, template_folder="templates")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.secret_key = os.urandom(24)  # Required for session
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# === Model & Elasticsearch ===
model = SentenceTransformer("all-MiniLM-L6-v2")
es = Elasticsearch(ES_HOST)

# === Utils ===
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def sanitize_index_name(filename):
    name = os.path.splitext(filename)[0].lower()
    name = re.sub(r'[^a-z0-9-]', '-', name)
    name = re.sub(r'-+', '-', name)
    name = name.strip('-')
    return name

def build_search_query(query_params):
    must_conditions = []
    filter_conditions = []
    
    # Text search with operators
    if query_params.get('query'):
        query = query_params['query']
        if ' AND ' in query:
            terms = query.split(' AND ')
            must_conditions.append({"multi_match": {"query": " ".join(terms), "fields": ["content", "title"]}})
        elif ' OR ' in query:
            terms = query.split(' OR ')
            should_conditions = [{"multi_match": {"query": term, "fields": ["content", "title"]}} for term in terms]
            must_conditions.append({"bool": {"should": should_conditions, "minimum_should_match": 1}})
        elif ' NOT ' in query:
            terms = query.split(' NOT ')
            must_conditions.append({"multi_match": {"query": terms[0], "fields": ["content", "title"]}})
            must_not_conditions = [{"multi_match": {"query": term, "fields": ["content", "title"]}} for term in terms[1:]]
            must_conditions.append({"bool": {"must_not": must_not_conditions}})
        else:
            must_conditions.append({"multi_match": {"query": query, "fields": ["content", "title"]}})
    
    # Date range filter
    if query_params.get('date_from') or query_params.get('date_to'):
        date_filter = {"range": {"upload_timestamp": {}}}
        if query_params.get('date_from'):
            date_filter["range"]["upload_timestamp"]["gte"] = query_params['date_from']
        if query_params.get('date_to'):
            date_filter["range"]["upload_timestamp"]["lte"] = query_params['date_to']
        filter_conditions.append(date_filter)
    
    # Document type filter
    if query_params.get('doc_type'):
        filter_conditions.append({"term": {"file_type": query_params['doc_type']}})
    
    # Section filter
    if query_params.get('section'):
        must_conditions.append({"match": {"section": query_params['section']}})
    
    # Build final query
    query = {
        "bool": {
            "must": must_conditions,
            "filter": filter_conditions
        }
    }
    
    return query

# === Routes ===
@app.route("/")
def index():
    return render_template("upload.html")

@app.route("/search")
def search():
    # Get search history from session
    search_history = session.get('search_history', [])
    return render_template("search.html", search_history=search_history)

@app.route("/save-search", methods=["POST"])
def save_search():
    search_query = request.json
    if not search_query:
        return jsonify({"error": "No search query provided"}), 400
    
    # Get existing search history
    search_history = session.get('search_history', [])
    
    # Add new search to history
    search_history.insert(0, {
        "query": search_query,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    # Keep only the last MAX_SEARCH_HISTORY searches
    search_history = search_history[:MAX_SEARCH_HISTORY]
    
    # Save back to session
    session['search_history'] = search_history
    
    return jsonify({"message": "Search saved successfully"})

@app.route("/semantic-search", methods=["POST"])
def semantic_search():
    query_params = request.form.to_dict()
    index = query_params.pop('index', None)
    
    if not index:
        return jsonify({"error": "Missing index"}), 400
    
    try:
        # Build the search query
        search_query = build_search_query(query_params)
        
        # Add vector search if there's a semantic query
        if query_params.get('semantic_query'):
            query_vector = model.encode(query_params['semantic_query']).tolist()
            search_query = {
                "bool": {
                    "must": [
                        search_query,
                        {
                            "script_score": {
                                "query": {"match_all": {}},
                                "script": {
                                    "source": "cosineSimilarity(params.query_vector, 'vector') + 1.0",
                                    "params": {"query_vector": query_vector}
                                }
                            }
                        }
                    ]
                }
            }
        
        response = es.search(
            index=index,
            body={
                "query": search_query,
                "size": 10,
                "sort": [{"_score": "desc"}]
            }
        )
        
        hits = [{
            "score": hit["_score"],
            "text": hit["_source"]["content"],
            "page": hit["_source"].get("page_number", "?"),
            "title": hit["_source"].get("title", ""),
            "author": hit["_source"].get("author", ""),
            "upload_date": hit["_source"].get("upload_timestamp", ""),
            "file_type": hit["_source"].get("file_type", ""),
            "section": hit["_source"].get("section", "")
        } for hit in response["hits"]["hits"]]
        
        # Save search to history
        if query_params.get('query'):
            save_search(query_params)
        
        return render_template("results.html", 
                             query=query_params.get('query', ''),
                             results=hits,
                             total_hits=response["hits"]["total"]["value"])
    
    except Exception as e:
        logger.error(f"Error during search: {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

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

    index_name = sanitize_index_name(filename)
    logger.info(f"Processing file: {filename} for index: {index_name}")

    try:
        file_size = os.path.getsize(file_path)
        upload_timestamp = datetime.utcnow().isoformat()

        doc = fitz.open(file_path)
        total_pages = doc.page_count
        metadata = doc.metadata or {}

        title = metadata.get("title", "")
        author = metadata.get("author", "")
        producer = metadata.get("producer", "")
        creation_date = metadata.get("creationDate", "")
        modification_date = metadata.get("modDate", "")

        if not es.indices.exists(index=index_name):
            logger.info(f"Creating new index: {index_name}")
            es.indices.create(index=index_name, body={
                "mappings": {
                    "properties": {
                        "content": {"type": "text"},
                        "vector": {"type": "dense_vector", "dims": VECTOR_DIM, "index": False},
                        "page_number": {"type": "integer"},
                        "file_name": {"type": "keyword"},
                        "file_size": {"type": "long"},
                        "upload_timestamp": {"type": "date"},
                        "total_pages": {"type": "integer"},
                        "title": {"type": "text"},
                        "author": {"type": "text"},
                        "producer": {"type": "text"},
                        "creation_date": {"type": "text"},
                        "modification_date": {"type": "text"},
                        "content_length": {"type": "integer"},
                        "has_images": {"type": "boolean"},
                        "page_width": {"type": "float"},
                        "page_height": {"type": "float"}
                    }
                }
            })

        actions = []
        for i, page in enumerate(doc):
            text = page.get_text()
            if text.strip():
                embedding = model.encode(text).tolist()
                content_length = len(text)
                has_images = bool(page.get_images())
                rect = page.rect

                actions.append({
                    "_index": index_name,
                    "_id": f"page-{i}",
                    "_source": {
                        "content": text,
                        "vector": embedding,
                        "page_number": i + 1,
                        "file_name": filename,
                        "file_size": file_size,
                        "upload_timestamp": upload_timestamp,
                        "total_pages": total_pages,
                        "title": title,
                        "author": author,
                        "producer": producer,
                        "creation_date": creation_date,
                        "modification_date": modification_date,
                        "content_length": content_length,
                        "has_images": has_images,
                        "page_width": float(rect.width),
                        "page_height": float(rect.height)
                    }
                })
                logger.info(f"Processed page {i+1}")

        doc.close()
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
        if os.path.exists(file_path):
            os.remove(file_path)

if __name__ == "__main__":
    app.run(debug=True)
