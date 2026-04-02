# Semantic Layer

A lightweight semantic layer built in Python that lets you query your data warehouse using natural language. Define metrics and entities in YAML, and ask questions in plain English — the system handles retrieval, SQL generation, and returns results through a clean chat interface.

Everything runs locally. No cloud APIs, no external dependencies, no ongoing costs.

## Demo

Ask questions like:
- "what is our total revenue by customer segment?"
- "how many orders did we get by status?"
- "show me revenue broken down by order status"

The system translates these into SQL, executes them against DuckDB, and returns results in a chat UI.

## Architecture
```
Natural language question
        ↓
RAG retrieval (nomic-embed-text + ChromaDB)
        ↓
LLM picks metric + dimensions (llama3.2:3b via Ollama)
        ↓
Query engine generates SQL (query.py)
        ↓
DuckDB executes query and returns results
        ↓
FastAPI + HTML chat UI displays results
```

## Project structure
```
semantic_layer/
├── metrics/                  # metric definitions (YAML)
│   ├── total_revenue.yml
│   └── order_count.yml
├── models/                   # entity and dimension definitions (YAML)
│   ├── orders.yml
│   └── customer.yml
├── semantic_layer/
│   ├── models.py             # dataclasses: Metric, Entity, Dimension, Join
│   ├── catalog.py            # loads and validates YAML definitions
│   ├── query.py              # SQL generation engine with join resolution
│   ├── embeddings.py         # vector embeddings and ChromaDB retrieval
│   ├── agent.py              # LLM agent that translates questions to queries
│   └── __init__.py           # clean Python API
├── static/
│   └── index.html            # chat UI
├── app.py                    # FastAPI server
├── setup_db.py               # loads TPC-H data into DuckDB
└── test_catalog.py           # end-to-end tests
```

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) for dependency management
- [Ollama](https://ollama.com) for local LLM inference
- 16GB RAM recommended

## Quickstart

**1. Clone and install dependencies**
```bash
git clone https://github.com/yourname/semantic-layer
cd semantic-layer
uv sync
```

**2. Install and start Ollama**

Download from [ollama.com](https://ollama.com), then pull the required models:
```bash
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

**3. Load TPC-H data into DuckDB**

Download the TPC-H `.tbl` files and update the `TBL_DIR` path in `setup_db.py`, then:
```bash
uv run python setup_db.py
```

**4. Start Ollama in one terminal tab**
```bash
ollama serve
```

**5. Start the API server in another terminal tab**
```bash
uv run uvicorn app:app --reload
```

**6. Open the chat UI**
```
http://localhost:8000
```

## Defining a metric
```yaml
# metrics/total_revenue.yml
name: total_revenue
label: Total revenue
type: simple
entity: orders
expression: SUM(o_totalprice)
dimensions_allowed:
  - order_status
  - order_date
  - customer_segment
```

## Defining an entity
```yaml
# models/orders.yml
entity: orders
table: orders
primary_key: o_orderkey

joins:
  - entity: customer
    join_key: o_custkey
    foreign_key: c_custkey
    type: left

dimensions:
  - name: order_status
    column: o_orderstatus
    type: string
  - name: order_date
    column: o_orderdate
    type: date
  - name: customer_segment
    column: c_mktsegment
    entity: customer      # signals a join is needed
    type: string
```

## Using the Python API directly
```python
from semantic_layer import SemanticLayer

sl = SemanticLayer(
    metrics_dir="metrics",
    models_dir="models",
    db="tpch.duckdb"
)

# see what's available
print(sl.available_metrics())
print(sl.available_dimensions("total_revenue"))

# run a query
sl.query(metric="total_revenue", dimensions=["customer_segment"])
```

## Using the CLI
```bash
# list metrics
uv run python -m semantic_layer metrics

# list dimensions for a metric
uv run python -m semantic_layer dimensions --metric total_revenue

# run a query
uv run python -m semantic_layer query --metric total_revenue --dimensions customer_segment
```

## Known limitations

- **No filtering** — WHERE clauses are not yet supported. Questions like "revenue where status = O" won't filter correctly.
- **No ordering or limits** — ORDER BY and LIMIT are not yet implemented.
- **No date ranges** — "last month" or "this quarter" are not resolved.
- **English only** — the LLM and embeddings are optimised for English queries.
- **Small model** — llama3.2:3b is fast and local but less capable than larger models. Complex or ambiguous questions may not resolve correctly.

## Roadmap

- [x] Phase 1 — YAML metric and entity definitions with validation
- [x] Phase 2 — SQL generation engine with automatic join resolution
- [x] Phase 3 — Python API and CLI
- [x] Phase 4 — vector embeddings and semantic retrieval (ChromaDB + nomic-embed-text)
- [x] Phase 5 — LLM agent translating natural language to queries (llama3.2:3b)
- [x] Phase 6 — FastAPI + HTML chat UI
- [ ] Phase 7 — filter and ordering support
- [ ] Phase 8 — additional TPC-H entities and metrics
- [ ] Phase 9 — knowledge graph enrichment layer

## Tech stack

| Component | Technology |
|---|---|
| Data warehouse | DuckDB |
| Metric definitions | YAML |
| Embeddings | nomic-embed-text via Ollama |
| Vector store | ChromaDB |
| LLM | llama3.2:3b via Ollama |
| API | FastAPI |
| Frontend | Vanilla HTML/CSS/JS |
| Package manager | uv |