import json
import ollama
from .catalog import Catalog
from .embeddings import build_vector_store, retrieve
from .query import query as run_query
import duckdb

SYSTEM_PROMPT = """
You are a data assistant that helps users query a semantic layer.

You will be given:
1. A user question
2. A list of relevant metrics and dimensions from the semantic layer

Your job is to respond with a JSON object containing:
- "metric": the name of the most relevant metric (exactly as shown)
- "dimensions": a list of dimension names to slice by (exactly as shown, can be empty)

Rules:
- Only use metrics and dimensions from the context provided
- Return ONLY valid JSON, no explanation, no markdown, no code blocks
- If you cannot answer from the available metrics, return {"error": "cannot answer"} - do not hallucinate
  an answer if you are unable to retrieve one from available metrics

Example response:
{"metric": "total_revenue", "dimensions": ["customer_segment"]}
"""

def ask(question: str, catalog: Catalog, collection, con: duckdb.DuckDBPyConnection):
    # step 1 - retrieve relevant context 
    context_chunks = retrieve(question, collection, n=4)
    context = "\n".join(context_chunks)

    # step 2 - build the prompt 
    user_prompt = f"""User question: {question}
                      Available metrics and dimensions: {context}
                      Respond with JSON only."""
    
    # step 3 - call llama model
    response = ollama.chat(
        model = "llama3.2:3b",
        messages = [
            {"role":"system", "content":SYSTEM_PROMPT},
            {"role":"user", "content":user_prompt}
        ]
    )

    raw = response["message"]["content"].strip()

    # step 4 - parse the JSON response 
    try: 
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        print(f"LLM could not answer: {parsed['error']}")
        return None
    
    if "error" in parsed:
        print(f"LLM could not answer: {parsed['error']}")
        return None
    
    metric = parsed.get("metric")
    dimensions = parsed.get("dimensions", [])

    print(f"  Metric:       {metric}")
    print(f"  Dimensions:   {dimensions}")

    # step 5 - run the query 
    try:
        sql = run_query(metric=metric, dimensions=dimensions, catalog=catalog)
        print(f"SQL: {sql}\n")
        return con.execute(sql).df()
    except ValueError as e:
        print(f"Query Error: {e}")
        return None 