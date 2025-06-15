import os
import uuid
import streamlit as st
from PyPDF2 import PdfReader
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
from ollama import chat

# --- Configuration ---
ES_INDEX = "document_vectors"
CHUNK_SIZE = 500
EMBED_MODEL = "all-MiniLM-L6-v2"
OLLAMA_MODEL = "gemma:2b"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- Elasticsearch Client ---
es = Elasticsearch("http://localhost:9200")

# --- Create Index with Vector Mapping ---
def create_index():
    if not es.indices.exists(index=ES_INDEX):
        es.indices.create(index=ES_INDEX, body={
            "mappings": {
                "properties": {
                    "chunk": {"type": "text"},
                    "embedding": {
                        "type": "dense_vector",
                        "dims": 384,
                        "index": True,
                        "similarity": "cosine"
                    },
                    "source": {"type": "keyword"}
                }
            }
        })

# --- PDF Chunking ---
def extract_chunks(pdf_file):
    reader = PdfReader(pdf_file)
    full_text = "\n".join([page.extract_text() or "" for page in reader.pages])
    chunks = [full_text[i:i + CHUNK_SIZE] for i in range(0, len(full_text), CHUNK_SIZE)]
    return chunks

# --- Embed and Index ---
embedder = SentenceTransformer(EMBED_MODEL)

def ingest_pdf(file):
    chunks = extract_chunks(file)
    embeddings = embedder.encode(chunks).tolist()
    for i, chunk in enumerate(chunks):
        doc = {
            "chunk": chunk,
            "embedding": embeddings[i],
            "source": file.name
        }
        es.index(index=ES_INDEX, id=str(uuid.uuid4()), body=doc)
    return len(chunks)

# --- Semantic Search ---
def search(question, k=5):
    q_embed = embedder.encode([question])[0]
    query = {
        "size": k,
        "query": {
            "script_score": {
                "query": {"match_all": {}},
                "script": {
                    "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                    "params": {"query_vector": q_embed}
                }
            }
        }
    }
    res = es.search(index=ES_INDEX, body=query)
    return [hit["_source"]["chunk"] for hit in res["hits"]["hits"]]

# --- Answer with Ollama ---
def ask_ollama(question, context):
    context_text = "\n\n".join(context)
    prompt = f"""
Answer the question using the context below. Be concise.

Context:
{context_text}

Question: {question}
"""
    response = chat(model=OLLAMA_MODEL, messages=[
        {"role": "user", "content": prompt}
    ])
    return response['message']['content']

# --- Streamlit UI ---
st.set_page_config(page_title="Elastic SearchIQ", layout="centered")
st.title("📚 Ask Your PDF using Elasticsearch + Ollama")

uploaded_files = st.file_uploader("📤 Upload PDFs", type=["pdf"], accept_multiple_files=True)
if uploaded_files:
    create_index()
    if st.button("📥 Ingest PDFs"):
        for file in uploaded_files:
            num_chunks = ingest_pdf(file)
            st.success(f"Ingested {num_chunks} chunks from {file.name}")

st.markdown("---")
query = st.text_input("🔎 Ask a question about your PDFs:")
if query:
    with st.spinner("🤖 Thinking..."):
        top_chunks = search(query)
        answer = ask_ollama(query, top_chunks)
        st.markdown("### 💬 Answer")
        st.write(answer)
