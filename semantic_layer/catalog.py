import yaml
from pathlib import Path
from .models import Metric, Entity, Dimension, Join

class Catalog:
    def __init__(self, metrics_dir: str, models_dir: str):
        self.metrics: dict[str, Metric] = {}
        self.entities: dict[str, Entity] = {}
        self._load_entities(models_dir)
        self._load_metrics(metrics_dir)
        self.validate()

    def _load_entities(self, path: str):
        for f in Path(path).glob("*.yml"):
            raw = yaml.safe_load(f.read_text())
            dims = [Dimension(**d) for d in raw.get("dimensions", [])]
            joins = [Join(**j) for j in raw.get("joins", [])]
            entity = Entity(
                entity=raw["entity"],
                table=raw["table"],
                primary_key=raw["primary_key"],
                dimensions=dims,
                joins=joins,
            )
            self.entities[entity.entity] = entity

    def _load_metrics(self, path: str):
        for f in Path(path).glob("*.yml"):
            raw = yaml.safe_load(f.read_text())
            metric = Metric(**raw)
            self.metrics[metric.name] = metric

    def validate(self):
        errors = []
        for metric in self.metrics.values():
            if metric.entity not in self.entities:
                errors.append(
                    f"Metric '{metric.name}' references unknown entity '{metric.entity}'"
                )
                continue
            entity = self.entities[metric.entity]
            dim_names = {d.name for d in entity.dimensions}
            for dim in metric.dimensions_allowed:
                if dim not in dim_names:
                    errors.append(
                        f"Metric '{metric.name}' allows dimension '{dim}' "
                        f"which doesn't exist on entity '{metric.entity}'"
                    )
        if errors:
            raise ValueError("Catalog validation failed:\n" + "\n".join(errors))