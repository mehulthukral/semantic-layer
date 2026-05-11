from .catalog import Catalog

def query(  metric: str,
            dimensions: list[str],
            catalog: Catalog,
            filters: list[dict] | None = None,
            order_by: str | None = None,
            order_dir: str = "desc",
            limit: int | None = None,) -> str:
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

    # 6. pre-process filters to collect any additional joins needed
    where_clauses = []
    if filters:
        filter_lookup = {f.name: f for f in entity.filters}
        for f in filters:
            field = filter_lookup.get(f["field"])
            if not field:
                raise ValueError(f"Unknown filter field: '{f['field']}'")
            if field.entity:
                filter_entity = catalog.entities.get(field.entity)
                if not filter_entity:
                    raise ValueError(f"Unknown filter entity: '{field.entity}'")
                col = f"{filter_entity.table}.{field.column}"
                joins_needed[field.entity] = join_lookup[field.entity]
            else:
                col = f"{entity.table}.{field.column}"
            value = f["value"]
            if field.type == "string":
                where_clauses.append(f"{col} = '{value}'")
            elif field.type == "date":
                where_clauses.append(f"{col} = '{value}'")
            else:
                where_clauses.append(f"{col} = {value}")

    # 7. assemble SQL
    select_clause = ",\n  ".join(select_cols)
    sql = f"SELECT\n  {select_clause}\nFROM {entity.table}"

    # 8. add joins (now includes any joins required by filters)
    for join in joins_needed.values():
        joined_entity = catalog.entities[join.entity]
        sql += (
            f"\n{join.type.upper()} JOIN {joined_entity.table}"
            f" ON {entity.table}.{join.join_key}"
            f" = {joined_entity.table}.{join.foreign_key}"
        )

    if where_clauses:
        sql += f"\nWHERE {' AND '.join(where_clauses)}"

    # 8. add group by
    if group_cols:
        sql += f"\nGROUP BY {', '.join(group_cols)}"

    if order_by:
        direction = (order_dir or "desc").upper()
        sql += f"\nORDER BY {order_by} {direction}"

    # add LIMIT
    if limit:
        sql += f"\nLIMIT {limit}"

    return sql