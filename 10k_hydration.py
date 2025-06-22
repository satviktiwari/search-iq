import fitz
import camelot
import re
import os
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer

# === CONFIGURATION ===
pdf_path = "10-Q4-2024-As-Filed.pdf"
es_host = "http://localhost:9200"
es_index = "sec-filings"
embedding_dim = 384  # For all-MiniLM-L6-v2

# === LOAD EMBEDDING MODEL ===
model = SentenceTransformer('all-MiniLM-L6-v2')

# === CONNECT TO ELASTICSEARCH ===
es = Elasticsearch(es_host)

# === CREATE INDEX WITH VECTOR MAPPING IF NEEDED ===
if not es.indices.exists(index=es_index):
    es.indices.create(index=es_index, body={
        "mappings": {
            "properties": {
                "filename": {"type": "keyword"},
                "section_title": {"type": "text"},
                "section_content": {"type": "text"},
                "section_page": {"type": "integer"},
                "section_content_vector": {"type": "dense_vector", "dims": embedding_dim},
                "tables": {
                    "type": "nested",
                    "properties": {
                        "table_title": {"type": "text"},
                        "table_data": {"type": "object"},
                        "table_vector": {"type": "dense_vector", "dims": embedding_dim}
                    }
                }
            }
        }
    })

filename = os.path.basename(pdf_path)
doc = fitz.open(pdf_path)
page_texts = [page.get_text() for page in doc]
full_text = "\n".join(page_texts)

section_pattern = re.compile(
    r'(Item\s+\d+[A-Z]?(?:\.\d+)?\.?.*?)(?=\n\s*Item\s+\d+[A-Z]?(?:\.\d+)?\.?|$)',
    re.IGNORECASE | re.DOTALL
)

# Extract tables once for all pages (to avoid repeated extraction)
tables_stream = camelot.read_pdf(pdf_path, pages="all", flavor="stream")
tables_lattice = camelot.read_pdf(pdf_path, pages="all", flavor="lattice")
all_tables = list(tables_stream) + list(tables_lattice)

# Build a mapping from page number to tables
page_to_tables = {}
for table in all_tables:
    page_num = table.page
    table_title = " | ".join(table.data[0]) if table.data else "Extracted Table"
    table_str = "\n".join(["\t".join(row) for row in table.data])
    table_obj = {
        "table_title": table_title,
        "table_data": table.data,
        "table_str": table_str
    }
    page_to_tables.setdefault(page_num, []).append(table_obj)

# Sequentially process and upload each section
for match in section_pattern.finditer(full_text):
    section_text = match.group(0).strip()
    # Find which page this section starts on
    for i, page in enumerate(page_texts):
        if section_text[:20] in page:
            section_page = i + 1
            break
    else:
        section_page = None
    lines = section_text.splitlines()
    title = " ".join(lines[:2]).strip() if len(lines) > 1 and len(lines[0]) < 20 else lines[0]
    content = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""

    # Embed section content
    section_vector = model.encode(content or "", normalize_embeddings=True).tolist()

    # Get tables for this section's page and embed them
    tables_with_vectors = []
    for t in page_to_tables.get(section_page, []):
        table_vector = model.encode(t["table_str"] or "", normalize_embeddings=True).tolist()
        tables_with_vectors.append({
            "table_title": t["table_title"],
            "table_data": t["table_data"],
            "table_vector": table_vector
        })

    doc_body = {
        "filename": filename,
        "section_title": title,
        "section_content": content,
        "section_page": section_page,
        "section_content_vector": section_vector,
        "tables": tables_with_vectors
    }

    # Upload to Elasticsearch
    es.index(index=es_index, body=doc_body)
    print(f"Uploaded section: {title}")

print("All sections processed and uploaded sequentially.")