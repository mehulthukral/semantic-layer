from .catalog import Catalog

def query(metric: str, dimensions: list[str], catalog: Catalog) -> str:
    # 1. look up the metric
    m = catalog.metrics.get(metric)
    if not m:
        raise ValueError(f"Unknown metric: '{metric}'. "
                         f"Available: {list(catalog.metrics.keys())}")

    # 2. look up the base entity
    entity = catalog.entities.get(m.entity)
    if not entity:
        raise ValueError(f"Unknown entity: '{m.entity}'")

    # 3. validate requested dimensions are allowed on this metric
    for dim_name in dimensions:
        if dim_name not in m.dimensions_allowed:
            raise ValueError(
                f"Dimension '{dim_name}' is not allowed on metric '{metric}'. "
                f"Allowed: {m.dimensions_allowed}"
            )

    # 4. resolve each dimension to its column, track joins needed
    dim_lookup = {d.name: d for d in entity.dimensions}
    join_lookup = {j.entity: j for j in entity.joins}

    select_cols = []
    group_cols = []
    joins_needed = {}

    for dim_name in dimensions:
        dim = dim_lookup.get(dim_name)
        if not dim:
            raise ValueError(
                f"Dimension '{dim_name}' not found on entity '{entity.entity}'"
            )

        if dim.entity:
            joined_entity = catalog.entities.get(dim.entity)
            if not joined_entity:
                raise ValueError(f"Unknown join entity: '{dim.entity}'")
            col = f"{joined_entity.table}.{dim.column}"
            joins_needed[dim.entity] = join_lookup[dim.entity]
        else:
            col = f"{entity.table}.{dim.column}"

        select_cols.append(f"{col} AS {dim_name}")
        group_cols.append(col)

    # 5. add the metric expression
    select_cols.append(f"{m.expression} AS {m.name}")

    # 6. assemble SQL
    select_clause = ",\n  ".join(select_cols)
    sql = f"SELECT\n  {select_clause}\nFROM {entity.table}"

    # 7. add joins
    for join in joins_needed.values():
        joined_entity = catalog.entities[join.entity]
        sql += (
            f"\n{join.type.upper()} JOIN {joined_entity.table}"
            f" ON {entity.table}.{join.join_key}"
            f" = {joined_entity.table}.{join.foreign_key}"
        )

    # 8. add group by
    if group_cols:
        sql += f"\nGROUP BY {', '.join(group_cols)}"

    return sql