from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Join:
    entity: str
    join_key: str       # column on the base table
    foreign_key: str    # column on the joined table
    type: str = "left"

@dataclass
class Dimension:
    name: str
    column: str
    type: str
    entity: Optional[str] = None  # None = lives on base table

@dataclass
class Filter:
    name: str
    column: str
    type: str
    entity: Optional[str] = None

@dataclass
class Entity:
    entity: str
    table: str
    primary_key: str
    dimensions: list[Dimension] = field(default_factory=list)
    joins: list[Join] = field(default_factory=list)
    filters: list[Filter] = field(default_factory=list)

@dataclass
class Metric:
    name: str
    label: str
    entity: str
    expression: str
    type: str = "simple"
    dimensions_allowed: list[str] = field(default_factory=list)