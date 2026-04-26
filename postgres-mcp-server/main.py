# MCP mental model:
# @mcp.tool() → defines tools (what AI can call)
# mcp.run() → activates tools (starts the server)
# main() → organizes startup

from typing import List, Dict
import os
import psycopg2
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initializes your MCP server instance. It's used to register your tools.
mcp = FastMCP("postgres-server")

# Database connection configuration from environment variables
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "practice_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "password123"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
}


# EXECUTE_SQL TOOL -takes a SQL query as input and returns output rows as dictionaries (mapping column names to values)
@mcp.tool()
async def execute_sql(sql: str) -> List[Dict]:
    """Execute a read-only SQL query and return the rows as a list of dictionaries (column_name → value)."""
    # Safety guard: allow only SELECT queries
    cleaned_sql = sql.strip().lower()

    if not cleaned_sql.startswith("select"):
        raise ValueError("Only read-only SELECT queries are allowed.")

    blocked_keywords = ["insert", "update", "delete", "drop", "alter", "truncate", "create"]

    if any(keyword in cleaned_sql for keyword in blocked_keywords):
        raise ValueError("Query contains a blocked SQL keyword.")    
    
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            columns = [desc[0] for desc in cur.description]
            rows = [dict(zip(columns, row)) for row in cur.fetchall()]
    return rows

#LIST_TABLES TOOL - takes no inputs and returns the list of table names available in the current database
@mcp.tool()
async def list_tables() -> List[str]:
    """Return the list of table names available in the current database."""
    sql = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """

    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = [r[0] for r in cur.fetchall()]
    return rows



#GET_SCHEMA TOOL - takes a table name as input and returns the column names and types for that table
@mcp.tool() 
async def get_schema(table: str) -> List[Dict]:
    """Return column names and types for a given table."""
    sql = """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = %s
    """
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (table,))
            rows = [{"column": r[0], "type": r[1]} for r in cur.fetchall()]
    return rows

def main():
    # Run MCP server using stdio transport for AI assistant integration
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
