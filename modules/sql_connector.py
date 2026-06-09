import re
import pyodbc
import pandas as pd
from typing import Tuple, Any

# DML/DDL keywords that are never allowed as statement starters
_BLOCKED_STARTERS = {
    'DROP', 'TRUNCATE', 'DELETE', 'UPDATE', 'INSERT',
    'ALTER', 'EXEC', 'EXECUTE', 'BULK',
}
# CREATE is blocked EXCEPT when it's "CREATE INDEX"
_BLOCKED_CREATE = True


def _is_write_sql(sql: str) -> bool:
    """Return True if sql contains any write/destructive statement.

    Only checks the *first keyword of each semicolon-separated statement*
    to avoid false positives from column aliases like AS [On Update].
    """
    # Strip single-line comments
    sql_stripped = re.sub(r'--[^\n]*', ' ', sql)
    # Strip block comments
    sql_stripped = re.sub(r'/\*.*?\*/', ' ', sql_stripped, flags=re.DOTALL)
    # Strip quoted identifiers and string literals to avoid matching inside them
    sql_stripped = re.sub(r'\[.*?\]', ' IDENTIFIER ', sql_stripped)
    sql_stripped = re.sub(r"'[^']*'", " STRING ", sql_stripped)

    for statement in sql_stripped.split(';'):
        tokens = statement.split()
        if not tokens:
            continue
        first = tokens[0].upper()
        if first in _BLOCKED_STARTERS:
            return True
        if first == 'CREATE':
            # Allow CREATE INDEX, block everything else
            second = tokens[1].upper() if len(tokens) > 1 else ''
            third  = tokens[2].upper() if len(tokens) > 2 else ''
            if second in ('INDEX',):
                continue
            if second in ('NONCLUSTERED', 'CLUSTERED', 'UNIQUE') and third == 'INDEX':
                continue
            return True
        # Also catch xp_cmdshell anywhere (it's always dangerous)
        if re.search(r'\bxp_cmdshell\b', statement, re.IGNORECASE):
            return True
    return False


class SQLConnector:
    """Thin wrapper around pyodbc for SQL Server — READ-ONLY by default."""

    def __init__(self, connection_string: str):
        self.raw_cs = connection_string
        self.connection_string = self._normalize(connection_string)

    # ── normalise ADO.NET → ODBC ──────────────────────────────────────────
    def _normalize(self, cs: str) -> str:
        if re.search(r'Driver\s*=', cs, re.IGNORECASE):
            return cs                                   # already ODBC style

        replacements = {
            r'Integrated Security\s*=\s*(True|SSPI|Yes)': 'Trusted_Connection=yes',
            r'User Id\s*=': 'UID=',
            r'Password\s*=': 'PWD=',
            r'\bDatabase\s*=': 'DATABASE=',
            r'\bServer\s*=': 'SERVER=',
            r'\bData Source\s*=': 'SERVER=',
            r'\bInitial Catalog\s*=': 'DATABASE=',
        }
        for pattern, repl in replacements.items():
            cs = re.sub(pattern, repl, cs, flags=re.IGNORECASE)

        return f"Driver={{ODBC Driver 17 for SQL Server}};{cs}"

    # ── connectivity test ─────────────────────────────────────────────────
    def test_connection(self) -> Tuple[bool, Any]:
        conn = None
        try:
            conn = pyodbc.connect(self.connection_string, timeout=15)
            row = conn.execute(
                "SELECT @@SERVERNAME AS s, DB_NAME() AS d, "
                "SYSTEM_USER AS u, LEFT(@@VERSION,100) AS v"
            ).fetchone()
            return True, {
                "server": row.s, "database": row.d,
                "user": row.u, "version": row.v,
            }
        except Exception as exc:
            return False, str(exc)
        finally:
            if conn:
                conn.close()

    # ── read-only query ───────────────────────────────────────────────────
    def execute_query(self, sql: str) -> pd.DataFrame:
        if _is_write_sql(sql):
            raise PermissionError(
                "🚫 BLOCKED — Agent operates in READ-ONLY mode. "
                "Destructive/write commands are not permitted."
            )
        conn = None
        try:
            conn = pyodbc.connect(self.connection_string, timeout=60)
            return pd.read_sql(sql, conn)
        finally:
            if conn:
                conn.close()

    # ── DML (INSERT/UPDATE/DELETE) — explicit user approval required ─────
    def execute_dml(self, sql: str) -> str:
        """Execute approved DML statement. Only INSERT, UPDATE, DELETE allowed.
        Called only after explicit confirmation in the UI approval workflow.
        """
        tokens = sql.strip().split()
        if not tokens:
            raise PermissionError("Empty statement.")
        first = tokens[0].upper()
        if first not in ("INSERT", "UPDATE", "DELETE"):
            raise PermissionError(
                "execute_dml() only permits INSERT, UPDATE, or DELETE statements."
            )
        conn = None
        try:
            conn = pyodbc.connect(self.connection_string, timeout=120)
            cursor = conn.cursor()
            cursor.execute(sql.strip())
            rows = cursor.rowcount
            conn.commit()
            return f"✅ Success — {rows} row(s) affected."
        except Exception as exc:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            return f"❌ Failed: {exc}"
        finally:
            if conn:
                conn.close()

    # ── DDL (CREATE INDEX only) — requires explicit user approval ─────────
    def execute_ddl(self, sql: str) -> str:
        if not re.match(
            r'\s*CREATE\s+(NONCLUSTERED\s+|CLUSTERED\s+)?INDEX\s+',
            sql, re.IGNORECASE
        ):
            raise PermissionError(
                "Only CREATE INDEX statements are permitted via this method."
            )
        conn = None
        try:
            conn = pyodbc.connect(self.connection_string, timeout=120)
            conn.execute(sql)
            conn.commit()
            return "✅ Index created successfully."
        except Exception as exc:
            return f"❌ Failed: {exc}"
        finally:
            if conn:
                conn.close()
