import requests
from elasticsearch import Elasticsearch, helpers

# === Config ===
API_URL = "https://api.domainsdb.info/v1/domains/search"
INDEX_NAME = "domains"

# === Init Elasticsearch/OpenSearch client ===
es = Elasticsearch("http://localhost:9200")

# === Call the API ===
response = requests.get(API_URL)
response.raise_for_status()  # Raise error if failed
data = response.json()

# === Choose the list to index ===
docs = data.get("domains", []) 

# === Stream into Elasticsearch/OpenSearch ===
actions = ({
    "_index": INDEX_NAME,
    "_source": doc
} for doc in docs)

helpers.bulk(es, actions)

print(f"✅ Successfully indexed {len(docs)} documents to `{INDEX_NAME}`")
