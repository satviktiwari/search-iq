# semantic_search.py

from sentence_transformers import SentenceTransformer
from elasticsearch import Elasticsearch

INDEX_NAME = "aws-overview"
ES_HOST = "http://localhost:9200"

# Connect to Elasticsearch
es = Elasticsearch(ES_HOST)

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Get query input from user
query = input("Enter your semantic query: ")
query_vector = model.encode(query).tolist()

# Perform semantic search
response = es.search(
    index=INDEX_NAME,
    size=3,
    body={
        "query": {
            "script_score": {
                "query": {"match_all": {}},
                "script": {
                    "source": "cosineSimilarity(params.query_vector, 'vector') + 1.0",
                    "params": {"query_vector": query_vector}
                }
            }
        }
    }
)

# Display results
print("\n🔍 Top Matches:")
for hit in response["hits"]["hits"]:
    print(f"\nScore: {hit['_score']:.4f}")
    print(hit["_source"]["content"][:500], "...")
