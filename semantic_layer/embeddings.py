import ollama
import chromadb
from .catalog import Catalog

def embed_texts(texts: list[str]) -> list[list[float]]:
    embeddings = []
    for text in texts:
        response = ollama.embeddings(
            model="nomic-embed-text",
            prompt=text
        )
        embeddings.append(response["embedding"])
    return embeddings

def build_metric_chunks(catalog: Catalog) -> list[dict]:

    """
    This function loops through every metric in the catalog and converts it into a plain english 
    sentence. For total_revenue it will produce something like: 
    Metric: total_revenue. Label: Total revenue. 
    Calculates SUM(o_totalprice) on the orders table. 
    Can be sliced by: order_status, order_date, customer_segment.

    This is what gets embedded - natural language is much better for semantic search than raw YAML
    """

    chunks = []
    for metric in catalog.metrics.values():
        dims = ", ".join(metric.dimensions_allowed)
        text = (
            f"Metric: {metric.name}. "
            f"Label: {metric.label}. "
            f"Calculates {metric.expression} on the {metric.entity} table. "
            f"Can be sliced by: {dims}."
        )
        chunks.append({"id": metric.name, "text": text})
    return chunks

def build_dimension_chunks(catalog: Catalog) -> list[dict]:
    """
    Same idea like metrics but for dimensions. Each dimension becomes a sentence like:
    Dimension: customer_segment. Column: c_mktsegment on the customer table. Type: string.
    """
    chunks = []
    for entity in catalog.entities.values():
        for dim in entity.dimensions:
            text = (
                f"Dimension: {dim.name}. "
                f"Column: {dim.column} on the "
                f"{dim.entity or entity.entity} table. "
                f"Type: {dim.type}."
            )
            chunks.append({
                "id": f"{entity.entity}__{dim.name}",
                "text": text
            })
    return chunks 

def build_filter_chunks(catalog: Catalog) -> list[dict]:
    chunks = []
    for entity in catalog.entities.values():
        for f in entity.filters:
            text = (
                f"Filter name: {f.name}. "
                f"Use field='{f.name}' to filter on {f.column} ({f.type}) "
                f"on the {entity.entity} table."
            )
            chunks.append({"id": f"filter__{entity.entity}__{f.name}", "text": text})
    return chunks

def build_vector_store(catalog: Catalog) -> chromadb.Collection:

    """
    This function embeds everything and loads it into a ChromaDB

    This is the setup step you only run once. It takes all your metric and dimension chunks and embeds
    them all, and stores them in a ChromaDB collection called "semantic_layer". After this, ChromaDB holds
    both the original text and its vector for every metric and dimension that have been defined.
    """

    chroma = chromadb.Client()
    collection = chroma.get_or_create_collection("semantic_layer")

    metric_chunks = build_metric_chunks(catalog)
    dim_chunks = build_dimension_chunks(catalog)
    filter_chunks = build_filter_chunks(catalog)
    all_chunks = metric_chunks + dim_chunks + filter_chunks

    texts = [c["text"] for c in all_chunks]
    ids = [c["id"] for c in all_chunks]
    embeddings = embed_texts(texts)

    collection.add(
        documents=texts,
        embeddings=embeddings,
        ids=ids
    )
    return collection

def retrieve(question: str, collection: chromadb.Collection, n: int = 3) -> list[str]:
    """
    This is what runs at query time. When a user asks "show me revenue by customer type", it:

    1. Embeds the question into a vector using the same `nomic-embed-text` model
    2. Asks ChromaDB "which stored vectors are closest to this one?"
    3. Returns the top `n` matching chunks — which will be the most semantically relevant 
       metrics and dimensions

    The key insight: "customer type" and "customer_segment" will have similar vectors even though 
    the words are different, so the retriever finds the right dimension anyway.
    """

    embedding = embed_texts([question])[0]
    results = collection.query(
        query_embeddings=[embedding],
        n_results=n
    )
    return results["documents"][0]

