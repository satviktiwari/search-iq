import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
import PyPDF2
import os
import textwrap

# Step 1: Extract text from PDF
def extract_text_from_pdf(pdf_path):
    reader = PyPDF2.PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

# Step 2: Split text into chunks
def split_text(text, chunk_size=300):
    return textwrap.wrap(text, width=chunk_size)

# Step 3: Setup ChromaDB
client = chromadb.Client(Settings(persist_directory="./chroma_aws_pdf", anonymized_telemetry=False))

# Optional: Delete old collection if it exists
collection_name = "aws_pdf_chunks"
for col in client.list_collections():
    if col.name == collection_name:
        client.delete_collection(collection_name)

# Step 4: Create collection with sentence-transformer embedding
embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)
collection = client.create_collection(name=collection_name, embedding_function=embedding_func)

# Step 5: Process your PDF
pdf_path = "C:/Users/satvi/OneDrive/Desktop/SearchIQ/data/Solutions Architect Associate.pdf"  # Change to your PDF path
full_text = extract_text_from_pdf(pdf_path)
chunks = split_text(full_text, chunk_size=300)

# Step 6: Store in Chroma
ids = [f"chunk_{i}" for i in range(len(chunks))]
metadatas = [{"source": "Solutions Architect Associate.pdf", "chunk_id": i} for i in range(len(chunks))]
collection.add(documents=chunks, metadatas=metadatas, ids=ids)

print(f"✅ Stored {len(chunks)} chunks from the PDF.")

# Step 7: Semantic search
query = input("🔍 Ask something about AWS services: ")
results = collection.query(query_texts=[query], n_results=3)

print("\n🔎 Top results:")
for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
    print(f"\n📄 Chunk #{meta['chunk_id']}\n{doc[:500]}...")
