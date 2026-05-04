# Generic SQLite Database Query Tool

An intelligent, **read-only** database exploration tool that automatically analyzes SQLite databases and suggests useful queries based on schema discovery.

Built primarily for AI agents and CLI workflows. Read-only is enforced at the SQLite layer (URI `?mode=ro`), so this tool can be pointed at any database without risk of accidental mutation. For writes, use a tool built for that purpose.

## Features

- **Read-only by default**: Destructive SQL like `DELETE`, `DROP`, `UPDATE`, `INSERT` is rejected by SQLite itself, not by string-matching. Safe for exploratory work and agent-driven querying.
- **Smart Schema Analysis**: Automatically detects column types, date/numeric/text categories, and naming patterns
- **Dynamic Query Generation**: Suggests contextual queries based on your data structure
- **Multiple Output Formats**: Clean table format, structured JSON, or CSV export
- **Multi-statement queries**: `--sql` accepts multiple `;`-separated statements in one invocation
- **CSV Export**: Direct export of query results to spreadsheet-friendly format
- **Error-friendly**: Lists available tables when you typo a name, errors clearly if the database file doesn't exist (instead of silently creating an empty one)

## Installation

```bash
# Clone the tool
git clone https://github.com/klmn800/query-db-direct.git
cd query-db-direct

# No dependencies required - uses Python standard library only
```

## Quick Start

```bash
# Explore any SQLite database
python query_db_direct.py --db your_database.db --analyze

# Get intelligent query suggestions
python query_db_direct.py --db your_database.db --suggest

# Execute raw SQL
python query_db_direct.py --sql "SELECT COUNT(*) FROM users" --db your_data.db

# Export to CSV
python query_db_direct.py --csv "SELECT * FROM users LIMIT 100" --csv-file users.csv --db your_data.db

# List all tables
python query_db_direct.py --tables --db your_data.db
```

## Command Line Options

| Option | Description |
|--------|-------------|
| `--db DATABASE` | Path to SQLite database file (must exist; tool errors out otherwise) |
| `--analyze` | Perform comprehensive database analysis |
| `--suggest` | Generate intelligent query suggestions |
| `--tables` | List all tables in the database |
| `--sql "QUERY"` | Execute raw SQL query (read-only; multiple `;`-separated statements OK) |
| `--csv "QUERY"` | Execute query and export results to CSV |
| `--csv-file FILE` | Specify CSV output filename (use with `--csv`) |
| `--json` | Output results in JSON format |
| `--help` | Show help message |

## Example Output

```bash
$ python query_db_direct.py --analyze --db news.db

Database Analysis
==================================================
Database: news.db
• Database contains 2 tables with 1,250 total rows
• Largest tables: news_articles (1,200 rows), news_sentiment (50 rows)

Table Details:
------------------------------

news_articles (1,200 rows)
  Date columns: time_published, created_at
  Numeric columns: sentiment_score
  Text columns: title, summary, source, authors

news_sentiment (50 rows)
  Date columns: analysis_date
  Numeric columns: sentiment_score, confidence
  Text columns: symbol, sentiment_label
```

## Use Cases

- **Agent-driven querying**: Safe to hand to an AI agent — read-only by construction means the agent can't damage the database, even on a hallucinated SQL statement.
- **Database Exploration**: Quickly understand the structure and content of unfamiliar databases
- **Data Analysis**: Export specific datasets for analysis in Excel or other tools
- **Development**: Test queries and explore schema during development
- **Data Migration**: Analyze source databases before migration projects
- **Reporting**: Generate CSV exports for regular reporting workflows

## Technical Details

### Schema Discovery
The tool automatically analyzes:
- Column names and data types
- Row counts and data distribution
- Date/time columns for temporal analysis
- Numeric columns for statistical insights
- Text columns for content analysis

### Query Intelligence
Based on schema analysis, the tool suggests:
- Row count queries for each table
- Sample data queries to preview content
- Date range queries for temporal data
- Statistical queries for numeric columns
- **Foreign-key relationship hints** — surfaces likely FK columns based on naming patterns (e.g., `orders.user_id -> users`). These appear as insight strings, not as ready-to-run JOIN SQL.

### Safety Features
- **Read-only enforcement**: connections are opened with the SQLite URI flag `?mode=ro`. Any write statement returns `attempt to write a readonly database` instead of executing.
- **Schema-name validation**: `--schema TABLE` is checked against `sqlite_master` before the table name is interpolated into any `PRAGMA` or `COUNT` query, and identifiers are then double-quoted per the SQL standard.
- **Path validation**: `--db` errors out cleanly if the file doesn't exist (avoids the standard `sqlite3` behavior of silently creating an empty database on a typo'd path).
- **Helpful errors**: when a query fails on a missing table or column, the tool suggests next steps (lists available tables, points at `--schema`).
- **No raw-SQL filtering**: `--sql` runs whatever you give it. There's no `DROP`-detection regex or similar — the read-only mode is the safety boundary, and it's enforced at the database layer, not by string matching.

## Requirements

- Python 3.6+
- Standard library only (no external dependencies)

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

This tool was developed as part of the [Solutions Laboratory](https://github.com/klmn800/solutions-laboratory) project. Contributions, suggestions, and feedback are welcome!

## Author

**klmn800**
- Building practical database tools
- Learning modern development workflows
- Experimenting with AI-assisted programming

---

*A self-contained, intelligent database exploration tool designed for developers, analysts, and anyone working with SQLite databases.*