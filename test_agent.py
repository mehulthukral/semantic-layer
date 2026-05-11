import sys
sys.path.insert(0, ".")

import duckdb
from semantic_layer.catalog import Catalog
from semantic_layer.embeddings import build_vector_store
from semantic_layer.graph import build_graph, add_synonym
from semantic_layer.agent import ask

catalog = Catalog(metrics_dir="metrics", models_dir="models")
collection = build_vector_store(catalog)
con = duckdb.connect("tpch.duckdb")

# build the knowledge graph
graph = build_graph(catalog, con)

# add some manual synonyms
add_synonym(graph, "orders.order_status.F", "fulfilled")
add_synonym(graph, "orders.order_status.O", "open")
add_synonym(graph, "orders.order_status.P", "pending")
add_synonym(graph, "orders.customer_segment.BUILDING", "construction")
add_synonym(graph, "orders.customer_segment.AUTOMOBILE", "automotive")

questions = [
    "what is our total revenue by customer segment?",
    "show me revenue where order status is F",
    "top 5 customer segments by total revenue",
    "how many open orders do we have by status?",
    "show me revenue from construction companies",
]

for q in questions:
    print(f"\nQuestion: {q}")
    result = ask(q, catalog, collection, con, graph)
    if result is not None:
        print(result)