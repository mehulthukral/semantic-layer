import sys
sys.path.insert(0, ".")

from semantic_layer import SemanticLayer

sl = SemanticLayer(
    metrics_dir="metrics",
    models_dir="models",
    db="tpch.duckdb"
)

# check what's available
print("Metrics:", sl.available_metrics())
print("Dimensions for total_revenue:", sl.available_dimensions("total_revenue"))

# run queries
print("\n--- total_revenue by order_status ---")
print(sl.query(metric="total_revenue", dimensions=["order_status"]))

print("\n--- total_revenue by customer_segment ---")
print(sl.query(metric="total_revenue", dimensions=["customer_segment"]))

print("\n--- order_count by order_status ---")
print(sl.query(metric="order_count", dimensions=["order_status"]))