"""
Relationship Analyzer
- Existing FK/PK relationships
- Orphan tables (no FK connections)
- AI-suggested potential relationships
- Mermaid ER diagram generation
"""
import pandas as pd
from .sql_connector import SQLConnector


class RelationshipAnalyzer:
    def __init__(self, connector: SQLConnector):
        self.db = connector

    # ── Existing FK relationships ──────────────────────────────────────────
    def get_relationships(self) -> pd.DataFrame:
        sql = """
        SELECT
            fk.name                                                AS [FK Name],
            OBJECT_SCHEMA_NAME(fk.parent_object_id)               AS [Parent Schema],
            OBJECT_NAME(fk.parent_object_id)                      AS [Parent Table],
            COL_NAME(fkc.parent_object_id,fkc.parent_column_id)   AS [Parent Column],
            OBJECT_SCHEMA_NAME(fk.referenced_object_id)           AS [Ref Schema],
            OBJECT_NAME(fk.referenced_object_id)                  AS [Ref Table],
            COL_NAME(fkc.referenced_object_id,fkc.referenced_column_id) AS [Ref Column],
            fk.delete_referential_action_desc AS [On Delete],
            fk.update_referential_action_desc AS [On Update],
            CASE fk.is_disabled WHEN 1 THEN 'Disabled' ELSE 'Enabled' END AS [Status]
        FROM sys.foreign_keys        fk
        JOIN sys.foreign_key_columns fkc ON fkc.constraint_object_id = fk.object_id
        ORDER BY [Parent Schema],[Parent Table],[FK Name]
        """
        return self.db.execute_query(sql)

    # ── Orphan tables (no FK in or out) ───────────────────────────────────
    def get_orphan_tables(self) -> pd.DataFrame:
        sql = """
        SELECT
            s.name  AS [Schema],
            t.name  AS [Table],
            SUM(p.rows) AS [Row Count],
            (SELECT COUNT(*) FROM sys.columns c WHERE c.object_id = t.object_id) AS [Columns]
        FROM sys.tables t
        JOIN sys.schemas s ON s.schema_id = t.schema_id
        LEFT JOIN sys.partitions p ON p.object_id = t.object_id AND p.index_id IN (0,1)
        WHERE t.object_id NOT IN (
            SELECT parent_object_id  FROM sys.foreign_keys
            UNION
            SELECT referenced_object_id FROM sys.foreign_keys
        )
        GROUP BY s.name, t.name, t.object_id
        ORDER BY s.name, t.name
        """
        return self.db.execute_query(sql)

    # ── Column name similarity (potential FK candidates) ──────────────────
    def get_join_candidates(self) -> pd.DataFrame:
        """Find columns with same name+type across tables (likely FK candidates)."""
        sql = """
        WITH ColInfo AS (
            SELECT
                OBJECT_SCHEMA_NAME(c.object_id) AS sch,
                OBJECT_NAME(c.object_id)         AS tbl,
                c.name                           AS col,
                tp.name                          AS typ,
                c.object_id
            FROM sys.columns c
            JOIN sys.types   tp ON tp.user_type_id = c.user_type_id
            WHERE OBJECTPROPERTY(c.object_id,'IsUserTable') = 1
        )
        SELECT
            a.sch  AS [Schema A], a.tbl AS [Table A], a.col AS [Column],
            b.sch  AS [Schema B], b.tbl AS [Table B],
            a.typ  AS [Data Type],
            CASE WHEN EXISTS (
                SELECT 1 FROM sys.foreign_keys fk
                JOIN sys.foreign_key_columns fkc ON fkc.constraint_object_id = fk.object_id
                WHERE (fk.parent_object_id    = a.object_id AND
                       COL_NAME(fkc.parent_object_id,fkc.parent_column_id)  = a.col  AND
                       fk.referenced_object_id = b.object_id)
                   OR (fk.parent_object_id    = b.object_id AND
                       COL_NAME(fkc.parent_object_id,fkc.parent_column_id)  = b.col  AND
                       fk.referenced_object_id = a.object_id)
            ) THEN '✅ FK exists' ELSE '⚠️ No FK' END AS [FK Status]
        FROM ColInfo a
        JOIN ColInfo b ON a.col = b.col
                      AND a.typ = b.typ
                      AND a.object_id < b.object_id
        WHERE a.col NOT IN ('CreatedAt','UpdatedAt','ModifiedAt','DeletedAt',
                            'CreatedDate','ModifiedDate','RowVersion','Timestamp')
        ORDER BY [FK Status] DESC, a.col
        """
        return self.db.execute_query(sql)

    # ── Table dependency chain ─────────────────────────────────────────────
    def get_dependency_chain(self, schema: str, table: str) -> pd.DataFrame:
        sql = f"""
        WITH Deps AS (
            -- Tables that this table references (parents)
            SELECT
                'References →' AS Direction,
                OBJECT_SCHEMA_NAME(fk.referenced_object_id) AS Dep_Schema,
                OBJECT_NAME(fk.referenced_object_id)         AS Dep_Table,
                COL_NAME(fkc.parent_object_id,fkc.parent_column_id) AS Via_Column,
                1 AS Depth
            FROM sys.foreign_keys fk
            JOIN sys.foreign_key_columns fkc ON fkc.constraint_object_id = fk.object_id
            WHERE fk.parent_object_id = OBJECT_ID('{schema}.{table}')

            UNION ALL

            -- Tables that reference this table (children)
            SELECT
                '← Referenced by' AS Direction,
                OBJECT_SCHEMA_NAME(fk.parent_object_id),
                OBJECT_NAME(fk.parent_object_id),
                COL_NAME(fkc.parent_object_id,fkc.parent_column_id),
                1
            FROM sys.foreign_keys fk
            JOIN sys.foreign_key_columns fkc ON fkc.constraint_object_id = fk.object_id
            WHERE fk.referenced_object_id = OBJECT_ID('{schema}.{table}')
        )
        SELECT * FROM Deps ORDER BY Direction, Dep_Schema, Dep_Table
        """
        return self.db.execute_query(sql)

    # ── Mermaid ER diagram text ────────────────────────────────────────────
    def generate_mermaid(self, max_tables: int = 30) -> str:
        try:
            fk_df = self.get_relationships()
        except Exception:
            return "erDiagram\n    %% No relationship data available"

        if fk_df.empty:
            return "erDiagram\n    %% No foreign keys defined in this database"

        lines = ["erDiagram"]
        seen_tables: set = set()

        for _, row in fk_df.iterrows():
            pt = f"{row['Parent Schema']}_{row['Parent Table']}".replace(" ", "_")
            rt = f"{row['Ref Schema']}_{row['Ref Table']}".replace(" ", "_")
            lines.append(f"    {pt} ||--o{{ {rt} : \"{row['Parent Column']}\"")
            seen_tables.add(pt)
            seen_tables.add(rt)
            if len(seen_tables) >= max_tables * 2:
                break

        return "\n".join(lines)

    # ── Generate ALTER TABLE SQL for a suggested relationship ──────────────
    @staticmethod
    def generate_fk_sql(
        parent_schema: str, parent_table: str, parent_col: str,
        ref_schema: str, ref_table: str, ref_col: str,
    ) -> str:
        fk_name = (
            f"FK_{parent_table}_{parent_col}__{ref_table}_{ref_col}"[:128]
        )
        return (
            f"ALTER TABLE [{parent_schema}].[{parent_table}]\n"
            f"ADD CONSTRAINT [{fk_name}]\n"
            f"    FOREIGN KEY ([{parent_col}])\n"
            f"    REFERENCES [{ref_schema}].[{ref_table}] ([{ref_col}]);"
        )
