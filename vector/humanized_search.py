import os
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from PyPDF2 import PdfReader
from ollama import chat
import uuid

# === CONFIGURATION === #
PDF_FILE = "C:/Users/satvi/OneDrive/Desktop/SearchIQ/data/Solutions Architect Associate.pdf"  # Put your PDF in same folder
COLLECTION_NAME = "aws_pdf_chunks"
PERSIST_DIR = "./chroma_aws_pdf"
CHUNK_SIZE = 500  # characters
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
OLLAMA_MODEL = "gemma:2b"

# === EMBEDDING FUNCTION === #
embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=EMBEDDING_MODEL
)

# === CONNECT TO CHROMA === #
client = chromadb.Client(Settings(persist_directory=PERSIST_DIR, anonymized_telemetry=False))

# === CHECK & LOAD / INGEST === #
try:
    collection = client.get_collection(name=COLLECTION_NAME, embedding_function=embedding_func)
    print(f"✅ Loaded existing collection: {COLLECTION_NAME}")
except:
    print("📄 Ingesting PDF...")
    collection = client.create_collection(name=COLLECTION_NAME, embedding_function=embedding_func)

    # 1. Read PDF
    reader = PdfReader(PDF_FILE)
    text = "\n".join([page.extract_text() or "" for page in reader.pages])

    # 2. Chunk text
    chunks = [text[i:i+CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)]

    # 3. Add to ChromaDB
    collection.add(
        documents=chunks,
        ids=[str(uuid.uuid4()) for _ in chunks],
        metadatas=[{"source": PDF_FILE} for _ in chunks]
    )

    print(f"✅ Ingested and saved {len(chunks)} chunks.")

# === SEARCH & HUMANIZE === #
def search_and_answer(question: str):
    print(f"\n🔍 Question: {question}")
    
    results = collection.query(query_texts=[question], n_results=3)
    context = "\n\n".join(results["documents"][0])

    print("\n🤖 Generating answer using Ollama...")
    response = chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": "You are an expert AWS assistant."},
            {"role": "user", "content": f"Answer the question based on this context:\n\n{context}\n\nQuestion: {question}"}
        ]
    )

    print("\n💬 Answer:\n")
    print(response["message"]["content"])
    print("\n" + "-"*50 + "\n")

# === MAIN LOOP === #
if __name__ == "__main__":
    while True:
        query = input("🔎 Ask about AWS services (or type 'exit'): ").strip()
        if query.lower() in ("exit", "quit"):
            break
        search_and_answer(query)
