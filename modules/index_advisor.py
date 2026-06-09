import pandas as pd
from .sql_connector import SQLConnector


class IndexAdvisor:
    def __init__(self, connector: SQLConnector):
        self.db = connector

    # ── Missing index recommendations from DMVs ───────────────────────────
    def get_missing_indexes(self) -> pd.DataFrame:
        sql = """
        SELECT TOP 25
            ROUND(
                migs.avg_total_user_cost * migs.avg_user_impact
                * (migs.user_seeks + migs.user_scans), 0
            )                                              AS [Impact Score],
            mid.statement                                  AS [Table],
            ISNULL(mid.equality_columns,   'N/A')          AS [Equality Columns],
            ISNULL(mid.inequality_columns, 'N/A')          AS [Inequality Columns],
            ISNULL(mid.included_columns,   'N/A')          AS [Include Columns],
            migs.user_seeks                                AS [Seeks],
            migs.user_scans                                AS [Scans],
            CAST(migs.avg_user_impact AS DECIMAL(5,1))     AS [Avg Impact %],
            'CREATE NONCLUSTERED INDEX [IX_'
                + REPLACE(REPLACE(REPLACE(mid.statement,'[',''),']',''),'.','_')
                + '_'
                + CAST(ROW_NUMBER() OVER (
                      ORDER BY migs.avg_total_user_cost * migs.avg_user_impact
                             * (migs.user_seeks + migs.user_scans) DESC
                  ) AS VARCHAR(10))
                + '] ON ' + mid.statement
                + ' ('
                + ISNULL(mid.equality_columns, '')
                + CASE WHEN mid.inequality_columns IS NOT NULL
                        AND mid.equality_columns   IS NOT NULL THEN ', ' ELSE '' END
                + ISNULL(mid.inequality_columns, '')
                + ')'
                + CASE WHEN mid.included_columns IS NOT NULL
                       THEN ' INCLUDE (' + mid.included_columns + ')'
                       ELSE '' END
                                                           AS [Suggested SQL]
        FROM sys.dm_db_missing_index_groups          mig
        JOIN sys.dm_db_missing_index_group_stats     migs
             ON migs.group_handle = mig.index_group_handle
        JOIN sys.dm_db_missing_index_details         mid
             ON mid.index_handle  = mig.index_handle
        WHERE mid.database_id = DB_ID()
        ORDER BY [Impact Score] DESC
        """
        try:
            return self.db.execute_query(sql)
        except Exception as exc:
            return pd.DataFrame({"Error": [str(exc)]})

    # ── Unused indexes (write overhead, no reads) ─────────────────────────
    def get_unused_indexes(self) -> pd.DataFrame:
        sql = """
        SELECT
            OBJECT_SCHEMA_NAME(i.object_id)        AS [Schema],
            OBJECT_NAME(i.object_id)                AS [Table],
            i.name                                  AS [Index Name],
            i.type_desc                             AS [Type],
            ISNULL(ius.user_seeks,   0)             AS [Seeks],
            ISNULL(ius.user_scans,   0)             AS [Scans],
            ISNULL(ius.user_lookups, 0)             AS [Lookups],
            ISNULL(ius.user_updates, 0)             AS [Write Cost],
            ISNULL(CAST(ius.last_user_seek AS VARCHAR(23)), 'Never') AS [Last Seek],
            'DROP INDEX ['+ i.name +'] ON ['
                + OBJECT_SCHEMA_NAME(i.object_id) +'].['
                + OBJECT_NAME(i.object_id) +']'    AS [Drop SQL (review first!)]
        FROM sys.indexes i
        LEFT JOIN sys.dm_db_index_usage_stats ius
               ON ius.object_id  = i.object_id
              AND ius.index_id   = i.index_id
              AND ius.database_id = DB_ID()
        WHERE OBJECTPROPERTY(i.object_id, 'IsUserTable') = 1
          AND i.type_desc NOT IN ('HEAP','CLUSTERED')
          AND i.is_primary_key       = 0
          AND i.is_unique_constraint = 0
          AND ISNULL(ius.user_seeks,   0) = 0
          AND ISNULL(ius.user_scans,   0) = 0
          AND ISNULL(ius.user_lookups, 0) = 0
          AND ISNULL(ius.user_updates, 0) > 0
        ORDER BY [Write Cost] DESC
        """
        try:
            return self.db.execute_query(sql)
        except Exception as exc:
            return pd.DataFrame({"Error": [str(exc)]})

    # ── Duplicate indexes (identical key columns) ─────────────────────────
    def get_duplicate_indexes(self) -> pd.DataFrame:
        sql = """
        WITH IndexKeys AS (
            SELECT
                i.object_id,
                i.index_id,
                i.name AS index_name,
                STRING_AGG(c.name, ', ')
                    WITHIN GROUP (ORDER BY ic.key_ordinal) AS key_cols
            FROM sys.indexes       i
            JOIN sys.index_columns ic ON ic.object_id = i.object_id
                                     AND ic.index_id  = i.index_id
            JOIN sys.columns        c ON  c.object_id = i.object_id
                                     AND  c.column_id = ic.column_id
            WHERE OBJECTPROPERTY(i.object_id,'IsUserTable') = 1
              AND i.type_desc != 'HEAP'
              AND ic.is_included_column = 0
            GROUP BY i.object_id, i.index_id, i.name
        )
        SELECT
            OBJECT_SCHEMA_NAME(a.object_id) AS [Schema],
            OBJECT_NAME(a.object_id)         AS [Table],
            a.index_name                     AS [Index 1],
            b.index_name                     AS [Index 2],
            a.key_cols                       AS [Duplicate Key Columns]
        FROM IndexKeys a
        JOIN IndexKeys b ON a.object_id = b.object_id
                        AND a.index_id  < b.index_id
                        AND a.key_cols  = b.key_cols
        ORDER BY [Schema], [Table]
        """
        try:
            return self.db.execute_query(sql)
        except Exception as exc:
            return pd.DataFrame({"Error": [str(exc)]})

    # ── Apply a CREATE INDEX (user must explicitly confirm in UI) ─────────
    def apply_index(self, create_index_sql: str) -> str:
        return self.db.execute_ddl(create_index_sql)
