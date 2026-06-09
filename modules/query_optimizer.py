import pandas as pd

_IDLE_WAITS = (
    "'SLEEP_TASK','BROKER_TO_FLUSH','BROKER_TASK_STOP','CLR_AUTO_EVENT',"
    "'DISPATCHER_QUEUE_SEMAPHORE','FT_IFTS_SCHEDULER_IDLE_WAIT',"
    "'HADR_FILESTREAM_IOMGR_IOCOMPLETION','HADR_WORK_QUEUE',"
    "'LAZYWRITER_SLEEP','LOGMGR_QUEUE','ONDEMAND_TASK_QUEUE',"
    "'REQUEST_FOR_DEADLOCK_SEARCH','RESOURCE_QUEUE','SERVER_IDLE_CHECK',"
    "'SLEEP_DBSTARTUP','SLEEP_DCOMSTARTUP','SLEEP_MASTERDBREADY',"
    "'SLEEP_MASTERMDREADY','SLEEP_MASTERUPGRADED','SLEEP_MSDBSTARTUP',"
    "'SLEEP_SYSTEMTASK','SLEEP_TEMPDBSTARTUP','SNI_HTTP_ACCEPT',"
    "'SP_SERVER_DIAGNOSTICS_SLEEP','SQLTRACE_BUFFER_FLUSH',"
    "'SQLTRACE_INCREMENTAL_FLUSH_SLEEP','WAITFOR','XE_DISPATCHER_WAIT',"
    "'XE_TIMER_EVENT','BROKER_EVENTHANDLER','CHECKPOINT_QUEUE',"
    "'DBMIRROR_EVENTS_QUEUE','SQLTRACE_WAIT_ENTRIES',"
    "'WAIT_XTP_OFFLINE_CKPT_NEW_LOG'"
)


class QueryOptimizer:
    """SQL Server query performance analysis via DMVs."""

    def __init__(self, db):
        self.db = db

    def _q(self, sql: str) -> pd.DataFrame:
        try:
            return self.db.execute_query(sql)
        except Exception as ex:
            return pd.DataFrame([{"Error": str(ex)}])

    def get_top_cpu(self) -> pd.DataFrame:
        return self._q("""
        SELECT TOP 20
            qs.execution_count                                  AS [Executions],
            qs.total_worker_time/qs.execution_count/1000        AS [Avg CPU (ms)],
            qs.total_worker_time/1000                           AS [Total CPU (ms)],
            qs.total_elapsed_time/qs.execution_count/1000       AS [Avg Duration (ms)],
            qs.total_logical_reads/qs.execution_count           AS [Avg Reads],
            qs.last_execution_time                              AS [Last Run],
            DB_NAME(qp.dbid)                                    AS [Database],
            LEFT(REPLACE(REPLACE(st.text,CHAR(13),' '),CHAR(10),' '),200) AS [Query]
        FROM sys.dm_exec_query_stats qs
        CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) st
        CROSS APPLY sys.dm_exec_query_plan(qs.plan_handle) qp
        WHERE qs.execution_count > 0
        ORDER BY qs.total_worker_time DESC
        """)

    def get_top_io(self) -> pd.DataFrame:
        return self._q("""
        SELECT TOP 20
            qs.execution_count                                  AS [Executions],
            qs.total_logical_reads/qs.execution_count           AS [Avg Logical Reads],
            qs.total_physical_reads/qs.execution_count          AS [Avg Physical Reads],
            qs.total_logical_writes/qs.execution_count          AS [Avg Writes],
            qs.total_worker_time/qs.execution_count/1000        AS [Avg CPU (ms)],
            qs.last_execution_time                              AS [Last Run],
            DB_NAME(qp.dbid)                                    AS [Database],
            LEFT(REPLACE(REPLACE(st.text,CHAR(13),' '),CHAR(10),' '),200) AS [Query]
        FROM sys.dm_exec_query_stats qs
        CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) st
        CROSS APPLY sys.dm_exec_query_plan(qs.plan_handle) qp
        WHERE qs.execution_count > 0
        ORDER BY qs.total_logical_reads DESC
        """)

    def get_blocking(self) -> pd.DataFrame:
        return self._q("""
        SELECT
            r.session_id                AS [Session],
            r.blocking_session_id       AS [Blocked By],
            r.wait_type                 AS [Wait Type],
            r.wait_time/1000.0          AS [Wait (sec)],
            r.status                    AS [Status],
            DB_NAME(r.database_id)      AS [Database],
            s.login_name                AS [Login],
            s.host_name                 AS [Host],
            s.program_name              AS [App],
            LEFT(st.text, 300)          AS [Current SQL],
            r.cpu_time                  AS [CPU (ms)],
            r.reads                     AS [Reads],
            r.writes                    AS [Writes]
        FROM sys.dm_exec_requests r
        JOIN sys.dm_exec_sessions s ON r.session_id = s.session_id
        CROSS APPLY sys.dm_exec_sql_text(r.sql_handle) st
        WHERE r.blocking_session_id > 0
        ORDER BY r.wait_time DESC
        """)

    def get_long_running(self, threshold_sec: int = 5) -> pd.DataFrame:
        return self._q(f"""
        SELECT
            r.session_id                 AS [Session],
            r.status                     AS [Status],
            r.wait_type                  AS [Wait Type],
            r.wait_time/1000.0           AS [Wait (sec)],
            r.total_elapsed_time/1000.0  AS [Elapsed (sec)],
            r.cpu_time                   AS [CPU (ms)],
            r.reads                      AS [Reads],
            r.writes                     AS [Writes],
            DB_NAME(r.database_id)       AS [Database],
            s.login_name                 AS [Login],
            s.host_name                  AS [Host],
            LEFT(st.text, 300)           AS [Query]
        FROM sys.dm_exec_requests r
        JOIN sys.dm_exec_sessions s ON r.session_id = s.session_id
        CROSS APPLY sys.dm_exec_sql_text(r.sql_handle) st
        WHERE r.session_id != @@SPID
          AND r.total_elapsed_time/1000.0 >= {threshold_sec}
          AND s.is_user_process = 1
        ORDER BY r.total_elapsed_time DESC
        """)

    def get_wait_stats(self) -> pd.DataFrame:
        return self._q(f"""
        SELECT TOP 15
            wait_type               AS [Wait Type],
            waiting_tasks_count     AS [Tasks],
            wait_time_ms            AS [Total Wait (ms)],
            max_wait_time_ms        AS [Max Wait (ms)],
            CAST(100.0 * wait_time_ms / NULLIF(SUM(wait_time_ms) OVER(),0)
                 AS DECIMAL(5,2))  AS [%],
            CASE
                WHEN wait_type LIKE 'PAGEIOLATCH%'           THEN 'I/O Bottleneck'
                WHEN wait_type LIKE 'LCK_%'                  THEN 'Lock Contention'
                WHEN wait_type IN ('CXPACKET','CXCONSUMER')  THEN 'Parallelism'
                WHEN wait_type = 'SOS_SCHEDULER_YIELD'       THEN 'CPU Pressure'
                WHEN wait_type LIKE 'RESOURCE_SEMAPHORE%'    THEN 'Memory Pressure'
                ELSE 'Other'
            END AS [Category]
        FROM sys.dm_os_wait_stats
        WHERE wait_type NOT IN ({_IDLE_WAITS})
          AND wait_time_ms > 0
        ORDER BY wait_time_ms DESC
        """)

    def get_fragmentation(self) -> pd.DataFrame:
        return self._q("""
        SELECT TOP 30
            OBJECT_SCHEMA_NAME(ps.object_id)  AS [Schema],
            OBJECT_NAME(ps.object_id)          AS [Table],
            i.name                             AS [Index],
            i.type_desc                        AS [Type],
            CAST(ps.avg_fragmentation_in_percent AS DECIMAL(5,1)) AS [Frag %],
            ps.page_count                      AS [Pages],
            ps.record_count                    AS [Records],
            CASE
                WHEN ps.avg_fragmentation_in_percent < 10  THEN '✅ OK'
                WHEN ps.avg_fragmentation_in_percent < 30  THEN '🟡 Reorganize'
                ELSE '🔴 Rebuild'
            END AS [Action]
        FROM sys.dm_db_index_physical_stats(DB_ID(), NULL, NULL, NULL, 'SAMPLED') ps
        JOIN sys.indexes i ON i.object_id = ps.object_id AND i.index_id = ps.index_id
        WHERE ps.index_id > 0 AND ps.page_count > 100
        ORDER BY ps.avg_fragmentation_in_percent DESC
        """)
