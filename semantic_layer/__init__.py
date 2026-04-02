import duckdb
from .catalog import Catalog
from .query import query as _query 

class SemanticLayer: 
    def __init__(self, metrics_dir: str, models_dir:str, db:str):
        self.catalog = Catalog(metrics_dir=metrics_dir, models_dir=models_dir)
        self.con = duckdb.connect(db)

    def query(self, metric: str, dimensions: list[str]):
        sql = _query(metric=metric, dimensions=dimensions, catalog=self.catalog)
        return self.con.execute(sql).df()
    
    def available_metrics(self) -> list[str]:
        return list(self.catalog.metrics.keys())
    
    def available_dimensions(self, metric: str) -> list[str]:
        m = self.catalog.metrics.get(metric)
        if not m:
            raise ValueError(f"Unknown metric: '{metric}'")
        return m.dimensions_allowed
    
