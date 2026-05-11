import json
import ollama
from .catalog import Catalog
from .embeddings import build_vector_store, retrieve
from .query import query as run_query
import duckdb
from .graph import build_graph, enrich_context

SYSTEM_PROMPT = """You are a data assistant that helps users query a semantic layer.

You will be given:
1. A user question
2. A list of relevant metrics and dimensions from the semantic layer

Your job is to respond with a JSON object containing:
- "metric": the name of the most relevant metric (exactly as shown)
- "dimensions": a list of dimension names to slice by (exactly as shown, can be empty)
- "filters": a list of filter objects with "field" and "value" keys (can be empty list). The "field" value must be the semantic filter name (e.g. "order_status"), never a raw column name (e.g. never "o_orderstatus")
- "order_by": the metric name to order by, or null if not needed
- "order_dir": "asc" or "desc" (default "desc")
- "limit": an integer to limit rows, or null if not needed

Rules:
- Only use metrics and dimensions from the context provided
- Return ONLY valid JSON, no explanation, no markdown, no code blocks
- If you cannot answer from the available metrics, return {"error": "cannot answer"}
- When no filter is needed, use "filters": []
- When no sorting is needed, use "order_by": null
- When no row limit is needed, use "limit": null

Example with filters and sorting:
{
  "metric": "total_revenue",
  "dimensions": ["customer_segment"],
  "filters": [{"field": "order_status", "value": "F"}],
  "order_by": "total_revenue",
  "order_dir": "desc",
  "limit": 5
}

Example with no filters and no sorting:
{
  "metric": "total_revenue",
  "dimensions": ["order_status"],
  "filters": [],
  "order_by": null,
  "order_dir": "desc",
  "limit": null
}"""

def ask(question: str, catalog: Catalog, collection, con: duckdb.DuckDBPyConnection, graph=None):
    # step 1 — retrieve relevant context
    context_chunks = retrieve(question, collection, n=4)

    # step 2 — enrich with graph context if available
    if graph is not None:
        context = enrich_context(graph, question, context_chunks)
    else:
        context = "\n".join(context_chunks)

    # step 3 - build the prompt 
    user_prompt = f"""User question: {question}
                      Available metrics and dimensions: {context}
                      Respond with JSON only."""
    
    # step 4 - call llama model
    response = ollama.chat(
        model = "llama3.2:3b",
        messages = [
            {"role":"system", "content":SYSTEM_PROMPT},
            {"role":"user", "content":user_prompt}
        ]
    )

    raw = response["message"]["content"].strip()
    print(f"  Raw LLM response: {raw}")

    # strip markdown code fences that small models often add
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    # step 5 - parse the JSON response
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        print(f"LLM returned invalid JSON: {raw}")
        return None
    
    if "error" in parsed:
        print(f"LLM could not answer: {parsed['error']}")
        return None
    
    metric = parsed.get("metric")
    dimensions = parsed.get("dimensions") or []
    filters = [f for f in (parsed.get("filters") or [])
               if f.get("value") not in (None, "None", "null", "")]
    order_by = parsed.get("order_by") or None
    order_dir = parsed.get("order_dir") or "desc"
    limit = parsed.get("limit")

    print(f"  Metric:     {metric}")
    print(f"  Dimensions: {dimensions}")
    print(f"  Filters:    {filters}")
    print(f"  Order by:   {order_by} {order_dir}")
    print(f"  Limit:      {limit}")

    try:
        sql = run_query(
            metric=metric,
            dimensions=dimensions,
            catalog=catalog,
            filters=filters,
            order_by=order_by,
            order_dir=order_dir,
            limit=limit,
        )
    except ValueError as e:
        print(f"Query Error: {e}")
        return None

    print(f"  SQL:\n{sql}")
    return con.execute(sql).df()