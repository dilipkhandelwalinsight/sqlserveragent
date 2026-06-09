import pandas as pd
from typing import Dict, Any

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


class HealthMonitor:
    """SQL Server health metrics via DMVs."""

    def __init__(self, db):
        self.db = db

    def _q(self, sql: str) -> pd.DataFrame:
        try:
            return self.db.execute_query(sql)
        except Exception as ex:
            return pd.DataFrame([{"Error": str(ex)}])

    def get_active_connections(self) -> pd.DataFrame:
        return self._q("""
        SELECT
            s.session_id                                    AS [SID],
            s.login_name                                    AS [Login],
            s.host_name                                     AS [Host],
            s.program_name                                  AS [Program],
            DB_NAME(s.database_id)                          AS [Database],
            s.status                                        AS [Status],
            s.cpu_time                                      AS [CPU (ms)],
            s.memory_usage * 8                              AS [Memory KB],
            s.reads                                         AS [Reads],
            s.writes                                        AS [Writes],
            s.logical_reads                                 AS [Logical Reads],
            CONVERT(VARCHAR,s.login_time,120)               AS [Login Time],
            CONVERT(VARCHAR,s.last_request_start_time,120)  AS [Last Request]
        FROM sys.dm_exec_sessions s
        WHERE s.is_user_process = 1
        ORDER BY s.cpu_time DESC
        """)

    def get_wait_stats(self) -> pd.DataFrame:
        return self._q(f"""
        SELECT TOP 20
            wait_type               AS [Wait Type],
            waiting_tasks_count     AS [Tasks],
            wait_time_ms            AS [Total Wait (ms)],
            max_wait_time_ms        AS [Max Wait (ms)],
            CAST(100.0 * wait_time_ms / NULLIF(SUM(wait_time_ms) OVER(),0)
                 AS DECIMAL(5,2))  AS [% Total],
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

    def get_blocking(self) -> pd.DataFrame:
        return self._q("""
        SELECT
            r.session_id                AS [Session],
            r.blocking_session_id       AS [Blocked By],
            r.wait_type                 AS [Wait Type],
            r.wait_time / 1000.0        AS [Wait (sec)],
            r.status                    AS [Status],
            DB_NAME(r.database_id)      AS [Database],
            s.login_name                AS [Login],
            s.host_name                 AS [Host],
            LEFT(st.text, 200)          AS [Query],
            r.cpu_time                  AS [CPU (ms)],
            r.reads                     AS [Reads]
        FROM sys.dm_exec_requests r
        JOIN sys.dm_exec_sessions s ON r.session_id = s.session_id
        CROSS APPLY sys.dm_exec_sql_text(r.sql_handle) st
        WHERE r.blocking_session_id > 0
        ORDER BY r.wait_time DESC
        """)

    def get_disk_io(self) -> pd.DataFrame:
        return self._q("""
        SELECT
            DB_NAME(f.database_id)       AS [Database],
            mf.name                      AS [Logical File],
            mf.type_desc                 AS [File Type],
            f.num_of_reads               AS [Reads],
            f.num_of_writes              AS [Writes],
            f.io_stall_read_ms           AS [Read Stall (ms)],
            f.io_stall_write_ms          AS [Write Stall (ms)],
            f.io_stall                   AS [Total Stall (ms)],
            CASE WHEN f.num_of_reads  = 0 THEN 0
                 ELSE f.io_stall_read_ms  / f.num_of_reads  END AS [Avg Read (ms)],
            CASE WHEN f.num_of_writes = 0 THEN 0
                 ELSE f.io_stall_write_ms / f.num_of_writes END AS [Avg Write (ms)],
            f.size_on_disk_bytes / 1048576 AS [Size (MB)]
        FROM sys.dm_io_virtual_file_stats(NULL, NULL) f
        JOIN sys.master_files mf
             ON mf.database_id = f.database_id AND mf.file_id = f.file_id
        ORDER BY f.io_stall DESC
        """)

    def get_memory_usage(self) -> pd.DataFrame:
        return self._q("""
        SELECT TOP 15
            type                    AS [Clerk],
            SUM(pages_kb) / 1024    AS [Memory (MB)],
            SUM(pages_kb)           AS [Memory (KB)]
        FROM sys.dm_os_memory_clerks
        GROUP BY type
        ORDER BY SUM(pages_kb) DESC
        """)

    def get_top_queries(self) -> pd.DataFrame:
        return self._q("""
        SELECT TOP 20
            qs.execution_count                                 AS [Executions],
            qs.total_worker_time/qs.execution_count/1000       AS [Avg CPU (ms)],
            qs.total_elapsed_time/qs.execution_count/1000      AS [Avg Duration (ms)],
            qs.total_logical_reads/qs.execution_count          AS [Avg Reads],
            qs.last_execution_time                             AS [Last Run],
            DB_NAME(qp.dbid)                                   AS [Database],
            LEFT(REPLACE(REPLACE(st.text,CHAR(13),' '),CHAR(10),' '),200) AS [Query]
        FROM sys.dm_exec_query_stats qs
        CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) st
        CROSS APPLY sys.dm_exec_query_plan(qs.plan_handle) qp
        WHERE qs.execution_count > 0
        ORDER BY qs.total_worker_time DESC
        """)

    def get_health_score(self) -> Dict[str, Any]:
        """Compute a 0-100 health score from live DMV data."""
        score = 100
        issues: list = []
        warnings: list = []

        try:
            b = self.get_blocking()
            if not b.empty and "Error" not in b.columns:
                n = len(b)
                if n > 5:
                    score -= 20
                    issues.append(f"{n} active blocking sessions detected")
                elif n > 0:
                    score -= 10
                    warnings.append(f"{n} blocking session(s)")
        except Exception:
            pass

        try:
            w = self.get_wait_stats()
            if not w.empty and "Error" not in w.columns:
                cat = w.iloc[0].get("Category", "")
                wt  = w.iloc[0].get("Wait Type", "")
                if cat in ("I/O Bottleneck", "Lock Contention", "Memory Pressure"):
                    score -= 15
                    issues.append(f"Top wait: {cat} ({wt})")
                elif cat in ("CPU Pressure", "Parallelism"):
                    score -= 10
                    warnings.append(f"Top wait category: {cat} ({wt})")
        except Exception:
            pass

        score = max(0, score)
        grade = "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D" if score >= 40 else "F"
        color = "#1a7f37" if score >= 90 else "#1f6feb" if score >= 75 else "#9a6700" if score >= 60 else "#cf222e"
        return {
            "score": score, "grade": grade, "color": color,
            "issues": issues, "warnings": warnings,
        }
