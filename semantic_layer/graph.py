import networkx as nx
import duckdb
from .catalog import Catalog

# columns with more than this many distinct values won't have
# their values loaded into the graph
CARDINALITY_THRESHOLD = 50

def build_graph(catalog: Catalog, con: duckdb.DuckDBPyConnection) -> nx.DiGraph:
    g = nx.DiGraph()

    for entity in catalog.entities.values():
        # add entity node
        g.add_node(entity.entity, type="entity", table=entity.table)

        # add join relationships between entities
        for join in entity.joins:
            g.add_edge(
                entity.entity,
                join.entity,
                rel="joins",
                join_key=join.join_key,
                foreign_key=join.foreign_key,
            )

        # add dimension nodes and their values
        for dim in entity.dimensions:
            dim_node = f"{entity.entity}.{dim.name}"
            g.add_node(dim_node, type="dimension", column=dim.column, dtype=dim.type)
            g.add_edge(entity.entity, dim_node, rel="has_dimension")

            # load distinct values for low cardinality string dimensions
            if dim.type == "string":
                table = catalog.entities[dim.entity].table if dim.entity else entity.table
                try:
                    rows = con.execute(
                        f"SELECT DISTINCT {dim.column} FROM {table} "
                        f"WHERE {dim.column} IS NOT NULL "
                        f"LIMIT {CARDINALITY_THRESHOLD + 1}"
                    ).fetchall()
                    values = [r[0] for r in rows]

                    if len(values) <= CARDINALITY_THRESHOLD:
                        for val in values:
                            val_node = f"{dim_node}.{val}"
                            g.add_node(val_node, type="value", value=val)
                            g.add_edge(dim_node, val_node, rel="has_value")
                except Exception as e:
                    print(f"  Warning: could not load values for {dim.column}: {e}")

    # add metric nodes
    for metric in catalog.metrics.values():
        g.add_node(metric.name, type="metric", expression=metric.expression)
        g.add_edge(metric.entity, metric.name, rel="has_metric")

    return g

def add_synonym(g: nx.DiGraph, node: str, synonym: str):
    """manually add a synonym for a value or dimension"""
    if node in g.nodes:
        g.add_node(synonym, type="synonym")
        g.add_edge(synonym, node, rel="synonym_of")

def resolve_synonyms(g: nx.DiGraph, term: str) -> list[str]:
    """find canonical nodes that a term is a synonym of"""
    term_lower = term.lower()
    results = []

    # check direct synonym edges
    for node in g.nodes:
        if node.lower() == term_lower:
            for _, target, data in g.out_edges(node, data=True):
                if data.get("rel") == "synonym_of":
                    results.append(target)

    return results

def enrich_context(
    g: nx.DiGraph,
    question: str,
    retrieved_chunks: list[str]
) -> str:
    """
    Takes the retrieved chunks and enriches them with graph context —
    valid filter values for any dimensions mentioned.
    Returns an enriched context string to pass to the LLM.
    """
    context_lines = list(retrieved_chunks)
    question_lower = question.lower()

    # find dimension nodes whose name appears in the question
    for node, data in g.nodes(data=True):
        if data.get("type") != "dimension":
            continue

        dim_name = node.split(".")[-1]
        if dim_name.lower() not in question_lower:
            continue

        # get valid values for this dimension from the graph
        values = [
            g.nodes[target]["value"]
            for _, target, edge_data in g.out_edges(node, data=True)
            if edge_data.get("rel") == "has_value"
        ]

        if values:
            context_lines.append(
                f"Valid values for '{dim_name}': {', '.join(str(v) for v in values)}"
            )

        # check if question term maps to a synonym
        synonyms = resolve_synonyms(g, dim_name)
        if synonyms:
            context_lines.append(f"'{dim_name}' is also known as: {', '.join(synonyms)}")

    return "\n".join(context_lines)