import sys
sys.path.insert(0, ".")

import duckdb
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from semantic_layer.catalog import Catalog
from semantic_layer.embeddings import build_vector_store
from semantic_layer.agent import ask

app = FastAPI()

# initialise everything once at startup
catalog = Catalog(metrics_dir="metrics", models_dir="models")
collection = build_vector_store(catalog)
con = duckdb.connect("tpch.duckdb")

class QuestionRequest(BaseModel):
    question: str

@app.get("/")
def root():
    return FileResponse("static/index.html")

@app.get("/metrics")
def list_metrics():
    return {"metrics": list(catalog.metrics.keys())}

@app.post("/query")
def query(request: QuestionRequest):
    result = ask(request.question, catalog, collection, con)
    if result is None:
        return {"error": "Could not answer the question from available metrics"}
    return {
        "question": request.question,
        "data": result.to_dict(orient="records"),
        "columns": list(result.columns),
    }

app.mount("/static", StaticFiles(directory="static"), name="static")