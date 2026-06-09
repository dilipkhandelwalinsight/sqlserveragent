"""
SQL Server Infrastructure Monitor
Agent Jobs · Backup Status · Server Config · Linked Servers
"""
import pandas as pd


class ServerMonitor:
    """SQL Server infrastructure and operational monitoring."""

    def __init__(self, db):
        self.db = db

    def _q(self, sql: str) -> pd.DataFrame:
        try:
            return self.db.execute_query(sql)
        except Exception as ex:
            return pd.DataFrame([{"Error": str(ex)}])

    def get_server_properties(self) -> pd.DataFrame:
        return self._q("""
        SELECT
            @@SERVERNAME                                         AS [Server Name],
            CAST(SERVERPROPERTY('ProductVersion') AS NVARCHAR)   AS [SQL Version],
            CAST(SERVERPROPERTY('ProductLevel')   AS NVARCHAR)   AS [Service Pack],
            CAST(SERVERPROPERTY('Edition')        AS NVARCHAR)   AS [Edition],
            CAST(SERVERPROPERTY('Collation')      AS NVARCHAR)   AS [Collation],
            CAST(SERVERPROPERTY('IsClustered')    AS NVARCHAR)   AS [Clustered],
            CAST(SERVERPROPERTY('IsHadrEnabled')  AS NVARCHAR)   AS [Always On],
            CAST(SERVERPROPERTY('IsFullTextInstalled') AS NVARCHAR) AS [Full Text],
            (SELECT COUNT(*) FROM sys.databases)                 AS [Total Databases],
            (SELECT COUNT(*) FROM sys.databases WHERE state = 0) AS [Online DBs],
            @@MAX_CONNECTIONS                                    AS [Max Connections]
        """)

    def get_agent_jobs(self) -> pd.DataFrame:
        return self._q("""
        SELECT
            j.name                                               AS [Job Name],
            ISNULL(cat.name, 'Uncategorized')                    AS [Category],
            CASE j.enabled WHEN 1 THEN 'Enabled' ELSE 'Disabled' END AS [Status],
            CASE jh.run_status
                WHEN 0 THEN 'Failed'
                WHEN 1 THEN 'Succeeded'
                WHEN 2 THEN 'Retry'
                WHEN 3 THEN 'Cancelled'
                WHEN 4 THEN 'In Progress'
                ELSE        'Never Run'
            END AS [Last Outcome],
            CASE
                WHEN jh.run_date IS NULL THEN NULL
                ELSE CAST(
                    CAST(jh.run_date AS VARCHAR(8)) + ' ' +
                    RIGHT('0' + CAST(jh.run_time / 10000       AS VARCHAR), 2) + ':' +
                    RIGHT('0' + CAST(jh.run_time / 100 % 100   AS VARCHAR), 2) + ':' +
                    RIGHT('0' + CAST(jh.run_time % 100         AS VARCHAR), 2)
                    AS DATETIME)
            END AS [Last Run],
            CONVERT(VARCHAR,
                DATEADD(SECOND,
                    ISNULL(jh.run_duration % 100, 0) +
                    ISNULL((jh.run_duration / 100 % 100) * 60, 0) +
                    ISNULL((jh.run_duration / 10000) * 3600, 0),
                    0), 108) AS [Last Duration],
            j.date_created                                       AS [Created],
            j.date_modified                                      AS [Modified]
        FROM msdb.dbo.sysjobs j
        LEFT JOIN msdb.dbo.syscategories cat ON cat.category_id = j.category_id
        LEFT JOIN (
            SELECT job_id, MAX(instance_id) AS last_inst
            FROM msdb.dbo.sysjobhistory
            WHERE step_id = 0
            GROUP BY job_id
        ) li ON li.job_id = j.job_id
        LEFT JOIN msdb.dbo.sysjobhistory jh
            ON jh.job_id = li.job_id AND jh.instance_id = li.last_inst
        ORDER BY j.name
        """)

    def get_job_history(self, limit: int = 50) -> pd.DataFrame:
        return self._q(f"""
        SELECT TOP {limit}
            j.name AS [Job],
            jh.step_name AS [Step],
            CASE jh.run_status
                WHEN 0 THEN 'Failed'
                WHEN 1 THEN 'Succeeded'
                WHEN 2 THEN 'Retry'
                WHEN 3 THEN 'Cancelled'
                ELSE 'Unknown'
            END AS [Status],
            CAST(
                CAST(jh.run_date AS VARCHAR(8)) + ' ' +
                RIGHT('0' + CAST(jh.run_time / 10000       AS VARCHAR), 2) + ':' +
                RIGHT('0' + CAST(jh.run_time / 100 % 100   AS VARCHAR), 2) + ':' +
                RIGHT('0' + CAST(jh.run_time % 100         AS VARCHAR), 2)
                AS DATETIME) AS [Run Time],
            CONVERT(VARCHAR,
                DATEADD(SECOND,
                    jh.run_duration % 100 +
                    (jh.run_duration / 100 % 100) * 60 +
                    (jh.run_duration / 10000) * 3600,
                    0), 108) AS [Duration],
            LEFT(jh.message, 200) AS [Message]
        FROM msdb.dbo.sysjobhistory jh
        JOIN msdb.dbo.sysjobs j ON j.job_id = jh.job_id
        WHERE jh.step_id = 0
        ORDER BY jh.instance_id DESC
        """)

    def get_backup_status(self) -> pd.DataFrame:
        return self._q("""
        SELECT
            d.name                                               AS [Database],
            d.recovery_model_desc                                AS [Recovery Model],
            d.state_desc                                         AS [State],
            CASE
                WHEN bs_f.backup_finish_date IS NULL
                    THEN 'NEVER BACKED UP'
                WHEN DATEDIFF(DAY, bs_f.backup_finish_date, GETDATE()) > 7
                    THEN 'OVERDUE - ' +
                         CAST(DATEDIFF(DAY, bs_f.backup_finish_date, GETDATE()) AS VARCHAR) +
                         ' days ago'
                WHEN DATEDIFF(DAY, bs_f.backup_finish_date, GETDATE()) > 1
                    THEN CAST(DATEDIFF(DAY, bs_f.backup_finish_date, GETDATE()) AS VARCHAR) +
                         ' days ago'
                ELSE 'Recent'
            END AS [Full Backup Status],
            CONVERT(VARCHAR, bs_f.backup_finish_date, 120)       AS [Last Full Backup],
            CONVERT(VARCHAR, bs_l.backup_finish_date, 120)       AS [Last Log Backup],
            CAST(ISNULL(bs_f.backup_size, 0) / 1073741824.0 AS DECIMAL(10,2)) AS [Backup Size GB]
        FROM sys.databases d
        LEFT JOIN (
            SELECT database_name,
                   MAX(backup_finish_date) AS backup_finish_date,
                   MAX(backup_size)        AS backup_size
            FROM msdb.dbo.backupset
            WHERE type = 'D'
            GROUP BY database_name
        ) bs_f ON bs_f.database_name = d.name
        LEFT JOIN (
            SELECT database_name, MAX(backup_finish_date) AS backup_finish_date
            FROM msdb.dbo.backupset
            WHERE type = 'L'
            GROUP BY database_name
        ) bs_l ON bs_l.database_name = d.name
        WHERE d.database_id > 4
          AND d.state = 0
        ORDER BY bs_f.backup_finish_date ASC
        """)

    def get_database_sizes(self) -> pd.DataFrame:
        return self._q("""
        SELECT
            d.name                                               AS [Database],
            d.recovery_model_desc                                AS [Recovery],
            d.state_desc                                         AS [State],
            d.compatibility_level                                AS [Compat Level],
            CAST(SUM(CASE mf.type WHEN 0 THEN mf.size * 8.0 / 1024 ELSE 0 END) AS DECIMAL(12,2))
                AS [Data MB],
            CAST(SUM(CASE mf.type WHEN 1 THEN mf.size * 8.0 / 1024 ELSE 0 END) AS DECIMAL(12,2))
                AS [Log MB],
            CAST(SUM(mf.size * 8.0 / 1024) AS DECIMAL(12,2))    AS [Total MB],
            d.create_date                                        AS [Created]
        FROM sys.databases d
        JOIN sys.master_files mf ON mf.database_id = d.database_id
        WHERE d.database_id > 0
        GROUP BY d.name, d.recovery_model_desc, d.state_desc,
                 d.compatibility_level, d.create_date
        ORDER BY SUM(mf.size) DESC
        """)

    def get_server_config(self) -> pd.DataFrame:
        return self._q("""
        SELECT
            name             AS [Configuration Option],
            description      AS [Description],
            value            AS [Configured Value],
            value_in_use     AS [Running Value],
            minimum          AS [Min],
            maximum          AS [Max],
            CASE is_dynamic  WHEN 1 THEN 'Yes' ELSE 'No' END AS [Dynamic],
            CASE is_advanced WHEN 1 THEN 'Yes' ELSE 'No' END AS [Advanced]
        FROM sys.configurations
        ORDER BY name
        """)

    def get_linked_servers(self) -> pd.DataFrame:
        return self._q("""
        SELECT
            s.name                                               AS [Linked Server],
            s.provider                                           AS [Provider],
            s.product                                            AS [Product],
            s.data_source                                        AS [Data Source],
            CASE s.is_linked               WHEN 1 THEN 'Yes' ELSE 'No' END AS [Is Linked],
            CASE s.is_remote_login_enabled WHEN 1 THEN 'Yes' ELSE 'No' END AS [Remote Login],
            s.modify_date                                        AS [Modified],
            ISNULL(s.description, '')                            AS [Description]
        FROM sys.servers s
        WHERE s.is_linked = 1
        ORDER BY s.name
        """)
