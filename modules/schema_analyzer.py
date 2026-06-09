import pandas as pd
from .sql_connector import SQLConnector


class SchemaAnalyzer:
    def __init__(self, connector: SQLConnector):
        self.db = connector

    # ── Tables & Views ────────────────────────────────────────────────────
    def get_tables(self) -> pd.DataFrame:
        sql = """
        SELECT
            t.TABLE_SCHEMA               AS [Schema],
            t.TABLE_NAME                 AS [Table],
            t.TABLE_TYPE                 AS [Type],
            CAST(ISNULL(SUM(p.rows),0) AS BIGINT) AS [Row Count]
        FROM INFORMATION_SCHEMA.TABLES t
        LEFT JOIN sys.tables  st ON st.name = t.TABLE_NAME
              AND SCHEMA_NAME(st.schema_id) = t.TABLE_SCHEMA
        LEFT JOIN sys.partitions p ON p.object_id = st.object_id
              AND p.index_id IN (0,1)
        GROUP BY t.TABLE_SCHEMA, t.TABLE_NAME, t.TABLE_TYPE
        ORDER BY t.TABLE_SCHEMA, t.TABLE_NAME
        """
        return self.db.execute_query(sql)

    # ── Columns with PK indicator ─────────────────────────────────────────
    def get_columns(self, schema: str = None, table: str = None) -> pd.DataFrame:
        where = "1=1"
        if schema:
            where += f" AND c.TABLE_SCHEMA = '{schema.replace(chr(39), '')}'"
        if table:
            where += f" AND c.TABLE_NAME  = '{table.replace(chr(39), '')}'"

        sql = f"""
        SELECT
            c.TABLE_SCHEMA  AS [Schema],
            c.TABLE_NAME    AS [Table],
            c.COLUMN_NAME   AS [Column],
            c.ORDINAL_POSITION AS [Pos],
            c.DATA_TYPE     AS [Type],
            ISNULL(
                CAST(c.CHARACTER_MAXIMUM_LENGTH AS VARCHAR(20)),
                CASE WHEN c.NUMERIC_PRECISION IS NOT NULL
                     THEN CAST(c.NUMERIC_PRECISION AS VARCHAR(10)) +
                          ISNULL(',' + CAST(c.NUMERIC_SCALE AS VARCHAR(10)),'')
                     ELSE '' END
            ) AS [Size],
            c.IS_NULLABLE   AS [Nullable],
            ISNULL(c.COLUMN_DEFAULT,'') AS [Default],
            CASE WHEN pk.COLUMN_NAME IS NOT NULL THEN '🔑 PK' ELSE '' END AS [Key]
        FROM INFORMATION_SCHEMA.COLUMNS c
        LEFT JOIN (
            SELECT kcu.TABLE_SCHEMA, kcu.TABLE_NAME, kcu.COLUMN_NAME
            FROM   INFORMATION_SCHEMA.TABLE_CONSTRAINTS  tc
            JOIN   INFORMATION_SCHEMA.KEY_COLUMN_USAGE   kcu
                   ON  kcu.CONSTRAINT_NAME = tc.CONSTRAINT_NAME
                   AND kcu.TABLE_SCHEMA    = tc.TABLE_SCHEMA
            WHERE  tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
        ) pk ON pk.TABLE_SCHEMA = c.TABLE_SCHEMA
            AND pk.TABLE_NAME   = c.TABLE_NAME
            AND pk.COLUMN_NAME  = c.COLUMN_NAME
        WHERE {where}
        ORDER BY c.TABLE_SCHEMA, c.TABLE_NAME, c.ORDINAL_POSITION
        """
        return self.db.execute_query(sql)

    # ── Foreign Keys ──────────────────────────────────────────────────────
    def get_relationships(self) -> pd.DataFrame:
        sql = """
        SELECT
            fk.name                                               AS [FK Name],
            OBJECT_SCHEMA_NAME(fk.parent_object_id)              AS [Parent Schema],
            OBJECT_NAME(fk.parent_object_id)                     AS [Parent Table],
            COL_NAME(fkc.parent_object_id, fkc.parent_column_id) AS [Parent Column],
            OBJECT_SCHEMA_NAME(fk.referenced_object_id)          AS [Ref Schema],
            OBJECT_NAME(fk.referenced_object_id)                 AS [Ref Table],
            COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id) AS [Ref Column],
            fk.delete_referential_action_desc AS [On Delete],
            fk.update_referential_action_desc AS [On Update]
        FROM sys.foreign_keys        fk
        JOIN sys.foreign_key_columns fkc ON fkc.constraint_object_id = fk.object_id
        ORDER BY [Parent Schema], [Parent Table], [FK Name]
        """
        return self.db.execute_query(sql)

    # ── Indexes ───────────────────────────────────────────────────────────
    def get_indexes(self, table: str = None) -> pd.DataFrame:
        extra = f"AND OBJECT_NAME(i.object_id) = '{table}'" if table else ""
        sql = f"""
        SELECT
            OBJECT_SCHEMA_NAME(i.object_id)  AS [Schema],
            OBJECT_NAME(i.object_id)          AS [Table],
            i.name                            AS [Index Name],
            i.type_desc                       AS [Type],
            CASE i.is_unique        WHEN 1 THEN 'Yes' ELSE 'No' END AS [Unique],
            CASE i.is_primary_key   WHEN 1 THEN 'Yes' ELSE 'No' END AS [PK],
            STRING_AGG(
                c.name + CASE ic.is_descending_key WHEN 1 THEN ' DESC' ELSE ' ASC' END,
                ', '
            ) WITHIN GROUP (ORDER BY ic.key_ordinal) AS [Key Columns]
        FROM sys.indexes       i
        JOIN sys.index_columns ic ON ic.object_id = i.object_id AND ic.index_id = i.index_id
        JOIN sys.columns        c ON  c.object_id = i.object_id AND  c.column_id = ic.column_id
        WHERE OBJECTPROPERTY(i.object_id,'IsUserTable') = 1
          AND i.type_desc  != 'HEAP'
          AND ic.is_included_column = 0
          {extra}
        GROUP BY i.object_id, i.name, i.type_desc, i.is_unique, i.is_primary_key
        ORDER BY [Schema], [Table], [Index Name]
        """
        return self.db.execute_query(sql)

    # ── Stored procedures ─────────────────────────────────────────────────
    def get_stored_procedures(self) -> pd.DataFrame:
        sql = """
        SELECT
            ROUTINE_SCHEMA AS [Schema],
            ROUTINE_NAME   AS [Procedure],
            CREATED        AS [Created],
            LAST_ALTERED   AS [Last Modified]
        FROM INFORMATION_SCHEMA.ROUTINES
        WHERE ROUTINE_TYPE = 'PROCEDURE'
        ORDER BY ROUTINE_SCHEMA, ROUTINE_NAME
        """
        return self.db.execute_query(sql)

    def get_sp_definition(self, schema: str, name: str) -> str:
        safe = f"{schema}.{name}".replace("'", "")
        df = self.db.execute_query(
            f"SELECT OBJECT_DEFINITION(OBJECT_ID('{safe}')) AS def"
        )
        if not df.empty and df["def"].iloc[0]:
            return df["def"].iloc[0]
        return "-- Definition not available"

    # ── Compact schema summary for AI context ─────────────────────────────
    def get_schema_summary(self) -> str:
        try:
            tables  = self.get_tables()
            columns = self.get_columns()
            fks     = self.get_relationships()

            lines = ["DATABASE SCHEMA SUMMARY", "=" * 60, ""]
            for _, t in tables.iterrows():
                s, tbl, rows = t["Schema"], t["Table"], t["Row Count"]
                lines.append(f"TABLE [{s}].[{tbl}]  ({rows:,} rows)")

                tcols = columns[
                    (columns["Schema"] == s) & (columns["Table"] == tbl)
                ]
                for _, col in tcols.iterrows():
                    pk   = " [PK]" if "PK" in str(col["Key"]) else ""
                    size = f"({col['Size']})" if col["Size"] else ""
                    null = "" if col["Nullable"] == "YES" else " NOT NULL"
                    lines.append(
                        f"  · {col['Column']} {col['Type']}{size}{null}{pk}"
                    )

                if not fks.empty:
                    for _, fk in fks[fks["Parent Table"] == tbl].iterrows():
                        lines.append(
                            f"  FK {fk['Parent Column']} → "
                            f"[{fk['Ref Schema']}].[{fk['Ref Table']}]"
                            f".{fk['Ref Column']}"
                        )
                lines.append("")
            return "\n".join(lines)
        except Exception as exc:
            return f"Schema summary unavailable: {exc}"

    # ── Triggers ──────────────────────────────────────────────────────────
    def get_triggers(self) -> pd.DataFrame:
        sql = """
        SELECT
            OBJECT_SCHEMA_NAME(t.parent_id)  AS [Schema],
            OBJECT_NAME(t.parent_id)          AS [Table],
            t.name                            AS [Trigger],
            t.type_desc                       AS [Type],
            CASE t.is_disabled WHEN 1 THEN 'Disabled' ELSE 'Enabled' END AS [Status],
            STRING_AGG(te.type_desc, ', ')
                WITHIN GROUP (ORDER BY te.type_desc) AS [Events],
            t.create_date  AS [Created],
            t.modify_date  AS [Last Modified]
        FROM sys.triggers     t
        JOIN sys.trigger_events te ON te.object_id = t.object_id
        WHERE t.parent_class = 1   -- DML triggers only
        GROUP BY t.parent_id, t.name, t.type_desc, t.is_disabled,
                 t.create_date, t.modify_date
        ORDER BY [Schema],[Table],[Trigger]
        """
        return self.db.execute_query(sql)

    def get_trigger_definition(self, trigger_name: str) -> str:
        df = self.db.execute_query(
            f"SELECT OBJECT_DEFINITION(OBJECT_ID('{trigger_name}')) AS def"
        )
        if not df.empty and df["def"].iloc[0]:
            return df["def"].iloc[0]
        return "-- Definition not available"

    # ── User-Defined Functions ─────────────────────────────────────────────
    def get_functions(self) -> pd.DataFrame:
        sql = """
        SELECT
            ROUTINE_SCHEMA          AS [Schema],
            ROUTINE_NAME            AS [Function],
            ROUTINE_TYPE            AS [Routine Type],
            DATA_TYPE               AS [Return Type],
            SPECIFIC_CATALOG        AS [Database],
            CREATED                 AS [Created],
            LAST_ALTERED            AS [Last Modified]
        FROM INFORMATION_SCHEMA.ROUTINES
        WHERE ROUTINE_TYPE = 'FUNCTION'
        ORDER BY ROUTINE_SCHEMA, ROUTINE_NAME
        """
        return self.db.execute_query(sql)

    def get_function_definition(self, schema: str, name: str) -> str:
        safe = f"{schema}.{name}".replace("'", "")
        df = self.db.execute_query(
            f"SELECT OBJECT_DEFINITION(OBJECT_ID('{safe}')) AS def"
        )
        if not df.empty and df["def"].iloc[0]:
            return df["def"].iloc[0]
        return "-- Definition not available"

    # ── Views with definitions ─────────────────────────────────────────────
    def get_views(self) -> pd.DataFrame:
        sql = """
        SELECT
            v.TABLE_SCHEMA         AS [Schema],
            v.TABLE_NAME           AS [View],
            so.create_date         AS [Created],
            so.modify_date         AS [Last Modified],
            (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS c
             WHERE c.TABLE_SCHEMA = v.TABLE_SCHEMA
               AND c.TABLE_NAME   = v.TABLE_NAME) AS [Columns]
        FROM INFORMATION_SCHEMA.VIEWS v
        JOIN sys.objects so ON so.name = v.TABLE_NAME
                           AND SCHEMA_NAME(so.schema_id) = v.TABLE_SCHEMA
        ORDER BY v.TABLE_SCHEMA, v.TABLE_NAME
        """
        return self.db.execute_query(sql)

    def get_view_definition(self, schema: str, name: str) -> str:
        safe = f"{schema}.{name}".replace("'", "")
        df = self.db.execute_query(
            f"SELECT OBJECT_DEFINITION(OBJECT_ID('{safe}')) AS def"
        )
        if not df.empty and df["def"].iloc[0]:
            return df["def"].iloc[0]
        return "-- Definition not available"

    # ── Database-level statistics ─────────────────────────────────────────
    def get_database_stats(self) -> dict:
        sql = """
        SELECT
            (SELECT COUNT(*) FROM sys.tables   WHERE OBJECTPROPERTY(object_id,'IsUserTable')=1) AS tables,
            (SELECT COUNT(*) FROM sys.views    WHERE OBJECTPROPERTY(object_id,'IsView')=1)      AS views,
            (SELECT COUNT(*) FROM INFORMATION_SCHEMA.ROUTINES WHERE ROUTINE_TYPE='PROCEDURE')   AS procedures,
            (SELECT COUNT(*) FROM INFORMATION_SCHEMA.ROUTINES WHERE ROUTINE_TYPE='FUNCTION')    AS functions,
            (SELECT COUNT(*) FROM sys.triggers WHERE parent_class=1)                            AS triggers,
            (SELECT COUNT(*) FROM sys.indexes
             WHERE OBJECTPROPERTY(object_id,'IsUserTable')=1
               AND type_desc != 'HEAP')                                                          AS indexes,
            (SELECT COUNT(*) FROM sys.foreign_keys)                                              AS foreign_keys,
            DB_NAME()  AS db_name,
            @@SERVERNAME AS server_name
        """
        try:
            df = self.db.execute_query(sql)
            if not df.empty:
                return df.iloc[0].to_dict()
        except Exception:
            pass
        return {}

    def get_database_size(self) -> pd.DataFrame:
        sql = """
        SELECT
            name                                             AS [File Name],
            physical_name                                    AS [Path],
            type_desc                                        AS [Type],
            CAST(size * 8.0 / 1024 AS DECIMAL(10,2))        AS [Size MB],
            CAST(FILEPROPERTY(name,'SpaceUsed')*8.0/1024 AS DECIMAL(10,2)) AS [Used MB]
        FROM sys.database_files
        """
        return self.db.execute_query(sql)
