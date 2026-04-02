import sys
sys.path.insert(0, ".")

import duckdb
from semantic_layer.catalog import Catalog
from semantic_layer.embeddings import build_vector_store
from semantic_layer.agent import ask

catalog = Catalog(metrics_dir="metrics", models_dir="models")
collection = build_vector_store(catalog)
con = duckdb.connect("tpch.duckdb")

questions = [
    "what was our total revenue?",
    "how many orders did we get by status?",
    "show me revenue broken down by customer type",
    "what is our order count by order date?",
]

for q in questions:
    print(f"\nQuestion: {q}")
    result = ask(q, catalog, collection, con)
    if result is not None:
        print(result)