"""
Role-Based Access Control (RBAC) for Enterprise SQL Server AI Agent
Roles: Business User < Analyst < Developer < DBA < Admin
"""
import hashlib
import json
from pathlib import Path
from typing import Dict, Optional

USERS_FILE = Path(__file__).parent.parent / "users.json"

# Role definitions — each level inherits all permissions below it
ROLES: Dict[str, dict] = {
    "Business User": {
        "level": 1,
        "icon": "👤",
        "color": "#4caf50",
        "permissions": {
            "dashboard", "ai_chat",
        },
        "description": "View dashboards and ask questions in plain English.",
    },
    "Analyst": {
        "level": 2,
        "icon": "📊",
        "color": "#2196f3",
        "permissions": {
            "dashboard", "ai_chat",
            "schema_explorer", "query_builder", "export_csv",
        },
        "description": "Explore schemas and build/export queries.",
    },
    "Developer": {
        "level": 3,
        "icon": "💻",
        "color": "#9c27b0",
        "permissions": {
            "dashboard", "ai_chat",
            "schema_explorer", "query_builder", "export_csv",
            "sp_analyzer", "function_explorer", "trigger_explorer",
            "relationship_mapper",
        },
        "description": "Analyse stored procedures, functions, triggers, and relationships.",
    },
    "DBA": {
        "level": 4,
        "icon": "🔧",
        "color": "#ff9800",
        "permissions": {
            "dashboard", "ai_chat",
            "schema_explorer", "query_builder", "export_csv",
            "sp_analyzer", "function_explorer", "trigger_explorer",
            "relationship_mapper",
            "index_advisor", "apply_indexes", "admin_tools",
        },
        "description": "Full database administration including indexes and performance.",
    },
    "Admin": {
        "level": 5,
        "icon": "👑",
        "color": "#f44336",
        "permissions": {"*"},   # wildcard = all permissions
        "description": "Full access including user and role management.",
    },
}


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _load_users() -> dict:
    if USERS_FILE.exists():
        return json.loads(USERS_FILE.read_text())
    return {}


def _save_users(users: dict):
    USERS_FILE.write_text(json.dumps(users, indent=2))


def bootstrap_default_users():
    """Create default users on first run."""
    if USERS_FILE.exists():
        return
    defaults = {
        "admin":     {"name": "Administrator",  "role": "Admin",         "password": _hash("Admin@123")},
        "dba":       {"name": "Database Admin", "role": "DBA",           "password": _hash("Dba@123")},
        "developer": {"name": "Developer",      "role": "Developer",     "password": _hash("Dev@123")},
        "analyst":   {"name": "Data Analyst",   "role": "Analyst",       "password": _hash("Analyst@123")},
        "user":      {"name": "Business User",  "role": "Business User", "password": _hash("User@123")},
    }
    _save_users(defaults)


def authenticate(username: str, password: str) -> Optional[dict]:
    """Return user dict if credentials valid, else None."""
    users = _load_users()
    u = users.get(username.lower().strip())
    if u and u["password"] == _hash(password):
        return {"username": username, "name": u["name"], "role": u["role"]}
    return None


def has_permission(role: str, permission: str) -> bool:
    """Check if a role has a specific permission."""
    r = ROLES.get(role, {})
    perms = r.get("permissions", set())
    return "*" in perms or permission in perms


def get_role_info(role: str) -> dict:
    return ROLES.get(role, ROLES["Business User"])


def list_users() -> list:
    """Return list of users (without password hashes)."""
    users = _load_users()
    return [
        {"username": k, "name": v["name"], "role": v["role"]}
        for k, v in users.items()
    ]


def create_user(username: str, name: str, role: str, password: str) -> tuple:
    """Create a new user. Returns (success, message)."""
    if role not in ROLES:
        return False, f"Invalid role: {role}"
    users = _load_users()
    if username.lower() in users:
        return False, f"Username '{username}' already exists."
    users[username.lower()] = {
        "name": name, "role": role, "password": _hash(password)
    }
    _save_users(users)
    return True, f"User '{username}' created successfully."


def update_user_role(username: str, new_role: str) -> tuple:
    if new_role not in ROLES:
        return False, f"Invalid role: {new_role}"
    users = _load_users()
    if username not in users:
        return False, f"User '{username}' not found."
    users[username]["role"] = new_role
    _save_users(users)
    return True, "Role updated."


def delete_user(username: str) -> tuple:
    users = _load_users()
    if username not in users:
        return False, "User not found."
    if username == "admin":
        return False, "Cannot delete the admin account."
    del users[username]
    _save_users(users)
    return True, "User deleted."


def change_password(username: str, old_pw: str, new_pw: str) -> tuple:
    users = _load_users()
    u = users.get(username)
    if not u or u["password"] != _hash(old_pw):
        return False, "Current password is incorrect."
    if len(new_pw) < 6:
        return False, "Password must be at least 6 characters."
    users[username]["password"] = _hash(new_pw)
    _save_users(users)
    return True, "Password changed successfully."
