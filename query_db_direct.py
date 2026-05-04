#!/usr/bin/env python3
"""
Generic SQLite Database Query Tool
A read-only tool for exploring and querying SQLite databases with intelligent schema discovery.

Designed primarily for AI agents and CLI workflows. All database connections are
opened in read-only mode -- for writes, use a tool built for that purpose. This is
a safety AND a convenience choice: the tool can be pointed at any database without
risk of accidental mutation.

KEY FEATURES:
- Raw SQL execution: --sql "SELECT * FROM table_name LIMIT 5"
- Schema exploration: --schema table_name (validated against sqlite_master)
- Database structure discovery: --tables, --analyze, --suggest
- Output formats: table (default), JSON (--json), CSV (--csv)
- Error handling with helpful suggestions
- Works with any SQLite database

USAGE EXAMPLES:
    python query_db_direct.py --sql "SELECT COUNT(*) FROM users"
    python query_db_direct.py --tables
    python query_db_direct.py --schema users
    python query_db_direct.py --db my_data.db --analyze

Author: Ben Keilman
"""

import sqlite3
import sys
import json
import argparse
import os
import csv

class DirectDBQuery:
    def __init__(self, db_path="database.db"):
        """Initialize the query tool. Resolves the path; existence is enforced
        on first connect (read-only mode requires the file to exist)."""
        self.db_path = db_path

        # Handle relative paths relative to current working directory
        if not os.path.isabs(self.db_path):
            self.db_path = os.path.abspath(self.db_path)

        if not os.path.exists(self.db_path):
            raise FileNotFoundError("Database not found: {}".format(self.db_path))

    def _connect(self):
        """Open a read-only SQLite connection.

        Read-only mode is enforced via SQLite's URI form (?mode=ro). This makes
        the tool safe to point at any database -- destructive SQL like DROP,
        DELETE, UPDATE will be rejected by SQLite itself.
        """
        # Convert OS path to a SQLite file URI (cross-platform).
        # Windows: C:\foo\bar.db -> /C:/foo/bar.db -> file:/C:/foo/bar.db?mode=ro
        # Unix:    /foo/bar.db    -> /foo/bar.db    -> file:/foo/bar.db?mode=ro
        path_uri = self.db_path.replace("\\", "/")
        if not path_uri.startswith("/"):
            path_uri = "/" + path_uri
        return sqlite3.connect("file:{}?mode=ro".format(path_uri), uri=True)

    @staticmethod
    def _quote_ident(name):
        """Quote an SQL identifier (table/column name) for safe interpolation.

        SQL identifiers can't be passed as bind parameters, so when we need to
        embed a table name in a query we double-quote it and escape any internal
        quotes per the SQL standard. Used only after the identifier has been
        validated against sqlite_master.
        """
        return '"' + name.replace('"', '""') + '"'

    def execute_raw_sql(self, sql, output_format='table'):
        """Execute raw SQL and return results in specified format"""
        try:
            with self._connect() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Handle multiple statements
                statements = [stmt.strip() for stmt in sql.split(';') if stmt.strip()]
                all_results = []

                for stmt in statements:
                    cursor.execute(stmt)
                    results = cursor.fetchall()
                    all_results.append([dict(row) for row in results])

                if output_format == 'json':
                    return json.dumps(all_results, indent=2, default=str)
                elif output_format == 'table':
                    return self._format_table_results(all_results)
                else:
                    return all_results

        except Exception as e:
            error_msg = "SQL Error: {}".format(e)
            # Try to provide helpful suggestions
            if "no such table" in str(e).lower():
                tables = self.get_table_names()
                error_msg += "\nAvailable tables: {}".format(", ".join(tables))
            elif "no such column" in str(e).lower():
                error_msg += "\nTip: Use --schema <table> to see available columns"

            if output_format == 'json':
                return json.dumps({"error": error_msg})
            else:
                return error_msg

    def get_table_names(self):
        """Get list of all table names in database"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                tables = [row[0] for row in cursor.fetchall()]
                return tables
        except Exception:
            return []

    def get_table_schema(self, table_name):
        """Get schema information for a table.

        The table name is validated against sqlite_master before any
        identifier interpolation, and then quoted via _quote_ident.
        """
        try:
            with self._connect() as conn:
                cursor = conn.cursor()

                # Whitelist check: confirm the table exists before interpolating
                # its name into PRAGMA / COUNT statements.
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table_name,)
                )
                if not cursor.fetchone():
                    cursor.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                    )
                    available = [r[0] for r in cursor.fetchall()]
                    return {"error": "Table '{}' not found. Available tables: {}".format(
                        table_name, ", ".join(available) if available else "(none)")}

                quoted = self._quote_ident(table_name)

                # Get column info
                cursor.execute("PRAGMA table_info({})".format(quoted))
                columns = cursor.fetchall()

                # Get row count
                cursor.execute("SELECT COUNT(*) FROM {}".format(quoted))
                row_count = cursor.fetchone()[0]

                # Get indexes
                cursor.execute("PRAGMA index_list({})".format(quoted))
                indexes = cursor.fetchall()

                schema_info = {
                    'table': table_name,
                    'columns': [
                        {
                            'name': col[1],
                            'type': col[2],
                            'not_null': bool(col[3]),
                            'primary_key': bool(col[5])
                        }
                        for col in columns
                    ],
                    'row_count': row_count,
                    'indexes': [idx[1] for idx in indexes]
                }

                return schema_info

        except Exception as e:
            return {"error": "Error getting schema for {}: {}".format(table_name, e)}

    def _format_table_results(self, all_results):
        """Format query results as readable tables"""
        output = []

        for i, results in enumerate(all_results):
            if i > 0:
                output.append("\n" + "="*60 + "\n")

            if not results:
                output.append("No results returned")
                continue

            # Get column names
            columns = list(results[0].keys())

            # Calculate column widths
            col_widths = {}
            for col in columns:
                col_widths[col] = max(
                    len(col),
                    max(len(str(row.get(col, ''))) for row in results[:20])  # Sample first 20 rows
                )
                col_widths[col] = min(col_widths[col], 30)  # Max width 30

            # Header
            header = " | ".join(col.ljust(col_widths[col]) for col in columns)
            output.append(header)
            output.append("-" * len(header))

            # Rows
            for row in results:
                row_str = " | ".join(
                    str(row.get(col, ''))[:col_widths[col]].ljust(col_widths[col])
                    for col in columns
                )
                output.append(row_str)

            output.append("\nRows returned: {}".format(len(results)))

        return "\n".join(output)

    def export_to_csv(self, sql_query, output_file=None):
        """Export query results to CSV format"""
        try:
            with self._connect() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(sql_query)
                results = cursor.fetchall()

                if not results:
                    return {"error": "No results to export"}

                if output_file is None:
                    output_file = "query_results.csv"

                with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                    # Get column names from the first row
                    fieldnames = list(results[0].keys())
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                    writer.writeheader()
                    for row in results:
                        writer.writerow(dict(row))

                return {"success": "Data exported to {}".format(output_file), "rows": len(results)}

        except Exception as e:
            return {"error": "CSV export failed: {}".format(e)}

    def analyze_database_schema(self):
        """Analyze entire database schema and suggest useful queries"""
        analysis = {
            'database_path': self.db_path,
            'tables': {},
            'suggested_queries': [],
            'insights': []
        }

        tables = self.get_table_names()
        if not tables:
            return analysis

        for table in tables:
            schema = self.get_table_schema(table)
            if 'error' in schema:
                continue

            table_analysis = self._analyze_table_schema(table, schema)
            analysis['tables'][table] = table_analysis

            # Generate suggested queries for this table
            suggestions = self._generate_table_queries(table, table_analysis)
            analysis['suggested_queries'].extend(suggestions)

        # Generate database-wide insights
        analysis['insights'] = self._generate_database_insights(analysis['tables'])

        return analysis

    def _analyze_table_schema(self, table_name, schema):
        """Analyze a single table's schema"""
        analysis = {
            'row_count': schema.get('row_count', 0),
            'column_types': {},
            'date_columns': [],
            'numeric_columns': [],
            'text_columns': [],
            'primary_keys': [],
            'has_timestamps': False,
            'likely_relationships': []
        }

        for col in schema.get('columns', []):
            col_name = col['name']
            col_type = col['type'].upper()

            analysis['column_types'][col_name] = col_type

            if col['primary_key']:
                analysis['primary_keys'].append(col_name)

            # Categorize columns by type
            if 'INT' in col_type or 'REAL' in col_type or 'FLOAT' in col_type or 'NUMERIC' in col_type:
                analysis['numeric_columns'].append(col_name)
            elif 'TEXT' in col_type or 'CHAR' in col_type or 'VARCHAR' in col_type:
                analysis['text_columns'].append(col_name)
            elif 'DATE' in col_type or 'TIME' in col_type:
                analysis['date_columns'].append(col_name)

            # Detect timestamp patterns (but not numeric scores that happen to have time/date in name)
            if (any(keyword in col_name.lower() for keyword in ['created', 'updated', 'modified', 'time', 'date']) and
                not any(keyword in col_name.lower() for keyword in ['score', 'label', 'amount', 'value'])):
                analysis['has_timestamps'] = True
                if col_name not in analysis['date_columns']:
                    analysis['date_columns'].append(col_name)

        return analysis

    def _generate_table_queries(self, table_name, table_analysis):
        """Generate useful queries for a specific table"""
        queries = []

        # Basic exploration queries
        if table_analysis['row_count'] > 0:
            queries.append({
                'name': f'sample_{table_name}',
                'description': f'Sample data from {table_name}',
                'sql': f'SELECT * FROM {table_name} LIMIT 5'
            })

            queries.append({
                'name': f'count_{table_name}',
                'description': f'Total rows in {table_name}',
                'sql': f'SELECT COUNT(*) as total_rows FROM {table_name}'
            })

        # Date-based queries
        if table_analysis['date_columns']:
            date_col = table_analysis['date_columns'][0]
            queries.append({
                'name': f'recent_{table_name}',
                'description': f'Recent records from {table_name}',
                'sql': f'SELECT * FROM {table_name} ORDER BY {date_col} DESC LIMIT 10'
            })

            queries.append({
                'name': f'date_range_{table_name}',
                'description': f'Date range in {table_name}',
                'sql': f'SELECT MIN({date_col}) as earliest, MAX({date_col}) as latest FROM {table_name}'
            })

        # Numeric analysis
        for num_col in table_analysis['numeric_columns'][:3]:  # Limit to first 3
            if 'id' not in num_col.lower():  # Skip ID columns
                queries.append({
                    'name': f'stats_{table_name}_{num_col}',
                    'description': f'Statistics for {num_col} in {table_name}',
                    'sql': f'SELECT AVG({num_col}) as avg_{num_col}, MIN({num_col}) as min_{num_col}, MAX({num_col}) as max_{num_col} FROM {table_name}'
                })

        # Text analysis
        for text_col in table_analysis['text_columns'][:2]:  # Limit to first 2
            if any(keyword in text_col.lower() for keyword in ['title', 'name', 'description', 'summary']):
                queries.append({
                    'name': f'popular_{text_col}_{table_name}',
                    'description': f'Most common values in {text_col}',
                    'sql': f'SELECT {text_col}, COUNT(*) as frequency FROM {table_name} GROUP BY {text_col} ORDER BY frequency DESC LIMIT 10'
                })

        return queries

    def _generate_database_insights(self, tables_analysis):
        """Generate insights about the entire database"""
        insights = []

        total_tables = len(tables_analysis)
        total_rows = sum(t.get('row_count', 0) for t in tables_analysis.values())

        insights.append(f"Database contains {total_tables} tables with {total_rows:,} total rows")

        # Find largest tables
        largest_tables = sorted(
            [(name, analysis.get('row_count', 0)) for name, analysis in tables_analysis.items()],
            key=lambda x: x[1], reverse=True
        )[:3]

        if largest_tables and largest_tables[0][1] > 0:
            insights.append(f"Largest tables: {', '.join(f'{name} ({count:,} rows)' for name, count in largest_tables if count > 0)}")

        # Analyze relationships
        potential_relationships = []
        table_names = list(tables_analysis.keys())

        for table_name, analysis in tables_analysis.items():
            for col_name in analysis.get('column_types', {}):
                # Look for foreign key patterns
                for other_table in table_names:
                    if (other_table != table_name and
                        (col_name.lower().startswith(other_table.lower()) or
                         col_name.lower().endswith(other_table.lower()) or
                         other_table.lower() in col_name.lower())):
                        potential_relationships.append(f"{table_name}.{col_name} -> {other_table}")

        if potential_relationships:
            insights.append(f"Potential relationships: {', '.join(potential_relationships[:3])}")

        return insights

def main():
    parser = argparse.ArgumentParser(
        description='Generic SQLite Database Query Tool (read-only)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all tables
  python query_db_direct.py --tables

  # Show table schema
  python query_db_direct.py --schema users

  # Raw SQL query (multiple ;-separated statements supported)
  python query_db_direct.py --sql "SELECT COUNT(*) FROM users"

  # JSON output
  python query_db_direct.py --sql "SELECT * FROM users LIMIT 5" --json

  # Custom database
  python query_db_direct.py --db my_data.db --tables

  # Smart analysis
  python query_db_direct.py --analyze
  python query_db_direct.py --suggest

  # CSV export
  python query_db_direct.py --csv "SELECT * FROM users LIMIT 100" --csv-file users.csv
        """)

    # Enhanced options
    parser.add_argument('--sql', help='Execute raw SQL query (read-only; multiple ;-separated statements OK)')
    parser.add_argument('--schema', help='Show schema for specified table')
    parser.add_argument('--tables', action='store_true', help='List all tables')
    parser.add_argument('--analyze', action='store_true', help='Analyze database schema and provide insights')
    parser.add_argument('--suggest', action='store_true', help='Suggest useful queries based on schema analysis')
    parser.add_argument('--csv', help='Execute SQL query and export results to CSV')
    parser.add_argument('--csv-file', help='Output filename for CSV export (default: query_results.csv)')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    parser.add_argument('--db', default='database.db',
                       help='Database path (default: database.db in current directory)')

    args = parser.parse_args()

    # If no arguments provided, show help and exit before touching the filesystem.
    if not (args.sql or args.schema or args.tables or args.analyze or args.suggest or args.csv):
        print("Generic SQLite Database Query Tool (read-only)")
        print("Use --help for usage information")
        print("\nQuick start:")
        print("  --tables     List all tables")
        print("  --analyze    Analyze database structure")
        print("  --suggest    Get suggested queries")
        print("  --schema X   Show schema for table X")
        print("  --sql 'X'    Execute SQL query X")
        print("  --csv 'X'    Export query results to CSV")
        return

    # Validate the database exists before doing anything else.
    try:
        db = DirectDBQuery(args.db)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    output_format = 'json' if args.json else 'table'

    # Handle enhanced features
    if args.sql:
        result = db.execute_raw_sql(args.sql, output_format)
        print(result)
        return

    if args.schema:
        schema = db.get_table_schema(args.schema)
        if args.json:
            print(json.dumps(schema, indent=2))
        else:
            if 'error' in schema:
                print(schema['error'])
            else:
                print("Table: {}".format(schema['table']))
                print("Rows: {:,}".format(schema['row_count']))
                print("\nColumns:")
                for col in schema['columns']:
                    pk = " (PRIMARY KEY)" if col['primary_key'] else ""
                    null = " NOT NULL" if col['not_null'] else ""
                    print("  {} - {}{}{}".format(col['name'], col['type'], null, pk))
                if schema['indexes']:
                    print("\nIndexes: {}".format(", ".join(schema['indexes'])))
        return

    if args.tables:
        tables = db.get_table_names()
        if args.json:
            print(json.dumps({"tables": tables}))
        else:
            print("Tables in database:")
            for table in tables:
                print("  {}".format(table))
        return

    if args.analyze:
        analysis = db.analyze_database_schema()
        if args.json:
            print(json.dumps(analysis, indent=2))
        else:
            print("Database Analysis")
            print("=" * 50)
            print("Database: {}".format(analysis['database_path']))

            for insight in analysis['insights']:
                print("• {}".format(insight))

            print("\nTable Details:")
            print("-" * 30)
            for table_name, table_info in analysis['tables'].items():
                print("\n{} ({:,} rows)".format(table_name, table_info['row_count']))
                if table_info['date_columns']:
                    print("  Date columns: {}".format(', '.join(table_info['date_columns'])))
                if table_info['numeric_columns']:
                    print("  Numeric columns: {}".format(', '.join(table_info['numeric_columns'][:5])))
                if table_info['text_columns']:
                    print("  Text columns: {}".format(', '.join(table_info['text_columns'][:5])))
        return

    if args.suggest:
        analysis = db.analyze_database_schema()
        if args.json:
            print(json.dumps(analysis['suggested_queries'], indent=2))
        else:
            print("Suggested Queries")
            print("=" * 50)

            if not analysis['suggested_queries']:
                print("No queries suggested. Database may be empty or inaccessible.")
                return

            for i, query in enumerate(analysis['suggested_queries'], 1):
                print("\n{}. {} - {}".format(i, query['name'], query['description']))
                print("   SQL: {}".format(query['sql']))

            print("\nTo execute a query, use:")
            print('python query_db_direct.py --sql "QUERY_HERE"')
        return

    if args.csv:
        result = db.export_to_csv(args.csv, args.csv_file)
        if 'error' in result:
            print(result['error'])
        else:
            print(result['success'])
            print("Rows exported: {}".format(result['rows']))
        return

if __name__ == "__main__":
    main()