import pandas as pd


class DataQualityAnalyzer:
    """Data quality checks: overview, referential integrity, column analysis, disabled constraints."""

    def __init__(self, db):
        self.db = db

    def _q(self, sql: str) -> pd.DataFrame:
        try:
            return self.db.execute_query(sql)
        except Exception as ex:
            return pd.DataFrame([{"Error": str(ex)}])

    def get_tables_list(self) -> pd.DataFrame:
        return self._q("""
        SELECT s.name AS [Schema], t.name AS [Table]
        FROM sys.tables t
        JOIN sys.schemas s ON s.schema_id = t.schema_id
        ORDER BY s.name, t.name
        """)

    def get_data_overview(self) -> pd.DataFrame:
        return self._q("""
        SELECT
            s.name                  AS [Schema],
            t.name                  AS [Table],
            SUM(p.rows)             AS [Rows],
            COUNT(c.column_id)      AS [Columns],
            SUM(CASE c.is_nullable WHEN 1 THEN 1 ELSE 0 END) AS [Nullable Cols],
            (SELECT COUNT(*) FROM sys.indexes i
             WHERE i.object_id = t.object_id AND i.type > 0)            AS [Indexes],
            (SELECT COUNT(*) FROM sys.foreign_keys fk
             WHERE fk.parent_object_id = t.object_id)                   AS [FKs Out],
            (SELECT COUNT(*) FROM sys.foreign_keys fk
             WHERE fk.referenced_object_id = t.object_id)               AS [FKs In],
            CONVERT(VARCHAR, t.create_date, 120)    AS [Created],
            CONVERT(VARCHAR, t.modify_date, 120)    AS [Modified]
        FROM sys.tables t
        JOIN sys.schemas    s  ON s.schema_id  = t.schema_id
        JOIN sys.partitions p  ON p.object_id  = t.object_id AND p.index_id IN (0,1)
        JOIN sys.columns    c  ON c.object_id  = t.object_id
        GROUP BY s.name, t.name, t.object_id, t.create_date, t.modify_date
        ORDER BY SUM(p.rows) DESC
        """)

    def get_referential_integrity(self) -> pd.DataFrame:
        return self._q("""
        SELECT
            OBJECT_SCHEMA_NAME(fk.parent_object_id)     AS [Child Schema],
            OBJECT_NAME(fk.parent_object_id)             AS [Child Table],
            COL_NAME(fkc.parent_object_id, fkc.parent_column_id) AS [Child Column],
            OBJECT_SCHEMA_NAME(fk.referenced_object_id) AS [Parent Schema],
            OBJECT_NAME(fk.referenced_object_id)         AS [Parent Table],
            COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id) AS [Parent Column],
            fk.name                                      AS [Constraint],
            CASE fk.is_disabled    WHEN 1 THEN '⚠️ DISABLED'    ELSE '✅ Enabled'    END AS [Enabled],
            CASE fk.is_not_trusted WHEN 1 THEN '⚠️ NOT TRUSTED' ELSE '✅ Trusted'    END AS [Trusted],
            fk.delete_referential_action_desc            AS [On Delete],
            fk.update_referential_action_desc            AS [On Update]
        FROM sys.foreign_keys        fk
        JOIN sys.foreign_key_columns fkc ON fkc.constraint_object_id = fk.object_id
        ORDER BY [Child Schema], [Child Table]
        """)

    def get_column_stats(self, schema: str, table: str) -> pd.DataFrame:
        return self._q(f"""
        SELECT
            c.name                  AS [Column],
            tp.name                 AS [Type],
            c.max_length            AS [Length],
            c.precision             AS [Precision],
            c.scale                 AS [Scale],
            c.is_nullable           AS [Nullable],
            c.is_identity           AS [Identity],
            CASE WHEN pk.column_id IS NOT NULL THEN '✅' ELSE '' END AS [PK],
            CASE WHEN fkc.parent_column_id IS NOT NULL THEN '✅' ELSE '' END AS [FK],
            CASE WHEN uc.column_id IS NOT NULL THEN '✅' ELSE '' END AS [Unique],
            ISNULL(CAST(ep.value AS NVARCHAR(500)), '') AS [Description]
        FROM sys.columns c
        JOIN sys.types   tp ON tp.user_type_id = c.user_type_id
        JOIN sys.tables  t  ON t.object_id = c.object_id
        JOIN sys.schemas s  ON s.schema_id = t.schema_id
        LEFT JOIN sys.index_columns pk
            ON  pk.object_id = c.object_id AND pk.column_id = c.column_id
            AND pk.index_id = (
                SELECT TOP 1 i.index_id FROM sys.indexes i
                WHERE i.object_id = t.object_id AND i.is_primary_key = 1
            )
        LEFT JOIN sys.foreign_key_columns fkc
            ON fkc.parent_object_id = c.object_id AND fkc.parent_column_id = c.column_id
        LEFT JOIN (
            SELECT ic2.object_id, ic2.column_id
            FROM sys.index_columns ic2
            JOIN sys.indexes i2 ON i2.object_id = ic2.object_id AND i2.index_id = ic2.index_id
            WHERE i2.is_unique = 1 AND i2.is_primary_key = 0
        ) uc ON uc.object_id = c.object_id AND uc.column_id = c.column_id
        LEFT JOIN sys.extended_properties ep
            ON ep.major_id = c.object_id AND ep.minor_id = c.column_id
            AND ep.name = 'MS_Description'
        WHERE s.name = '{schema}' AND t.name = '{table}'
        ORDER BY c.column_id
        """)

    def get_disabled_constraints(self) -> pd.DataFrame:
        return self._q("""
        SELECT
            OBJECT_SCHEMA_NAME(o2.parent_object_id) AS [Schema],
            OBJECT_NAME(o2.parent_object_id)         AS [Table],
            o2.name                                  AS [Constraint],
            o2.type_desc                             AS [Type],
            '⚠️ DISABLED'                            AS [Status]
        FROM sys.objects o2
        WHERE o2.type IN ('F','C')
          AND OBJECTPROPERTY(o2.object_id, 'CnstIsDisabled') = 1
        ORDER BY [Schema], [Table]
        """)

    def get_duplicate_values(self, schema: str, table: str, column: str) -> pd.DataFrame:
        return self._q(f"""
        SELECT
            [{column}]      AS [Value],
            COUNT(*)        AS [Count]
        FROM [{schema}].[{table}]
        GROUP BY [{column}]
        HAVING COUNT(*) > 1
        ORDER BY COUNT(*) DESC
        """)
