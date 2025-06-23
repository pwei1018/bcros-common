"""move public schema to custom schema

Revision ID: 328095fcc390
Revises: d6a8ffda6b9c
Create Date: 2025-06-10 14:39:17.930581

"""
import importlib.util
import logging
import os
import re
from collections import defaultdict
from pathlib import Path

from alembic import op
from sqlalchemy.sql import text

from notify_api.config import MigrationConfig

# revision identifiers, used by Alembic.
revision = '328095fcc390'
down_revision = 'd6a8ffda6b9c'
branch_labels = None
depends_on = None

logger = logging.getLogger(__name__)

def get_table_dependencies(conn, schema='public'):
    """Build a dependency graph of tables based on foreign keys."""
    # Get all tables in schema
    tables = conn.execute(text(f"""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = '{schema}'
        AND table_type = 'BASE TABLE'
    """)).fetchall()

    # Build dependency graph
    graph = defaultdict(set)
    tables_with_fks = conn.execute(text(f"""
        SELECT tc.table_name, ccu.table_name as referenced_table
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name
          AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage ccu
          ON ccu.constraint_name = tc.constraint_name
          AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
        AND tc.table_schema = '{schema}'
    """)).fetchall()

    for table, referenced_table in tables_with_fks:
        graph[table].add(referenced_table)

    return graph, [t[0] for t in tables]

def topological_sort(graph, nodes):
    """Topologically sort tables based on foreign key dependencies."""
    visited = set()
    result = []

    def visit(node):
        if node not in visited:
            visited.add(node)
            for neighbor in graph.get(node, []):
                visit(neighbor)
            result.append(node)

    for node in nodes:
        visit(node)

    return result

def copy_data_with_dependencies(conn, target_schema):
    """Copy data respecting foreign key constraints with row count verification."""
    # Get dependency graph for public schema
    graph, all_tables = get_table_dependencies(conn, 'public')

    # Get topological order for copying
    copy_order = topological_sort(graph, all_tables)
    logger.info(f"Determined copy order: {copy_order}")

    # Dictionary to track row counts
    row_counts = {}

    for table_name in copy_order:
        try:
            # Check if table exists in target schema
            exists_in_target = conn.execute(text(f"""
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = '{target_schema}'
                AND table_name = '{table_name}'
            """)).scalar()

            if not exists_in_target:
                logger.info(f"Skipping {table_name} - not in target schema")
                continue

            # Get source row count
            source_count = conn.execute(
                text(f"SELECT COUNT(*) FROM public.{table_name}")
            ).scalar()
            row_counts[table_name] = {'source': source_count}

            # Skip if target has data (but verify counts match)
            target_has_data = conn.execute(
                text(f"SELECT EXISTS (SELECT 1 FROM {target_schema}.{table_name} LIMIT 1)")
            ).scalar()

            if target_has_data:
                target_count = conn.execute(
                    text(f"SELECT COUNT(*) FROM {target_schema}.{table_name}")
                ).scalar()
                if source_count != target_count:
                    logger.warning(
                        f"Table {table_name} has data but counts don't match "
                        f"(public: {source_count}, {target_schema}: {target_count}). "
                        f"Skipping this table."
                    )
                    continue
                logger.info(f"Skipping {table_name} - target already has matching data")
                continue

            # Get all columns with proper quoting
            columns = conn.execute(text(f"""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = '{target_schema}'
                AND table_name = '{table_name}'
                ORDER BY ordinal_position
            """)).fetchall()

            if not columns:
                logger.warning(f"No columns found for {target_schema}.{table_name}")
                continue

            # Build properly quoted column list
            quoted_columns = [f'"{col[0]}"' for col in columns]
            columns_str = ", ".join(quoted_columns)

            # Copy data
            logger.info(f"Copying data to {target_schema}.{table_name}")
            conn.execute(text(f"""
                INSERT INTO {target_schema}.{table_name} ({columns_str})
                SELECT {columns_str} FROM public.{table_name}
            """))

            # Verify target row count
            target_count = conn.execute(
                text(f"SELECT COUNT(*) FROM {target_schema}.{table_name}")
            ).scalar()
            row_counts[table_name]['target'] = target_count

            if source_count != target_count:
                logger.error(
                    f"Row count mismatch after copy for {table_name} "
                    f"(public: {source_count}, {target_schema}: {target_count})"
                )
                # Let the error bubble up to abort the entire migration
            update_sequences_for_table(conn, target_schema, table_name)

        except Exception as e:
            logger.error(f"Error processing table {table_name}: {str(e)}")
            # Don't explicitly ROLLBACK here - let Alembic handle the transaction
            raise  # Re-raise to ensure Alembic marks the migration as failed

    logger.info("All tables processed successfully")
    logger.debug(f"Row count verification: {row_counts}")

def update_sequences_for_table(conn, schema, table_name):
    """Update all sequences for a table to match the max ID values."""
    # Get primary key column and its sequence
    pk_info = conn.execute(text(f"""
        SELECT a.attname as column_name,
               pg_get_serial_sequence('{schema}.{table_name}', a.attname) as sequence_name
        FROM pg_index i
        JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
        WHERE i.indrelid = '{schema}.{table_name}'::regclass
        AND i.indisprimary
    """)).fetchone()

    if not pk_info:
        logger.debug(f"No primary key sequence found for {schema}.{table_name}")
        return

    column_name, sequence_name = pk_info
    if not sequence_name:
        logger.debug(f"No sequence found for {schema}.{table_name}.{column_name}")
        return

    # Get current max ID
    max_id = conn.execute(
        text(f"SELECT COALESCE(MAX({column_name}), 0) FROM {schema}.{table_name}")
    ).scalar()

    # Set sequence to max ID + 1 without advancing the sequence
    # The 'false' parameter means the sequence is marked as not called,
    # so the next nextval() will return exactly this value
    conn.execute(text(f"""
        SELECT setval('{sequence_name}', {max_id + 1}, false)
    """))

    logger.info(f"Updated sequence {sequence_name} for {schema}.{table_name} to {max_id + 1}")

def get_target_schema():
    """Minimal schema name fetch with validation."""
    schema = os.getenv("NOTIFY_DATABASE_SCHEMA", "public")
    if not re.match(r'^[a-z_][a-z0-9_]*$', schema, re.I):
        raise ValueError(f"Invalid schema name: {schema}")
    return schema

def get_migration_files():
    """Get sorted migration files."""
    migrations_dir = Path(__file__).parent.parent / 'versions'
    return sorted(
        f for f in os.listdir(migrations_dir)
        if f.endswith('.py') and f != '__init__.py'
    )

def load_migration_module(file_path):
    """Load a migration module from file."""
    spec = importlib.util.spec_from_file_location(f"migration_{file_path.stem}", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def upgrade():
    target_schema = get_target_schema()
    if target_schema == 'public':
        logger.info("Target schema is public, skipping migration")
        return
    
    conn = op.get_bind()
    
    # Save original search path
    original_search_path = conn.execute(text('SHOW search_path')).scalar()
    logger.info(f"Original search path: {original_search_path}")
    
    try:
        # Create schema if it doesn't exist
        if not conn.execute(
            text(f"SELECT 1 FROM information_schema.schemata WHERE schema_name = '{target_schema}'")
        ).scalar():
            conn.execute(text(f"CREATE SCHEMA {target_schema}"))

        # Set search path for this connection only
        conn.execute(text(f"SET LOCAL search_path TO {target_schema}"))
        logger.info(f"Set connection search_path to {target_schema}")

        # Run all previous migrations in the new schema
        migrations_dir = Path(__file__).parent.parent / 'versions'
        for file in get_migration_files():
            if file == os.path.basename(__file__):
                continue

            file_path = migrations_dir / file
            try:
                module = load_migration_module(file_path)
                logger.info(f"Applying {file} in schema {target_schema}")
                module.upgrade()
            except Exception as e:
                logger.error(f"Failed to apply {file}: {str(e)}")
                raise

        # COPY DATA FROM PUBLIC SCHEMA
        copy_data_with_dependencies(conn, target_schema)

        logger.info("Migration completed successfully (without ALTER DATABASE)")

    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise
    finally:
        # Always restore original search path
        try:
            conn.execute(text(f"SET search_path TO {original_search_path}"))
        except Exception as e:
            logger.error(f"Failed to restore search path: {str(e)}")

def downgrade():
    target_schema = get_target_schema()
    
    # Skip if target schema is public
    if target_schema == 'public':
        logger.info("Target schema is public, skipping downgrade")
        return

    conn = op.get_bind()

    try:
        # Check if schema exists
        schema_exists = conn.execute(
            text(f"SELECT 1 FROM information_schema.schemata WHERE schema_name = '{target_schema}'")
        ).scalar()

        if not schema_exists:
            logger.info(f"Schema {target_schema} does not exist, nothing to downgrade")
            return

        # Then drop the schema
        logger.info(f"Dropping schema {target_schema}")
        conn.execute(text(f"DROP SCHEMA {target_schema} CASCADE"))

        logger.info("Downgrade completed successfully")
    except Exception as e:
        logger.error(f"Downgrade failed: {str(e)}")
        raise