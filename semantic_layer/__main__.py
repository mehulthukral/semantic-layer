import argparse
import sys
sys.path.insert(0, ".")

from semantic_layer import SemanticLayer

def main():
    parser = argparse.ArgumentParser(description="Semantic Layer CLI")
    subparsers = parser.add_subparsers(dest="command")

    # query command
    query_parser = subparsers.add_parser("query", help="Run a metric query")
    query_parser.add_argument("--metric", required=True, help="Metric name")
    query_parser.add_argument("--dimensions", nargs="+", default=[], help="Dimensions to slice by")

    # list command
    subparsers.add_parser("metrics", help="List available metrics")

    # dimensions command
    dims_parser = subparsers.add_parser("dimensions", help="List dimensions for a metric")
    dims_parser.add_argument("--metric", required=True, help="Metric name")

    args = parser.parse_args()

    sl = SemanticLayer(
        metrics_dir="metrics",
        models_dir="models",
        db="tpch.duckdb"
    )

    if args.command == "query":
        result = sl.query(metric=args.metric, dimensions=args.dimensions)
        print(result.to_string(index=False))

    elif args.command == "metrics":
        print("Available metrics:")
        for m in sl.available_metrics():
            print(f"  - {m}")

    elif args.command == "dimensions":
        print(f"Dimensions for '{args.metric}':")
        for d in sl.available_dimensions(args.metric):
            print(f"  - {d}")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()