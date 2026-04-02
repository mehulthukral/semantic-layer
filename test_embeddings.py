import sys
sys.path.insert(0, ".")

from semantic_layer.catalog import Catalog
from semantic_layer.embeddings import build_vector_store, retrieve

catalog = Catalog(metrics_dir="metrics", models_dir="models")
collection = build_vector_store(catalog)

questions = [
    "what was our total revenue last month?",
    "how many orders did we get by status?",
    "show me revenue broken down by customer type",
]

for q in questions:
    print(f"\nQuestion: {q}")
    results = retrieve(q, collection, n=2)
    for r in results:
        print(f"  -> {r}")