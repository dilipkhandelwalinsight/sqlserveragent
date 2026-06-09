"""
SQL Server Security Intelligence Module
Logins · Users · Roles · Permissions · Risk Analysis
"""
import pandas as pd


class SecurityCenter:
    """Security audit: logins, users, roles, permissions, risk flags."""

    def __init__(self, db):
        self.db = db

    def _q(self, sql: str) -> pd.DataFrame:
        try:
            return self.db.execute_query(sql)
        except Exception as ex:
            return pd.DataFrame([{"Error": str(ex)}])

    def get_server_logins(self) -> pd.DataFrame:
        return self._q("""
        SELECT
            sp.name                                              AS [Login Name],
            sp.type_desc                                         AS [Login Type],
            CASE sp.is_disabled WHEN 1 THEN 'Disabled' ELSE 'Enabled' END AS [Status],
            ISNULL(sp.default_database_name, 'N/A')              AS [Default DB],
            sp.create_date                                       AS [Created],
            sp.modify_date                                       AS [Modified],
            CASE sp.is_policy_checked     WHEN 1 THEN 'Yes' ELSE 'No' END AS [Policy Check],
            CASE sp.is_expiration_checked WHEN 1 THEN 'Yes' ELSE 'No' END AS [Expiry Check],
            (
                SELECT STRING_AGG(sr2.name, ', ')
                FROM sys.server_role_members srm2
                JOIN sys.server_principals sr2 ON sr2.principal_id = srm2.role_principal_id
                WHERE srm2.member_principal_id = sp.principal_id
            ) AS [Server Roles]
        FROM sys.server_principals sp
        WHERE sp.type IN ('S','U','G','E','X')
          AND sp.name NOT LIKE '##%'
        ORDER BY sp.type_desc, sp.name
        """)

    def get_database_users(self) -> pd.DataFrame:
        return self._q("""
        SELECT
            dp.name                                              AS [DB User],
            dp.type_desc                                         AS [User Type],
            ISNULL(sp.name, '(no login)')                        AS [Mapped Login],
            ISNULL(dp.default_schema_name, 'dbo')                AS [Default Schema],
            dp.create_date                                       AS [Created],
            dp.modify_date                                       AS [Modified],
            (
                SELECT STRING_AGG(r2.name, ', ')
                FROM sys.database_role_members drm2
                JOIN sys.database_principals r2 ON r2.principal_id = drm2.role_principal_id
                WHERE drm2.member_principal_id = dp.principal_id
            ) AS [DB Roles]
        FROM sys.database_principals dp
        LEFT JOIN sys.server_principals sp ON sp.sid = dp.sid
        WHERE dp.type IN ('S','U','G','E')
          AND dp.name NOT IN ('dbo','guest','INFORMATION_SCHEMA','sys','public')
          AND dp.name NOT LIKE '##%'
        ORDER BY dp.type_desc, dp.name
        """)

    def get_server_role_members(self) -> pd.DataFrame:
        return self._q("""
        SELECT
            sr.name                                              AS [Server Role],
            sp.name                                              AS [Member Login],
            sp.type_desc                                         AS [Member Type],
            CASE sp.is_disabled WHEN 1 THEN 'Disabled' ELSE 'Enabled' END AS [Status],
            sp.create_date                                       AS [Login Created]
        FROM sys.server_role_members srm
        JOIN sys.server_principals sr ON sr.principal_id  = srm.role_principal_id
        JOIN sys.server_principals sp ON sp.principal_id  = srm.member_principal_id
        WHERE sp.name NOT LIKE '##%'
          AND sp.name NOT IN (
              'NT AUTHORITY\\SYSTEM',
              'NT SERVICE\\MSSQLSERVER',
              'NT SERVICE\\SQLSERVERAGENT'
          )
        ORDER BY sr.name, sp.name
        """)

    def get_database_role_members(self) -> pd.DataFrame:
        return self._q("""
        SELECT
            r.name                                               AS [DB Role],
            dp.name                                              AS [Member User],
            dp.type_desc                                         AS [Member Type],
            ISNULL(sp.name, '(no login)')                        AS [Mapped Login]
        FROM sys.database_role_members drm
        JOIN sys.database_principals r  ON r.principal_id  = drm.role_principal_id
        JOIN sys.database_principals dp ON dp.principal_id = drm.member_principal_id
        LEFT JOIN sys.server_principals sp ON sp.sid = dp.sid
        WHERE r.type = 'R'
          AND dp.name NOT LIKE '##%'
        ORDER BY r.name, dp.name
        """)

    def get_object_permissions(self) -> pd.DataFrame:
        return self._q("""
        SELECT TOP 300
            dp.name                                              AS [Grantee],
            dp.type_desc                                         AS [Principal Type],
            p.class_desc                                         AS [Object Class],
            ISNULL(SCHEMA_NAME(o.schema_id), 'N/A')              AS [Schema],
            ISNULL(OBJECT_NAME(p.major_id),  'N/A')              AS [Object Name],
            p.permission_name                                    AS [Permission],
            p.state_desc                                         AS [Grant State]
        FROM sys.database_permissions p
        JOIN sys.database_principals dp  ON dp.principal_id = p.grantee_principal_id
        LEFT JOIN sys.objects o          ON o.object_id     = p.major_id
        WHERE p.class_desc IN ('OBJECT_OR_COLUMN','SCHEMA')
          AND dp.name NOT IN ('public','dbo','guest','INFORMATION_SCHEMA','sys')
          AND dp.name NOT LIKE '##%'
        ORDER BY dp.name, p.class_desc, OBJECT_NAME(p.major_id)
        """)

    def get_security_risks(self) -> pd.DataFrame:
        return self._q("""
        SELECT
            'Sysadmin Login'                             AS [Category],
            sp.name                                      AS [Principal],
            sp.type_desc                                 AS [Type],
            'Member of sysadmin fixed server role'       AS [Risk Description],
            'HIGH'                                       AS [Severity]
        FROM sys.server_principals sp
        JOIN sys.server_role_members srm ON srm.member_principal_id = sp.principal_id
        JOIN sys.server_principals   sr  ON sr.principal_id         = srm.role_principal_id
        WHERE sr.name = 'sysadmin'
          AND sp.name NOT IN (
              'sa','NT AUTHORITY\\SYSTEM',
              'NT SERVICE\\MSSQLSERVER','NT SERVICE\\SQLSERVERAGENT'
          )
          AND sp.name NOT LIKE '##%'
        UNION ALL
        SELECT
            'Weak Password Policy',
            sp2.name, sp2.type_desc,
            'SQL login without password expiry or complexity enforcement',
            'MEDIUM'
        FROM sys.sql_logins sp2
        WHERE (sp2.is_expiration_checked = 0 OR sp2.is_policy_checked = 0)
          AND sp2.name NOT IN ('sa')
          AND sp2.name NOT LIKE '##%'
        UNION ALL
        SELECT
            'db_owner Assigned',
            dp.name, dp.type_desc,
            'Database user has db_owner role — can modify schema and data',
            'MEDIUM'
        FROM sys.database_role_members drm
        JOIN sys.database_principals r  ON r.principal_id  = drm.role_principal_id
        JOIN sys.database_principals dp ON dp.principal_id = drm.member_principal_id
        WHERE r.name = 'db_owner'
          AND dp.name NOT IN ('dbo','sa')
          AND dp.name NOT LIKE '##%'
        UNION ALL
        SELECT
            'Disabled Login',
            sp3.name, sp3.type_desc,
            'Login is disabled — may indicate an orphan or stale account',
            'LOW'
        FROM sys.server_principals sp3
        WHERE sp3.is_disabled = 1
          AND sp3.type IN ('S','U','G')
          AND sp3.name NOT LIKE '##%'
          AND sp3.name NOT IN ('sa','BUILTIN\\Administrators')
        ORDER BY [Severity], [Category]
        """)
