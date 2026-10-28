"""Execute read-only PostgreSQL queries with a hard 500-row cap.

Usage:
    python "<SKILL_PATH>/scripts/query_postgresql.py" "SELECT * FROM public.your_table"
    python "<SKILL_PATH>/scripts/query_postgresql.py" --file queries.sql --output results/

Requires exported PG_HOST, PG_PORT (optional, default 5432), PG_DATABASE,
PG_USER, and PG_PASSWORD. Pass --env-file explicitly when loading them from a file.

Packages: psycopg2-binary, python-dotenv, pandas
"""

import argparse
import os
import re

import pandas as pd
import psycopg2
from dotenv import load_dotenv

MAX_ROWS = 500
FORBIDDEN_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|MERGE|UPSERT|CREATE|ALTER|DROP|TRUNCATE|"
    r"REINDEX|GRANT|REVOKE|COPY|CALL|DO|EXECUTE|PREPARE|DEALLOCATE|"
    r"VACUUM|ANALYZE|CLUSTER|REFRESH|COMMENT|SECURITY|LOCK|SET|RESET|"
    r"COMMIT|ROLLBACK|SAVEPOINT|RELEASE|BEGIN|START)\b",
    re.IGNORECASE,
)


def sanitize_sql(query: str) -> str:
    """Replace comments, quoted identifiers, and literals while preserving SQL shape."""
    output = []
    index = 0
    while index < len(query):
        char = query[index]
        next_char = query[index + 1] if index + 1 < len(query) else ""

        if char == "-" and next_char == "-":
            output.extend((" ", " "))
            index += 2
            while index < len(query) and query[index] != "\n":
                output.append(" ")
                index += 1
            continue

        if char == "/" and next_char == "*":
            output.extend((" ", " "))
            index += 2
            depth = 1
            while index < len(query) and depth:
                if query[index:index + 2] == "/*":
                    output.extend((" ", " "))
                    index += 2
                    depth += 1
                elif query[index:index + 2] == "*/":
                    output.extend((" ", " "))
                    index += 2
                    depth -= 1
                else:
                    output.append("\n" if query[index] == "\n" else " ")
                    index += 1
            if depth:
                raise ValueError("Unterminated SQL block comment")
            continue

        if char == "$":
            tag_match = re.match(r"\$[A-Za-z_][A-Za-z0-9_]*\$|\$\$", query[index:])
            if tag_match:
                tag = tag_match.group(0)
                end = query.find(tag, index + len(tag))
                if end < 0:
                    raise ValueError("Unterminated PostgreSQL dollar-quoted string")
                segment = query[index:end + len(tag)]
                output.extend("\n" if value == "\n" else " " for value in segment)
                index = end + len(tag)
                continue

        if char in ("'", '"'):
            quote = char
            output.append(" ")
            index += 1
            closed = False
            while index < len(query):
                if query[index] == quote:
                    if index + 1 < len(query) and query[index + 1] == quote:
                        output.extend((" ", " "))
                        index += 2
                        continue
                    output.append(" ")
                    index += 1
                    closed = True
                    break
                output.append("\n" if query[index] == "\n" else " ")
                index += 1
            if not closed:
                raise ValueError("Unterminated SQL quoted value")
            continue

        output.append(char)
        index += 1

    return "".join(output)


def validate_read_only_query(query: str) -> str:
    """Validate that query is one non-locking SELECT/WITH/plain EXPLAIN statement."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Query must be a non-empty string")

    sanitized = sanitize_sql(query)
    semicolons = [index for index, char in enumerate(sanitized) if char == ";"]
    if len(semicolons) > 1:
        raise ValueError("Exactly one SQL statement is allowed")
    if semicolons:
        semicolon = semicolons[0]
        if not sanitized[:semicolon].strip() or sanitized[semicolon + 1:].strip():
            raise ValueError("Exactly one SQL statement is allowed; a semicolon is permitted only at the end")
        statement = sanitized[:semicolon].strip()
    else:
        statement = sanitized.strip()
    first_match = re.match(r"([A-Za-z]+)", statement)
    first_keyword = first_match.group(1).upper() if first_match else ""
    if first_keyword not in {"SELECT", "WITH", "EXPLAIN"}:
        raise ValueError("Only SELECT, WITH, or plain EXPLAIN queries are allowed")

    forbidden = FORBIDDEN_KEYWORDS.search(statement)
    if forbidden:
        raise ValueError(f"Read-only mode rejects SQL keyword {forbidden.group(1).upper()}")
    if re.search(r"\bSELECT\b[\s\S]*?\bINTO\b", statement, re.IGNORECASE):
        raise ValueError("SELECT INTO is not allowed")
    if re.search(
        r"\bFOR\s+(UPDATE|NO\s+KEY\s+UPDATE|SHARE|KEY\s+SHARE)\b",
        statement,
        re.IGNORECASE,
    ):
        raise ValueError("Row-locking SELECT queries are not allowed")
    if first_keyword == "EXPLAIN" and not re.search(r"\b(SELECT|WITH)\b", statement, re.IGNORECASE):
        raise ValueError("EXPLAIN must describe a SELECT or WITH query")

    if semicolons:
        return query[:semicolons[0]].strip()
    return query.strip()


def enforce_limit(query: str, limit: int = MAX_ROWS) -> str:
    """Wrap a validated query so existing or nested LIMIT clauses cannot exceed the cap."""
    if not isinstance(limit, int) or limit <= 0:
        raise ValueError("Limit must be a positive integer")
    stripped = validate_read_only_query(query)
    first_keyword = re.match(r"([A-Za-z]+)", sanitize_sql(stripped).lstrip()).group(1).upper()
    if first_keyword == "EXPLAIN":
        return stripped
    return f"SELECT * FROM (\n{stripped}\n) AS _tableau_read_only_query\nLIMIT {limit}"


def get_connection() -> psycopg2.extensions.connection:
    """Create a PostgreSQL connection from exported credentials."""
    host = os.getenv("PG_HOST")
    port = os.getenv("PG_PORT", "5432")
    database = os.getenv("PG_DATABASE")
    user = os.getenv("PG_USER")
    password = os.getenv("PG_PASSWORD")

    missing = [v for v, val in [
        ("PG_HOST", host),
        ("PG_DATABASE", database),
        ("PG_USER", user),
        ("PG_PASSWORD", password),
    ] if not val]
    if missing:
        raise EnvironmentError(f"Missing env vars: {', '.join(missing)}")

    connection = psycopg2.connect(
        host=host,
        port=int(port),
        dbname=database,
        user=user,
        password=password,
    )
    connection.set_session(readonly=True, autocommit=True)
    return connection


def run_query(query: str) -> pd.DataFrame:
    """Execute one validated query and return at most MAX_ROWS rows."""
    safe_query = enforce_limit(query)
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(safe_query)
        if cursor.description is None:
            raise ValueError("Query did not return a result set")
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchmany(MAX_ROWS + 1)[:MAX_ROWS]
        return pd.DataFrame(rows, columns=columns)
    finally:
        conn.close()


def main() -> None:
    """CLI entrypoint for read-only PostgreSQL query execution."""
    parser = argparse.ArgumentParser(
        description="Run one read-only PostgreSQL SELECT/WITH/EXPLAIN query with a 500-row cap"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("query", nargs="?", help="SQL query string")
    group.add_argument("--file", "-f", help="Path to one .sql query file")
    parser.add_argument("--output", "-o", default=".", help="Output directory for CSV")
    parser.add_argument("--env-file", help="Explicit path to a dotenv file")
    args = parser.parse_args()

    if args.env_file:
        env_path = os.path.abspath(os.path.expanduser(args.env_file))
        if not os.path.isfile(env_path):
            parser.error(f"--env-file is not a file: {env_path}")
        load_dotenv(dotenv_path=env_path, override=False)

    query = args.query
    if args.file:
        with open(args.file, "r", encoding="utf-8") as query_file:
            query = query_file.read()

    try:
        validate_read_only_query(query)
    except ValueError as exc:
        parser.error(str(exc))

    os.makedirs(args.output, exist_ok=True)

    print(f"Executing read-only query (maximum {MAX_ROWS} rows)...")
    df = run_query(query)

    csv_path = os.path.join(args.output, "query_results.csv")
    df.to_csv(csv_path, index=False)
    print(f"\nRows returned: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    print(f"CSV saved to: {csv_path}")
    print(f"\nSample (first 10 rows):\n{df.head(10).to_string()}")


if __name__ == "__main__":
    main()
