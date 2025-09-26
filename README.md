# Generic SQLite Database Query Tool

An intelligent database exploration tool that automatically analyzes SQLite databases and suggests useful queries based on schema discovery.

## Features

- **Smart Schema Analysis**: Automatically detects column types, relationships, and data patterns
- **Dynamic Query Generation**: Suggests contextual queries based on your data structure
- **Multiple Output Formats**: Clean table format, structured JSON, or CSV export
- **Multi-query Support**: Execute multiple SQL statements in sequence
- **CSV Export**: Direct export of query results to spreadsheet-friendly format
- **Connection Safety**: Uses proper SQLite context managers to prevent resource leaks
- **Error-friendly**: Helpful suggestions when queries fail with intelligent error handling

## Installation

```bash
# Clone or download the tool
git clone https://github.com/klmn800/solutions-laboratory.git
cd solutions-laboratory/query_db_direct

# Install dependencies
pip install -r requirements.txt
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
| `--db DATABASE` | Path to SQLite database file (required) |
| `--analyze` | Perform comprehensive database analysis |
| `--suggest` | Generate intelligent query suggestions |
| `--tables` | List all tables in the database |
| `--sql "QUERY"` | Execute raw SQL query |
| `--csv "QUERY"` | Execute query and export results to CSV |
| `--csv-file FILE` | Specify CSV output filename (use with --csv) |
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
- Join suggestions for related tables

### Safety Features
- Uses SQLite context managers for safe connection handling
- Read-only database access to prevent accidental modifications
- Input validation and SQL injection protection
- Graceful error handling with helpful error messages

## Requirements

- Python 3.6+
- Standard library only (no external dependencies)

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

This tool is part of the [Solutions Laboratory](https://github.com/klmn800/solutions-laboratory) project. Contributions, suggestions, and feedback are welcome!

## Author

**klmn800**
- Building practical database tools
- Learning modern development workflows
- Experimenting with AI-assisted programming

---

*A self-contained, intelligent database exploration tool designed for developers, analysts, and anyone working with SQLite databases.*