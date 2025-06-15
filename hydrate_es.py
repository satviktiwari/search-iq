# hydrate_pdf_to_elasticsearch.py

import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer
from elasticsearch import Elasticsearch, helpers

INDEX_NAME = "aws-overview"
PDF_PATH = "aws-overview.pdf"
ES_HOST = "http://localhost:9200"
VECTOR_DIM = 384

# Connect to Elasticsearch
es = Elasticsearch(ES_HOST)

# Create index if not exists
if not es.indices.exists(index=INDEX_NAME):
    mapping = {
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
    }
    es.indices.create(index=INDEX_NAME, body=mapping)

# Extract text from PDF
doc = fitz.open(PDF_PATH)
pages = [page.get_text() for page in doc]
doc.close()

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Prepare documents
docs = []
for i, text in enumerate(pages):
    if text.strip():
        embedding = model.encode(text).tolist()
        docs.append({
            "_index": INDEX_NAME,
            "_id": f"page-{i}",
            "_source": {
                "content": text,
                "vector": embedding
            }
        })

# Bulk index
helpers.bulk(es, docs)
print(f"✅ Indexed {len(docs)} pages from {PDF_PATH} into '{INDEX_NAME}'.")
