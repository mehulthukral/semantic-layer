import duckdb
import os

# update this to wherever your .tbl files are
TBL_DIR = "/Users/mehulthukral/Desktop/Projects/Project - Semantic Layer/TPC-H Dataset/"

con = duckdb.connect("tpch.duckdb")  # creates a persistent file

# TPC-H tables and their column definitions
tables = {
    "region": ["r_regionkey INTEGER", "r_name VARCHAR", "r_comment VARCHAR"],
    "nation": ["n_nationkey INTEGER", "n_name VARCHAR", "n_regionkey INTEGER", "n_comment VARCHAR"],
    "customer": [
        "c_custkey INTEGER", "c_name VARCHAR", "c_address VARCHAR",
        "c_nationkey INTEGER", "c_phone VARCHAR", "c_acctbal DOUBLE",
        "c_mktsegment VARCHAR", "c_comment VARCHAR"
    ],
    "orders": [
        "o_orderkey INTEGER", "o_custkey INTEGER", "o_orderstatus VARCHAR",
        "o_totalprice DOUBLE", "o_orderdate DATE", "o_orderpriority VARCHAR",
        "o_clerk VARCHAR", "o_shippriority INTEGER", "o_comment VARCHAR"
    ],
    "lineitem": [
        "l_orderkey INTEGER", "l_partkey INTEGER", "l_suppkey INTEGER",
        "l_linenumber INTEGER", "l_quantity DOUBLE", "l_extendedprice DOUBLE",
        "l_discount DOUBLE", "l_tax DOUBLE", "l_returnflag VARCHAR",
        "l_linestatus VARCHAR", "l_shipdate DATE", "l_commitdate DATE",
        "l_receiptdate DATE", "l_shipinstruct VARCHAR", "l_shipmode VARCHAR",
        "l_comment VARCHAR"
    ],
    "supplier": [
        "s_suppkey INTEGER", "s_name VARCHAR", "s_address VARCHAR",
        "s_nationkey INTEGER", "s_phone VARCHAR", "s_acctbal DOUBLE",
        "s_comment VARCHAR"
    ],
    "part": [
        "p_partkey INTEGER", "p_name VARCHAR", "p_mfgr VARCHAR",
        "p_brand VARCHAR", "p_type VARCHAR", "p_size INTEGER",
        "p_container VARCHAR", "p_retailprice DOUBLE", "p_comment VARCHAR"
    ],
    "partsupp": [
        "ps_partkey INTEGER", "ps_suppkey INTEGER", "ps_availqty INTEGER",
        "ps_supplycost DOUBLE", "ps_comment VARCHAR"
    ],
}

for table, col_defs in tables.items():
    tbl_file = os.path.join(TBL_DIR, f"{table}.tbl")
    if not os.path.exists(tbl_file):
        print(f"Skipping {table} — file not found at {tbl_file}")
        continue

    # build the columns dict as a proper Python dict string
    cols_dict = "{" + ", ".join(f"'{c.split()[0]}': '{c.split()[1]}'" for c in col_defs) + "}"

    print(f"Loading {table}...")
    con.execute(f"DROP TABLE IF EXISTS {table}")
    con.execute(f"""
        CREATE TABLE {table} AS
        SELECT * FROM read_csv(
            '{tbl_file}',
            delim='|',
            header=false,
            columns={cols_dict},
            ignore_errors=true
        )
    """)
    count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"  {table}: {count:,} rows")

print("\nDone. Tables loaded:")
print(con.execute("SHOW TABLES").fetchall())
con.close()

