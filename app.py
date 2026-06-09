"""
Enterprise SQL Server AI Agent
TransFlow-style enterprise UI · Multi-Agent Architecture · RBAC
"""
import json, re, sys
from pathlib import Path
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="SQLNexus Enterprise · AI Database Intelligence",
    page_icon="🗄️",
    layout="wide",
    initial_sidebar_state="expanded",
)
sys.path.insert(0, str(Path(__file__).parent))

# ─────────────────────────────────────────────────────────────────────────────
# ENTERPRISE CSS  (TransFlow-inspired dark nav + card layout)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ═══════════════════════════════════════════════════════════════════════════
   SQLNexus Enterprise · Design System v3.0
   AI-Powered SQL Server Intelligence Platform
   ═══════════════════════════════════════════════════════════════════════════ */

/* ── Base ── */
html,body,[data-testid="stAppViewContainer"]{
    background:#f1f5f9;color:#0f172a;
    font-family:'Segoe UI',system-ui,-apple-system,BlinkMacSystemFont,sans-serif;
}
[data-testid="stAppViewContainer"] .main .block-container{
    padding:1.25rem 1.75rem !important;max-width:100% !important;
}

/* ── Hide Streamlit chrome ── */
#MainMenu,footer,[data-testid="stToolbar"],[data-testid="stDecoration"]{display:none}
header[data-testid="stHeader"]{background:transparent;height:0}

/* ── Sidebar shell ── */
[data-testid="stSidebar"]{
    background:linear-gradient(180deg,#0f172a 0%,#1a2744 100%) !important;
    border-right:1px solid #1e3a5f;
    min-width:240px !important;max-width:240px !important;
}
[data-testid="stSidebar"] *{color:#94a3b8 !important}

/* ── Nav buttons ── */
[data-testid="stSidebar"] .stButton>button{
    width:100%;text-align:left;background:transparent;
    border:none;color:#94a3b8 !important;
    padding:9px 14px;border-radius:7px;
    font-size:13px;font-weight:400;
    transition:all .15s;margin:1px 0;
}
[data-testid="stSidebar"] .stButton>button:hover{
    background:rgba(255,255,255,.07) !important;
    color:#e2e8f0 !important;
}

/* ── Section labels ── */
.nav-section{
    font-size:9.5px;font-weight:800;letter-spacing:1.5px;
    color:#2d4a6e !important;text-transform:uppercase;
    padding:14px 16px 4px;margin:0;
}

/* ── Logo area ── */
.logo-wrap{
    display:flex;align-items:center;gap:11px;
    padding:18px 14px 14px;
    border-bottom:1px solid #1e3a5f;margin-bottom:6px;
}
.logo-icon{
    width:36px;height:36px;border-radius:10px;
    background:linear-gradient(135deg,#2563eb,#0891b2);
    display:flex;align-items:center;justify-content:center;
    font-size:16px;font-weight:800;color:#fff;flex-shrink:0;
    box-shadow:0 4px 12px rgba(37,99,235,.45);
}
.logo-text{font-size:14px;font-weight:800;color:#f1f5f9 !important;letter-spacing:-.01em;line-height:1.2}
.logo-sub{font-size:9px;color:#3d5a80 !important;text-transform:uppercase;letter-spacing:.9px}

/* ── Conn badge in sidebar ── */
.conn-badge{
    background:rgba(255,255,255,.04);border:1px solid #1e3a5f;
    border-radius:8px;padding:10px 14px;margin:6px 10px;
}
.conn-badge .label{font-size:9px;color:#3d5a80 !important;text-transform:uppercase;letter-spacing:.9px}
.conn-badge .value{font-size:13px;color:#38bdf8 !important;font-weight:600}
.conn-dot-green{width:7px;height:7px;border-radius:50%;background:#10b981;display:inline-block;margin-right:6px;box-shadow:0 0 5px rgba(16,185,129,.5)}
.conn-dot-gray{width:7px;height:7px;border-radius:50%;background:#334155;display:inline-block;margin-right:6px}

/* ── Main page header ── */
.page-header{
    display:flex;align-items:center;justify-content:space-between;
    margin-bottom:1.5rem;padding-bottom:1rem;
    border-bottom:1px solid #e2e8f0;
}
.page-title{font-size:22px;font-weight:800;color:#0f172a;margin:0;letter-spacing:-.025em}
.page-subtitle{font-size:12px;color:#64748b;margin-top:3px}
.status-pill{
    display:inline-flex;align-items:center;gap:5px;
    padding:5px 14px;border-radius:20px;
    background:#dcfce7;color:#166534;font-size:11px;font-weight:700;
    border:1px solid #bbf7d0;
}
.status-dot{width:7px;height:7px;border-radius:50%;background:#10b981;box-shadow:0 0 5px rgba(16,185,129,.4)}

/* ── Feature cards (Control Center) ── */
.feat-card{
    background:#fff;border:1px solid #e2e8f0;border-radius:14px;
    padding:20px 22px;height:100%;cursor:pointer;
    transition:all .2s ease;box-shadow:0 1px 3px rgba(15,23,42,.05);
    position:relative;overflow:hidden;
}
.feat-card:hover{
    border-color:#2563eb;
    box-shadow:0 8px 28px rgba(37,99,235,.14);
    transform:translateY(-2px);
}
.feat-icon{
    width:46px;height:46px;border-radius:12px;
    display:flex;align-items:center;justify-content:center;
    font-size:23px;margin-bottom:12px;
}
.feat-title{font-size:14px;font-weight:700;color:#0f172a;margin:0 0 6px}
.feat-desc{font-size:12px;color:#64748b;line-height:1.6;margin:0}

/* ── Metric cards ── */
.metric-card{
    background:#fff;border:1px solid #e2e8f0;border-radius:12px;
    padding:16px 18px;position:relative;overflow:hidden;
    box-shadow:0 1px 3px rgba(15,23,42,.05);
    transition:box-shadow .2s;
}
.metric-card:hover{box-shadow:0 4px 16px rgba(15,23,42,.1)}
.metric-card::before{
    content:'';position:absolute;top:0;left:0;right:0;height:3px;
    background:linear-gradient(90deg,#2563eb,#0891b2);
}
.metric-val{font-size:26px;font-weight:800;color:#0f172a;letter-spacing:-.03em;margin:6px 0 2px}
.metric-lbl{font-size:11px;color:#64748b;font-weight:600;text-transform:uppercase;letter-spacing:.7px}
.metric-change{font-size:11px;color:#10b981;font-weight:600;margin-top:4px}

/* ── Section cards ── */
.section-card{
    background:#fff;border:1px solid #e2e8f0;border-radius:12px;
    padding:0;overflow:hidden;box-shadow:0 1px 3px rgba(15,23,42,.04);
}
.section-card-header{
    padding:14px 20px;border-bottom:1px solid #f1f5f9;
    display:flex;align-items:center;justify-content:space-between;
    background:#fafbfc;
}
.section-card-title{font-size:14px;font-weight:700;color:#0f172a}
.section-card-body{padding:16px 20px}

/* ── Status badges ── */
.badge{display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:700}
.badge-green{background:#dcfce7;color:#166534}
.badge-red{background:#fef2f2;color:#dc2626}
.badge-yellow{background:#fef9c3;color:#a16207}
.badge-blue{background:#eff6ff;color:#1d4ed8}
.badge-gray{background:#f1f5f9;color:#475569}
.badge-purple{background:#f5f3ff;color:#6d28d9}
.badge-teal{background:#ecfeff;color:#0891b2}
.badge-orange{background:#fff7ed;color:#c2410c}

/* ── Table styling ── */
.stDataFrame{border:1px solid #e2e8f0 !important;border-radius:10px !important;overflow:hidden !important}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"]{
    gap:0;background:#fff;border-bottom:2px solid #e2e8f0;
    padding:0 4px;border-radius:0;
}
.stTabs [data-baseweb="tab"]{
    background:transparent;color:#64748b;border:none;
    padding:11px 20px;font-size:13px;font-weight:500;
    border-bottom:2px solid transparent;margin-bottom:-2px;
    border-radius:0;
}
.stTabs [aria-selected="true"]{
    color:#2563eb !important;background:transparent !important;
    border-bottom-color:#2563eb !important;font-weight:700;
}

/* ── Inputs ── */
.stTextInput input,.stTextArea textarea,.stSelectbox select{
    background:#fff !important;border:1.5px solid #e2e8f0 !important;
    border-radius:8px !important;color:#0f172a !important;font-size:13px !important;
}
.stTextInput input:focus,.stTextArea textarea:focus{
    border-color:#2563eb !important;box-shadow:0 0 0 3px rgba(37,99,235,.1) !important;
}

/* ── Primary buttons ── */
.stButton>button[kind="primary"]{
    background:linear-gradient(135deg,#1d4ed8,#2563eb) !important;
    border:none !important;color:#fff !important;
    border-radius:8px !important;padding:9px 22px !important;
    font-weight:700 !important;font-size:13px !important;
    box-shadow:0 2px 8px rgba(37,99,235,.3) !important;
}
.stButton>button[kind="primary"]:hover{
    background:linear-gradient(135deg,#1e40af,#1d4ed8) !important;
    box-shadow:0 4px 16px rgba(37,99,235,.4) !important;
}
.stButton>button{
    background:#fff !important;border:1.5px solid #e2e8f0 !important;
    color:#374151 !important;border-radius:8px !important;
    padding:8px 18px !important;font-size:13px !important;font-weight:500 !important;
}
.stButton>button:hover{background:#f8fafc !important;border-color:#cbd5e1 !important}

/* ── Alerts ── */
.stSuccess>div{background:#f0fdf4 !important;border:1px solid #bbf7d0 !important;border-left:4px solid #10b981 !important;border-radius:8px !important;color:#166534 !important}
.stError>div  {background:#fef2f2 !important;border:1px solid #fecaca !important;border-left:4px solid #ef4444 !important;border-radius:8px !important;color:#dc2626 !important}
.stInfo>div   {background:#eff6ff !important;border:1px solid #bfdbfe !important;border-left:4px solid #2563eb !important;border-radius:8px !important;color:#1d4ed8 !important}
.stWarning>div{background:#fffbeb !important;border:1px solid #fde68a !important;border-left:4px solid #d97706 !important;border-radius:8px !important;color:#92400e !important}

/* ── Expander ── */
.streamlit-expanderHeader{
    background:#fafbfc !important;border:1.5px solid #e2e8f0 !important;
    border-radius:8px !important;font-size:13px !important;
    color:#374151 !important;font-weight:600 !important;
}

/* ── Code blocks ── */
.stCodeBlock{background:#0f172a !important;border:1px solid #1e293b !important;border-radius:10px !important}

/* ── Chat ── */
[data-testid="stChatMessage"]{
    background:#fff !important;border:1px solid #e2e8f0 !important;
    border-radius:12px !important;margin:8px 0 !important;
    box-shadow:0 1px 4px rgba(15,23,42,.05) !important;
}
[data-testid="stChatInput"]{
    background:#fff !important;border:1.5px solid #e2e8f0 !important;
    border-radius:10px !important;
}

/* ── Sidebar divider ── */
.sidebar-divider{height:1px;background:#1e3a5f;margin:8px 12px}

/* ── DB connection list item ── */
.db-item{
    display:flex;align-items:center;gap:8px;
    padding:8px 14px;cursor:pointer;border-radius:6px;transition:.15s;
}
.db-item:hover{background:rgba(255,255,255,.06)}
.db-item.active{background:rgba(37,99,235,.2)}

/* ── Hero banner (Control Center) ── */
.hero-banner{
    background:linear-gradient(135deg,#0f172a 0%,#1e3a5f 50%,#0d4f8a 100%);
    border-radius:16px;padding:30px 34px;color:#fff;margin-bottom:22px;
    position:relative;overflow:hidden;
    border:1px solid #1e3a5f;
    box-shadow:0 8px 32px rgba(15,23,42,.25);
}
.hero-banner::before{
    content:'';position:absolute;top:-80px;right:-80px;
    width:300px;height:300px;border-radius:50%;
    background:radial-gradient(circle,rgba(37,99,235,.15) 0%,transparent 70%);
}
.hero-tag{
    display:inline-flex;align-items:center;gap:6px;
    background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);
    padding:4px 14px;border-radius:20px;
    font-size:10px;font-weight:700;letter-spacing:1.2px;text-transform:uppercase;
    margin-bottom:12px;color:#7dd3fc;
}
.hero-title{font-size:26px;font-weight:800;letter-spacing:-.03em;margin:0 0 6px}
.hero-sub{font-size:13px;opacity:.75;line-height:1.5;max-width:620px;margin:0 0 18px}
.hero-stats{
    display:flex;gap:28px;padding-top:18px;
    border-top:1px solid rgba(255,255,255,.1);
}
.hero-stat-val{font-size:20px;font-weight:800;line-height:1}
.hero-stat-lbl{font-size:10px;color:rgba(255,255,255,.55);text-transform:uppercase;letter-spacing:.8px;margin-top:3px}

/* ── Info/warn panels ── */
.info-panel{background:#eff6ff;border:1px solid #bfdbfe;border-left:4px solid #2563eb;border-radius:8px;padding:12px 16px;font-size:13px;color:#1e40af;margin:8px 0}
.warn-panel{background:#fffbeb;border:1px solid #fde68a;border-left:4px solid #d97706;border-radius:8px;padding:12px 16px;font-size:13px;color:#92400e;margin:8px 0}
.danger-panel{background:#fef2f2;border:1px solid #fecaca;border-left:4px solid #ef4444;border-radius:8px;padding:12px 16px;font-size:13px;color:#991b1b;margin:8px 0}

/* ── Hide streamlit sidebar scrollbar artifacts ── */
[data-testid="stSidebar"] section{overflow-x:hidden}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# BOOTSTRAP & MODULES
# ─────────────────────────────────────────────────────────────────────────────
from modules import rbac as RBAC
RBAC.bootstrap_default_users()
CONFIG_FILE = Path(__file__).parent / "connections.json"

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
_DEFAULTS = {
    "authenticated": False, "current_user": None,
    "page": "control_center",
    "connections": {}, "active_conn_id": None,
    "schema_cache": None, "chat_history": [],
    "query_history": [],
    "ai_cfg": {
        "endpoint": "https://aisozvsdemo.openai.azure.com",
        "api_key": "", "model": "gpt-4.1-mini",
        "api_version": "2024-12-01-preview",
    },
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

if CONFIG_FILE.exists() and not st.session_state["connections"]:
    try:
        saved = json.loads(CONFIG_FILE.read_text())
        st.session_state["connections"]    = saved.get("connections", {})
        st.session_state["active_conn_id"] = saved.get("active_conn_id")
        cfg = saved.get("ai_cfg", {}); cfg.pop("api_key", None)
        st.session_state["ai_cfg"].update(cfg)
    except Exception:
        pass

def _save():
    CONFIG_FILE.write_text(json.dumps({
        "connections":    st.session_state["connections"],
        "active_conn_id": st.session_state["active_conn_id"],
        "ai_cfg": {k:v for k,v in st.session_state["ai_cfg"].items() if k!="api_key"},
    }, indent=2, default=str))

def goto(page): st.session_state["page"] = page

# ─────────────────────────────────────────────────────────────────────────────
# FACTORIES
# ─────────────────────────────────────────────────────────────────────────────
def _conn(cid=None):
    from modules.sql_connector import SQLConnector
    cid = cid or st.session_state["active_conn_id"]
    if not cid or cid not in st.session_state["connections"]: return None
    return SQLConnector(st.session_state["connections"][cid]["connection_string"])

def _agent():
    from modules.ai_agent import AIAgent
    c = st.session_state["ai_cfg"]
    if not c.get("api_key") or not c.get("endpoint"): return None
    return AIAgent(c["endpoint"], c["api_key"], c["model"], c["api_version"])

def _orch():
    from modules.agents.orchestrator import AgentOrchestrator
    ag = _agent()
    if not ag: return None
    u = st.session_state.get("current_user") or {}
    return AgentOrchestrator(ag, st.session_state.get("schema_cache") or "", u.get("role","Analyst"))

def _can(p):
    u = st.session_state.get("current_user")
    return bool(u and RBAC.has_permission(u["role"], p))

def _role(): 
    u = st.session_state.get("current_user")
    return u["role"] if u else "Business User"

def _load_schema():
    if st.session_state.get("schema_cache") or not st.session_state["active_conn_id"]: return
    try:
        from modules.schema_analyzer import SchemaAnalyzer
        st.session_state["schema_cache"] = SchemaAnalyzer(_conn()).get_schema_summary()
    except Exception: pass

def _chart(df, spec):
    try:
        ct=spec.get("chart_type","table"); cols=list(df.columns)
        xc=spec.get("x_column",""); yc=spec.get("y_column","")
        cc=spec.get("color_column"); title=spec.get("title","Results")
        if xc not in cols: xc=cols[0] if cols else ""
        if yc not in cols: yc=cols[1] if len(cols)>1 else xc
        if cc and cc not in cols: cc=None
        kw=dict(template="plotly_white",title=title,color_discrete_sequence=px.colors.qualitative.Set2)
        if ct=="bar":    return px.bar(df,x=xc,y=yc,color=cc,**kw)
        if ct=="line":   return px.line(df,x=xc,y=yc,color=cc,**kw)
        if ct=="pie":    return px.pie(df,names=xc,values=yc,**kw)
        if ct=="scatter":return px.scatter(df,x=xc,y=yc,color=cc,**kw)
        if ct=="histogram":return px.histogram(df,x=xc,color=cc,**kw)
    except Exception: pass
    return None

# ─────────────────────────────────────────────────────────────────────────────
# LOGIN PAGE
# ─────────────────────────────────────────────────────────────────────────────
if not st.session_state["authenticated"]:
    st.markdown("""
    <div style="min-height:100vh;display:flex;align-items:center;justify-content:center;
    background:linear-gradient(135deg,#0d1117 0%,#161b2e 50%,#0d1117 100%);">
    """, unsafe_allow_html=True)

    _, mid, _ = st.columns([1,1,1])
    with mid:
        st.markdown("""
        <div style='text-align:center;padding:20px 0 30px'>
            <div style='width:56px;height:56px;border-radius:14px;
            background:linear-gradient(135deg,#1f6feb,#58a6ff);
            display:inline-flex;align-items:center;justify-content:center;
            font-size:26px;margin-bottom:16px'>🗄️</div>
            <div style='font-size:24px;font-weight:800;color:#fff;margin-bottom:4px'>SQLNexus Enterprise</div>
            <div style='font-size:12px;color:#94a3b8;letter-spacing:.5px'>
                AI-POWERED SQL SERVER INTELLIGENCE PLATFORM
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login", clear_on_submit=False):
            st.markdown("<p style='color:#8b949e;font-size:13px;margin-bottom:4px'>USERNAME</p>", unsafe_allow_html=True)
            username = st.text_input("", placeholder="Enter username", label_visibility="collapsed")
            st.markdown("<p style='color:#8b949e;font-size:13px;margin-top:12px;margin-bottom:4px'>PASSWORD</p>", unsafe_allow_html=True)
            password = st.text_input("", type="password", placeholder="Enter password", label_visibility="collapsed")
            st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)
            if st.form_submit_button("Sign In →", use_container_width=True, type="primary"):
                user = RBAC.authenticate(username, password)
                if user:
                    st.session_state["authenticated"] = True
                    st.session_state["current_user"]  = user
                    st.rerun()
                else:
                    st.error("Invalid username or password")

        st.markdown("""
        <div style='background:#161b2e;border:1px solid #21262d;border-radius:8px;
        padding:14px 16px;margin-top:16px'>
            <p style='color:#8b949e;font-size:11px;font-weight:600;
            letter-spacing:.8px;text-transform:uppercase;margin:0 0 10px'>
            Default Accounts</p>
        """, unsafe_allow_html=True)
        for icon, lbl, cred in [
            ("👑","Admin","admin / Admin@123"),("🔧","DBA","dba / Dba@123"),
            ("💻","Developer","developer / Dev@123"),("📊","Analyst","analyst / Analyst@123"),
            ("👤","User","user / User@123"),
        ]:
            st.markdown(
                f"<div style='display:flex;justify-content:space-between;padding:3px 0'>"
                f"<span style='color:#8b949e;font-size:12px'>{icon} {lbl}</span>"
                f"<code style='color:#58a6ff;font-size:11px;background:#0d1117;padding:1px 6px;"
                f"border-radius:4px'>{cred}</code></div>",
                unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# AUTHENTICATED → SIDEBAR NAV
# ─────────────────────────────────────────────────────────────────────────────
user = st.session_state["current_user"]
role = user["role"]
ri   = RBAC.get_role_info(role)
page = st.session_state["page"]
active_c = st.session_state["connections"].get(st.session_state["active_conn_id"])

with st.sidebar:
    # ── Logo ──────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="logo-wrap">
        <div class="logo-icon">SN</div>
        <div>
            <div class="logo-text">SQLNexus</div>
            <div class="logo-sub">Enterprise · AI Powered</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Active DB badge ───────────────────────────────────────────────────
    if active_c:
        st.markdown(f"""
        <div class="conn-badge">
            <div class="label">Active Database</div>
            <div class="value">
                <span class="conn-dot-green"></span>{active_c['label']}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="conn-badge">
            <div class="label">Database</div>
            <div class="value" style="color:#484f58 !important">
                <span class="conn-dot-gray"></span>Not connected
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div class='sidebar-divider'></div>", unsafe_allow_html=True)

    # ── Navigation helper ─────────────────────────────────────────────────
    def nav(icon, label, page_id, perm=None):
        if perm and not _can(perm): return
        is_active = page == page_id
        lbl = f"▸ {icon}  {label}" if is_active else f"   {icon}  {label}"
        if st.button(lbl, key=f"nav_{page_id}", use_container_width=True):
            goto(page_id); st.rerun()

    def nav_section(label):
        st.markdown(f"<p class='nav-section'>{label}</p>", unsafe_allow_html=True)

    nav_section("OVERVIEW")
    nav("⊞", "Control Center",    "control_center")

    nav_section("DATABASE")
    nav("🔌", "Database Manager",  "db_manager")
    nav("🗂️", "Metadata Explorer", "metadata",    "schema_explorer")
    nav("🔗", "Relationship Mapper","relationships","relationship_mapper")

    nav_section("AI & ANALYTICS")
    nav("🤖", "AI Assistant",       "ai_chat",       "ai_chat")
    nav("⚡", "Query Studio",       "query_studio",  "query_builder")
    nav("📈", "AI Insights",        "ai_insights")

    nav_section("PERFORMANCE")
    nav("📊", "Index Intelligence",  "index_intel",   "index_advisor")
    nav("🔍", "Query Optimizer",     "query_optimizer")
    nav("💓", "Health Monitor",      "health_monitor")

    nav_section("DATA MANAGEMENT")
    nav("✏️", "Data Editor",         "data_editor")
    nav("🛡️", "Data Quality",        "data_quality")

    nav_section("SECURITY & GOVERNANCE")
    nav("🔐", "Security Center",     "security_center", "schema_explorer")

    nav_section("INFRASTRUCTURE")
    nav("🤖", "SQL Agent Jobs",      "agent_jobs")
    nav("💾", "Backup Monitor",      "backup_monitor")
    nav("⚙️", "Server Config",       "server_config",   "schema_explorer")

    nav_section("ADMINISTRATION")
    if role == "Admin":
        nav("🔐", "Admin Console",   "admin")

    st.markdown("<div class='sidebar-divider'></div>", unsafe_allow_html=True)

    # ── User info + sign out ──────────────────────────────────────────────
    st.markdown(f"""
    <div style='padding:10px 14px;display:flex;align-items:center;gap:10px'>
        <div style='width:30px;height:30px;border-radius:50%;
        background:{ri['color']};display:flex;align-items:center;
        justify-content:center;font-size:13px;flex-shrink:0'>{ri['icon']}</div>
        <div>
            <div style='font-size:12px;font-weight:600;color:#c9d1d9 !important'>{user['name']}</div>
            <div style='font-size:10px;color:#484f58 !important'>{role}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Sign Out", use_container_width=True, key="signout"):
        for k in ["authenticated","current_user","chat_history","schema_cache","page"]:
            st.session_state.pop(k, None)
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# PAGE HEADER HELPER
# ─────────────────────────────────────────────────────────────────────────────
def page_header(title, subtitle="", status="operational"):
    status_html = ""
    if status == "operational":
        status_html = "<span class='status-pill'><span class='status-dot'></span>System Operational</span>"
    elif status == "connected" and active_c:
        status_html = (f"<span class='status-pill'><span class='status-dot'></span>"
                      f"Connected: {active_c['label']}</span>")
    elif status == "disconnected":
        status_html = ("<span class='status-pill' style='background:#f6f8fa;color:#6e7681'>"
                      "⚪ Not Connected</span>")

    st.markdown(f"""
    <div class="page-header">
        <div>
            <div class="page-title">{title}</div>
            <div class="page-subtitle">{subtitle}</div>
        </div>
        {status_html}
    </div>
    """, unsafe_allow_html=True)

def metric_card(label, value, change="", color="#1f6feb"):
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-lbl">{label}</div>
        <div class="metric-val" style="color:{color}">{value}</div>
        {"<div class='metric-change'>"+change+"</div>" if change else ""}
    </div>
    """, unsafe_allow_html=True)

def feat_card(icon, bg, title, desc, page_id):
    st.markdown(f"""
    <div class="feat-card" onclick="">
        <div class="feat-icon" style="background:{bg}">{icon}</div>
        <div class="feat-title">{title}</div>
        <div class="feat-desc">{desc}</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button(f"Open →", key=f"fc_{page_id}", use_container_width=True):
        goto(page_id); st.rerun()

def section_card_start(title, action_label="", action_key=""):
    st.markdown(f"""
    <div class="section-card">
        <div class="section-card-header">
            <span class="section-card-title">{title}</span>
        </div>
        <div class="section-card-body">
    """, unsafe_allow_html=True)

def section_card_end():
    st.markdown("</div></div>", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: CONTROL CENTER
# ═════════════════════════════════════════════════════════════════════════════
if page == "control_center":
    # ── Hero Banner ────────────────────────────────────────────────────────
    conns_n  = len(st.session_state["connections"])
    ai_ready = "✅ Ready" if st.session_state["ai_cfg"].get("api_key") else "⚙️ Setup"
    active_db = active_c["label"] if active_c else "Not Connected"
    st.markdown(f"""
    <div class="hero-banner">
        <div class="hero-tag">⚡ MULTI-AGENT · AI POWERED · 16 ENTERPRISE MODULES</div>
        <div class="hero-title">SQLNexus Enterprise</div>
        <div class="hero-sub">The AI-Powered SQL Server Intelligence Platform — Schema Discovery ·
        Natural Language Queries · Index Intelligence · Security Audit ·
        Health Monitoring · Backup Governance · Data Quality</div>
        <div class="hero-stats">
            <div><div class="hero-stat-val">{conns_n}</div><div class="hero-stat-lbl">Connections</div></div>
            <div><div class="hero-stat-val">{ai_ready}</div><div class="hero-stat-lbl">AI Engine</div></div>
            <div><div class="hero-stat-val">16</div><div class="hero-stat-lbl">Modules</div></div>
            <div><div class="hero-stat-val">6</div><div class="hero-stat-lbl">AI Agents</div></div>
            <div><div class="hero-stat-val" style="font-size:13px;word-break:break-word">{active_db}</div>
                 <div class="hero-stat-lbl">Active DB</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Feature Cards ─────────────────────────────────────────────────────
    c1,c2,c3 = st.columns(3, gap="medium")
    with c1:
        feat_card("🤖","linear-gradient(135deg,#ddf4ff,#b6e3ff)",
                  "AI Assistant",
                  "Natural language to optimized T-SQL via 6-agent pipeline — Schema, SQL, Validation, Optimization, Explanation, Visualization.",
                  "ai_chat")
    with c2:
        feat_card("🗂️","linear-gradient(135deg,#fff8c5,#f0e17a)",
                  "Metadata Explorer",
                  "Browse tables, views, stored procedures, functions, and triggers with AI-powered analysis and optimization.",
                  "metadata")
    with c3:
        feat_card("🔗","linear-gradient(135deg,#e6f4ea,#a3d9a5)",
                  "Relationship Mapper",
                  "Visualize FK/PK relationships, detect orphan tables, and get AI-suggested missing foreign keys.",
                  "relationships")

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    c4,c5,c6 = st.columns(3, gap="medium")
    with c4:
        feat_card("📊","linear-gradient(135deg,#ffebe9,#fac0bd)",
                  "Index Intelligence",
                  "DMV-based analysis of missing, unused, and duplicate indexes with impact scoring and one-click apply.",
                  "index_intel")
    with c5:
        feat_card("⚡","linear-gradient(135deg,#f3e2fc,#d8b4fe)",
                  "Query Studio",
                  "Natural language to optimized T-SQL with schema context, direct SQL editor, CSV export and result charts.",
                  "query_studio")
    with c6:
        feat_card("🔌","linear-gradient(135deg,#e1f0ff,#93c5fd)",
                  "Database Manager",
                  "Connect to any SQL Server — Windows Auth, SQL Auth, Azure SQL, LocalDB. Switch connections anytime.",
                  "db_manager")

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    c7,c8,c9 = st.columns(3, gap="medium")
    with c7:
        feat_card("💓","linear-gradient(135deg,#fce7f3,#f9a8d4)",
                  "Health Monitor",
                  "Real-time CPU, memory, I/O, blocking, and wait statistics from SQL Server DMVs.",
                  "health_monitor")
    with c8:
        feat_card("🔍","linear-gradient(135deg,#f0fdf4,#86efac)",
                  "Query Optimizer",
                  "Top CPU/I/O queries, blocking chains, index fragmentation analysis, and AI-powered rewrites.",
                  "query_optimizer")
    with c9:
        feat_card("🛡️","linear-gradient(135deg,#fff7ed,#fed7aa)",
                  "Data Quality",
                  "Referential integrity checks, column profiles, disabled constraints, and AI governance reports.",
                  "data_quality")

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    c10,c11,c12,c13 = st.columns(4, gap="medium")
    with c10:
        feat_card("🔐","linear-gradient(135deg,#fdf2f8,#f5d0fe)",
                  "Security Center",
                  "Audit logins, users, roles, object permissions, and identify high-priority security risks.",
                  "security_center")
    with c11:
        feat_card("🤖","linear-gradient(135deg,#f0fdf4,#bbf7d0)",
                  "SQL Agent Jobs",
                  "Monitor SQL Server Agent job status, history, failure patterns, and scheduling issues.",
                  "agent_jobs")
    with c12:
        feat_card("💾","linear-gradient(135deg,#eff6ff,#bfdbfe)",
                  "Backup Monitor",
                  "Track backup status, recovery models, database sizes, and generate backup strategy.",
                  "backup_monitor")
    with c13:
        feat_card("⚙️","linear-gradient(135deg,#f8fafc,#e2e8f0)",
                  "Server Config",
                  "Inspect server properties, configuration options, linked servers, and AI tuning advice.",
                  "server_config")

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # ── Stats Row ─────────────────────────────────────────────────────────
    conn = _conn()
    if conn:
        if st.button("🔄 Refresh Stats", key="cc_refresh"):
            with st.spinner("Loading…"):
                try:
                    from modules.schema_analyzer import SchemaAnalyzer
                    sa = SchemaAnalyzer(conn)
                    st.session_state["cc_stats"] = sa.get_database_stats()
                except Exception as ex:
                    st.error(str(ex))

        stats = st.session_state.get("cc_stats", {})
        if stats:
            st.markdown("#### Database Overview")
            m = st.columns(8, gap="small")
            for i,(k,lbl,col) in enumerate([
                ("tables","Tables","#1f6feb"),("views","Views","#0969da"),
                ("procedures","Procedures","#8250df"),("functions","Functions","#9a6700"),
                ("triggers","Triggers","#cf222e"),("indexes","Indexes","#1a7f37"),
                ("foreign_keys","Foreign Keys","#0550ae"),
            ]):
                with m[i]:
                    metric_card(lbl, stats.get(k,0), color=col)
            m[-1].markdown(f"""
            <div class="metric-card">
                <div class="metric-lbl">AI Model</div>
                <div style="font-size:13px;font-weight:600;color:#1f6feb;word-break:break-all">
                    {st.session_state['ai_cfg']['model']}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Bottom Row ────────────────────────────────────────────────────────
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    left, right = st.columns([3,2], gap="medium")

    with left:
        st.markdown("""
        <div class="section-card">
            <div class="section-card-header">
                <span class="section-card-title">Query History</span>
            </div>
        """, unsafe_allow_html=True)
        qh = st.session_state.get("query_history", [])
        if qh:
            qh_df = pd.DataFrame(qh[-10:])
            st.dataframe(qh_df, use_container_width=True, height=200,
                        hide_index=True)
        else:
            st.markdown("<div style='padding:16px 20px;color:#6e7681;font-size:13px'>No queries executed yet.</div>",
                       unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("""
        <div class="section-card">
            <div class="section-card-header">
                <span class="section-card-title">Active Connections</span>
            </div>
        """, unsafe_allow_html=True)
        conns = st.session_state["connections"]
        if conns:
            for cid, c in conns.items():
                is_a = cid == st.session_state["active_conn_id"]
                dot  = "conn-dot-green" if is_a else "conn-dot-gray"
                badge = "<span class='badge badge-green'>Active</span>" if is_a else ""
                st.markdown(f"""
                <div style='display:flex;align-items:center;justify-content:space-between;
                padding:10px 20px;border-bottom:1px solid #f0f2f6;font-size:13px'>
                    <div><span class='{dot}'></span><b>{c['label']}</b></div>
                    {badge}
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown("<div style='padding:16px 20px;color:#6e7681;font-size:13px'>No connections. Add one in Database Manager.</div>",
                       unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: DATABASE MANAGER  (dedicated connection management)
# ═════════════════════════════════════════════════════════════════════════════
elif page == "db_manager":
    page_header(
        "Database Manager",
        "Connect and manage SQL Server database connections",
        "connected" if active_c else "disconnected",
    )

    left, right = st.columns([2,3], gap="large")

    with left:
        # ── Add connection form ───────────────────────────────────────────
        st.markdown("""
        <div class="section-card">
            <div class="section-card-header">
                <span class="section-card-title">➕ New Connection</span>
            </div>
            <div class="section-card-body">
        """, unsafe_allow_html=True)

        lbl = st.text_input("Connection Label", placeholder="e.g. Production, Staging, Dev")
        cs  = st.text_area("Connection String", height=90,
                           placeholder="Server=myserver;Database=mydb;Integrated Security=True;")

        st.markdown("<p style='font-size:12px;color:#6e7681;margin:8px 0 4px'>Quick Templates</p>", unsafe_allow_html=True)
        tpl = st.selectbox("", [
            "— Select template —",
            "Windows Auth (Local)",
            "Windows Auth (Remote)",
            "SQL Server Auth",
            "Azure SQL",
            "LocalDB",
        ], label_visibility="collapsed")

        templates = {
            "Windows Auth (Local)":  "Server=localhost;Database=mydb;Integrated Security=True;TrustServerCertificate=True;",
            "Windows Auth (Remote)": "Server=myserver\\INSTANCE;Database=mydb;Integrated Security=True;TrustServerCertificate=True;",
            "SQL Server Auth":       "Server=myserver;Database=mydb;User Id=sa;Password=yourpassword;TrustServerCertificate=True;",
            "Azure SQL":             "Server=tcp:yourserver.database.windows.net,1433;Database=mydb;User Id=user@server;Password=yourpassword;Encrypt=True;",
            "LocalDB":               "Server=(localdb)\\MSSQLLocalDB;Database=mydb;Integrated Security=True;",
        }
        if tpl in templates:
            st.code(templates[tpl], language="text")

        b1, b2 = st.columns(2)
        if b1.button("Add Connection", use_container_width=True):
            if lbl and cs:
                cid = re.sub(r"\s+","-",lbl.strip().lower())
                st.session_state["connections"][cid] = {"label":lbl,"connection_string":cs,"added_at":datetime.now().strftime("%Y-%m-%d %H:%M")}
                if not st.session_state["active_conn_id"]:
                    st.session_state["active_conn_id"] = cid
                st.session_state["schema_cache"] = None; _save()
                st.success(f"✅ '{lbl}' added"); st.rerun()
            else: st.error("Label and connection string required")

        if b2.button("Add & Activate", use_container_width=True, type="primary"):
            if lbl and cs:
                cid = re.sub(r"\s+","-",lbl.strip().lower())
                st.session_state["connections"][cid] = {"label":lbl,"connection_string":cs,"added_at":datetime.now().strftime("%Y-%m-%d %H:%M")}
                st.session_state["active_conn_id"] = cid
                st.session_state["schema_cache"] = None; _save()
                st.success(f"✅ '{lbl}' added and activated"); st.rerun()

        st.markdown("</div></div>", unsafe_allow_html=True)

        # ── AI Settings ───────────────────────────────────────────────────
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        with st.expander("⚙️ Azure OpenAI Settings"):
            cfg = st.session_state["ai_cfg"]
            ep  = st.text_input("Endpoint URL", value=cfg["endpoint"])
            key = st.text_input("API Key", value=cfg["api_key"], type="password",
                               placeholder="Paste your Azure OpenAI API key")
            c1,c2 = st.columns(2)
            mdl = c1.text_input("Model",   value=cfg["model"])
            ver = c2.text_input("API Ver", value=cfg["api_version"])
            if st.button("💾 Save AI Settings", use_container_width=True):
                st.session_state["ai_cfg"].update({"endpoint":ep,"api_key":key,"model":mdl,"api_version":ver})
                _save(); st.success("✅ Settings saved")
            if st.button("🔌 Test AI Connection", use_container_width=True):
                ag = _agent()
                if ag:
                    with st.spinner():
                        try: st.success(f"✅ AI Connected — {ag.test()[:50]}")
                        except Exception as ex: st.error(str(ex))
                else: st.warning("Enter endpoint + API key first")

    with right:
        # ── Connection list ───────────────────────────────────────────────
        st.markdown("""
        <div class="section-card">
            <div class="section-card-header">
                <span class="section-card-title">Saved Connections</span>
            </div>
        """, unsafe_allow_html=True)

        conns = st.session_state["connections"]
        if not conns:
            st.markdown("""
            <div style='padding:40px;text-align:center;color:#6e7681'>
                <div style='font-size:32px;margin-bottom:12px'>🔌</div>
                <div style='font-weight:600;margin-bottom:6px'>No connections yet</div>
                <div style='font-size:13px'>Add a connection using the form on the left</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            for cid, c in list(conns.items()):
                is_a = cid == st.session_state["active_conn_id"]
                bg   = "#f0f7ff" if is_a else "#fff"
                border = "#1f6feb" if is_a else "#e1e4e8"
                st.markdown(f"""
                <div style='background:{bg};border:1px solid {border};border-radius:8px;
                padding:14px 18px;margin-bottom:10px'>
                    <div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:8px'>
                        <div style='display:flex;align-items:center;gap:10px'>
                            <span class='{'conn-dot-green' if is_a else 'conn-dot-gray'}'></span>
                            <span style='font-size:15px;font-weight:600;color:#1a1a2e'>{c['label']}</span>
                            {"<span class='badge badge-blue'>Active</span>" if is_a else ""}
                        </div>
                    </div>
                    <div style='font-size:11px;color:#6e7681;font-family:monospace;
                    background:#f6f8fa;padding:6px 10px;border-radius:4px;margin-bottom:10px;
                    overflow:hidden;text-overflow:ellipsis;white-space:nowrap'>
                        {re.sub(r'(Password|Pwd|PWD)\s*=\s*[^;]+','\\1=*****',c['connection_string'])}
                    </div>
                    <div style='font-size:11px;color:#8b949e'>Added: {c.get('added_at','—')}</div>
                </div>
                """, unsafe_allow_html=True)

                ca, cb, cc_btn, cd = st.columns([2,2,2,2])
                if not is_a:
                    if ca.button("✅ Set Active", key=f"act_{cid}", use_container_width=True, type="primary"):
                        st.session_state["active_conn_id"] = cid
                        st.session_state["schema_cache"] = None; _save(); st.rerun()
                else:
                    ca.markdown("<span class='badge badge-green' style='display:block;text-align:center;padding:8px'>● Active</span>", unsafe_allow_html=True)

                if cb.button("🔌 Test", key=f"tst_{cid}", use_container_width=True):
                    c2_obj = _conn(cid)
                    if c2_obj:
                        with st.spinner("Testing…"):
                            ok, info = c2_obj.test_connection()
                            if ok:
                                st.success(f"✅ **{info['server']}** / **{info['database']}** | User: {info['user']}")
                            else:
                                st.error(f"❌ {info}")

                if cc_btn.button("🔄 Schema", key=f"sch_{cid}", use_container_width=True):
                    if cid == st.session_state["active_conn_id"]:
                        st.session_state["schema_cache"] = None; _load_schema()
                        st.success("✅ Schema cache refreshed")

                if cd.button("🗑️ Delete", key=f"del_{cid}", use_container_width=True):
                    del st.session_state["connections"][cid]
                    if st.session_state["active_conn_id"] == cid:
                        rem = list(st.session_state["connections"].keys())
                        st.session_state["active_conn_id"] = rem[0] if rem else None
                    st.session_state["schema_cache"] = None; _save(); st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

        # ── Connection string reference ───────────────────────────────────
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        with st.expander("📖 Connection String Reference"):
            st.markdown("""
| Type | Format |
|------|--------|
| **Windows Auth** | `Server=HOST;Database=DB;Integrated Security=True;TrustServerCertificate=True;` |
| **SQL Auth** | `Server=HOST;Database=DB;User Id=USER;Password=PASS;TrustServerCertificate=True;` |
| **Named Instance** | `Server=HOST\\INSTANCE;Database=DB;Integrated Security=True;` |
| **Azure SQL** | `Server=tcp:HOST.database.windows.net,1433;Database=DB;User Id=USER;Password=PASS;Encrypt=True;` |
| **LocalDB** | `Server=(localdb)\\MSSQLLocalDB;Database=DB;Integrated Security=True;` |
| **Port** | `Server=HOST,1433;Database=DB;User Id=USER;Password=PASS;` |
            """)

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: METADATA EXPLORER
# ═════════════════════════════════════════════════════════════════════════════
elif page == "metadata":
    page_header("Metadata Explorer", "Browse tables, procedures, functions, triggers, and views", "connected" if active_c else "disconnected")
    c = _conn()
    if not c: st.warning("⚠️ Connect to a database in **Database Manager** first."); st.stop()

    from modules.schema_analyzer import SchemaAnalyzer
    sa = SchemaAnalyzer(c)
    t1,t2,t3,t4,t5,t6 = st.tabs(["📋 Tables & Columns","🔍 Stored Procedures","⚡ Functions","🔔 Triggers","👁️ Views","🤖 AI Analysis"])

    with t1:
        if st.button("🔄 Load Tables & Columns", type="primary"):
            with st.spinner(): st.session_state["me_tables"] = sa.get_tables()
        if "me_tables" in st.session_state:
            df = st.session_state["me_tables"]
            c1,c2,c3 = st.columns(3, gap="medium")
            with c1: metric_card("Tables",     len(df[df["Type"]=="BASE TABLE"]))
            with c2: metric_card("Views",      len(df[df["Type"]=="VIEW"]))
            with c3: metric_card("Total Rows", f"{df[df['Type']=='BASE TABLE']['Row Count'].sum():,}")
            st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
            st.dataframe(df, use_container_width=True, height=280, hide_index=True)
            sel = st.selectbox("🔍 Inspect columns for table:", [""]+df["Table"].tolist())
            if sel:
                sch = df[df["Table"]==sel]["Schema"].iloc[0]
                with st.spinner(): cols_df = sa.get_columns(sch, sel)
                st.dataframe(cols_df, use_container_width=True, hide_index=True)

    with t2:
        if not _can("sp_analyzer"):
            st.info("🔒 Developer, DBA, or Admin role required.")
        else:
            if st.button("🔄 Load Stored Procedures", type="primary"):
                with st.spinner(): st.session_state["me_sps"] = sa.get_stored_procedures()
            if "me_sps" in st.session_state:
                sp_df = st.session_state["me_sps"]
                metric_card("Stored Procedures", len(sp_df))
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                st.dataframe(sp_df, use_container_width=True, height=240, hide_index=True)
                sel = st.selectbox("Select procedure:", [""]+[f"{r['Schema']}.{r['Procedure']}" for _,r in sp_df.iterrows()])
                if sel:
                    sc,pn = sel.split(".",1); sp_def = sa.get_sp_definition(sc, pn)
                    d1,d2,d3 = st.tabs(["📄 Definition","💡 Business Explanation","⚡ Performance Optimization"])
                    with d1: st.code(sp_def, language="sql")
                    with d2:
                        if st.button("🤖 Explain in Business Terms", type="primary"):
                            ag=_agent()
                            if ag:
                                with st.spinner("AI analyzing…"):
                                    r=ag.chat([{"role":"user","content":f"Explain this stored procedure in business terms.\nCover: purpose, parameters, output, key operations, calling context.\n```sql\n{sp_def}\n```"}])
                                    st.markdown(r)
                    with d3:
                        if st.button("⚡ Deep Performance Analysis", type="primary"):
                            ag=_agent()
                            if ag:
                                with st.spinner("AI optimizing…"):
                                    r=ag.chat([{"role":"user","content":f"Deep performance analysis of this SQL Server SP.\n🔴 Critical Issues | 🟡 Anti-Patterns | 🟢 Optimized SQL | 📊 Missing Indexes | 💡 Best Practices\n```sql\n{sp_def}\n```"}])
                                    st.markdown(r)

    with t3:
        if not _can("function_explorer"):
            st.info("🔒 Developer role or higher required.")
        else:
            if st.button("🔄 Load Functions", type="primary", key="fn_load"):
                with st.spinner(): st.session_state["me_fns"] = sa.get_functions()
            if "me_fns" in st.session_state:
                fn_df = st.session_state["me_fns"]
                metric_card("User-Defined Functions", len(fn_df))
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                st.dataframe(fn_df, use_container_width=True, height=230, hide_index=True)
                sel = st.selectbox("Select function:", [""]+[f"{r['Schema']}.{r['Function']}" for _,r in fn_df.iterrows()])
                if sel:
                    sc,fn = sel.split(".",1); fn_def = sa.get_function_definition(sc, fn)
                    ft1,ft2 = st.tabs(["📄 Definition","🤖 Analysis"])
                    with ft1: st.code(fn_def, language="sql")
                    with ft2:
                        if st.button("🤖 Analyze Function", type="primary"):
                            ag=_agent()
                            if ag:
                                with st.spinner():
                                    from modules.agents.orchestrator import AgentOrchestrator
                                    r=AgentOrchestrator(ag).analyze_function(fn_def)
                                    st.markdown(r)

    with t4:
        if not _can("trigger_explorer"):
            st.info("🔒 Developer role or higher required.")
        else:
            if st.button("🔄 Load Triggers", type="primary", key="tr_load"):
                with st.spinner(): st.session_state["me_trigs"] = sa.get_triggers()
            if "me_trigs" in st.session_state:
                tr_df = st.session_state["me_trigs"]
                if tr_df.empty: st.info("No DML triggers found.")
                else:
                    c1,c2,c3 = st.columns(3, gap="medium")
                    with c1: metric_card("Total Triggers", len(tr_df))
                    with c2: metric_card("Enabled", len(tr_df[tr_df["Status"]=="Enabled"]), color="#1a7f37")
                    with c3: metric_card("Disabled", len(tr_df[tr_df["Status"]=="Disabled"]), color="#cf222e")
                    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                    st.dataframe(tr_df, use_container_width=True, height=250, hide_index=True)
                    sel = st.selectbox("Select trigger:", [""]+tr_df["Trigger"].tolist())
                    if sel:
                        tr_def = sa.get_trigger_definition(sel)
                        tt1,tt2 = st.tabs(["📄 Definition","🤖 Analysis"])
                        with tt1: st.code(tr_def, language="sql")
                        with tt2:
                            if st.button("🤖 Analyze Trigger", type="primary"):
                                ag=_agent()
                                if ag:
                                    with st.spinner():
                                        from modules.agents.orchestrator import AgentOrchestrator
                                        r=AgentOrchestrator(ag).analyze_trigger(tr_def)
                                        st.markdown(r)

    with t5:
        if st.button("🔄 Load Views", type="primary", key="vw_load"):
            with st.spinner(): st.session_state["me_views"] = sa.get_views()
        if "me_views" in st.session_state:
            vw_df = st.session_state["me_views"]
            metric_card("Views", len(vw_df))
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            st.dataframe(vw_df, use_container_width=True, height=240, hide_index=True)
            sel = st.selectbox("Select view:", [""]+[f"{r['Schema']}.{r['View']}" for _,r in vw_df.iterrows()])
            if sel:
                sc,vn = sel.split(".",1)
                st.code(sa.get_view_definition(sc, vn), language="sql")

    with t6:
        st.markdown("#### 🧠 AI-Powered Full Schema Analysis")
        if st.button("Analyze Entire Database Schema", type="primary", use_container_width=True):
            ag=_agent()
            if ag:
                _load_schema()
                with st.spinner("AI analyzing complete schema…"):
                    r=ag.chat([{"role":"user","content":
                        "Analyze this SQL Server database schema comprehensively:\n"
                        "1. **Business Domain** — industry/system type\n"
                        "2. **Key Entities** — purpose of each major table\n"
                        "3. **Data Relationships** — how entities connect\n"
                        "4. **Normalization Assessment** — 1NF/2NF/3NF\n"
                        "5. **Data Quality Risks** — nullable PKs, missing constraints\n"
                        "6. **Architectural Recommendations** — improvements"}],
                        schema_context=st.session_state.get("schema_cache"))
                    st.markdown(r)
            else: st.error("Configure Azure OpenAI settings in Database Manager first.")

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: RELATIONSHIP MAPPER
# ═════════════════════════════════════════════════════════════════════════════
elif page == "relationships":
    page_header("Relationship Mapper", "FK/PK analysis, ER diagrams, orphan detection, and AI-suggested relationships", "connected" if active_c else "disconnected")
    c = _conn()
    if not c: st.warning("⚠️ Connect to a database in **Database Manager** first."); st.stop()

    from modules.relationship_analyzer import RelationshipAnalyzer
    ra = RelationshipAnalyzer(c)
    r1,r2,r3,r4 = st.tabs(["🔗 FK Relationships & ER Diagram","🔴 Orphan Tables","🔎 Join Candidates","🤖 AI Suggested FKs"])

    with r1:
        if st.button("🔄 Load Relationships", type="primary"):
            with st.spinner(): st.session_state["rm_fk"] = ra.get_relationships()
        if "rm_fk" in st.session_state:
            fk = st.session_state["rm_fk"]
            if fk.empty:
                st.info("No foreign key relationships defined. Use **AI Suggested FKs** tab to discover potential relationships.")
            else:
                metric_card("Foreign Key Constraints", len(fk))
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                st.dataframe(fk, use_container_width=True, height=300, hide_index=True)
                st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

                # ER Diagram
                st.markdown("#### 📐 Entity Relationship Diagram (Mermaid)")
                mermaid_code = ra.generate_mermaid()
                c1, c2 = st.columns([1,1])
                with c1:
                    st.code(mermaid_code, language="text")
                    st.caption("Copy and paste into https://mermaid.live to render")
                with c2:
                    mermaid_html = f"""<!DOCTYPE html><html>
                    <body style="background:#0d1117;margin:0;padding:10px">
                    <div class="mermaid">{mermaid_code}</div>
                    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
                    <script>mermaid.initialize({{startOnLoad:true,theme:'dark',securityLevel:'loose'}});</script>
                    </body></html>"""
                    st.components.v1.html(mermaid_html, height=400, scrolling=True)

                st.markdown("#### 🔍 Trace Dependencies")
                all_tables = sorted(set(fk["Parent Table"].tolist()+fk["Ref Table"].tolist()))
                sel = st.selectbox("Select table:", [""]+all_tables, key="dep_sel")
                if sel:
                    sch_v = fk[fk["Parent Table"]==sel]["Parent Schema"]
                    sc2 = sch_v.values[0] if len(sch_v) else "dbo"
                    dep_df = ra.get_dependency_chain(sc2, sel)
                    st.dataframe(dep_df, use_container_width=True, hide_index=True)

    with r2:
        st.markdown("Tables with no foreign key relationships — potential data islands.")
        if st.button("🔍 Find Orphan Tables", type="primary"):
            with st.spinner(): st.session_state["rm_orp"] = ra.get_orphan_tables()
        if "rm_orp" in st.session_state:
            orp = st.session_state["rm_orp"]
            if orp.empty: st.success("✅ All tables participate in foreign key relationships.")
            else:
                metric_card("Orphan Tables (No FK)", len(orp), color="#cf222e")
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                st.dataframe(orp, use_container_width=True, hide_index=True)

    with r3:
        st.markdown("Columns with matching names and data types across different tables — likely foreign key candidates.")
        if st.button("🔍 Detect Join Candidates", type="primary"):
            with st.spinner(): st.session_state["rm_jc"] = ra.get_join_candidates()
        if "rm_jc" in st.session_state:
            jc = st.session_state["rm_jc"]
            if jc.empty: st.info("No join candidates found.")
            else:
                missing = jc[jc["FK Status"].str.contains("No FK", na=False)]
                c1,c2 = st.columns(2, gap="medium")
                with c1: metric_card("Total Candidates", len(jc))
                with c2: metric_card("Missing FK", len(missing), color="#cf222e")
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                st.dataframe(jc, use_container_width=True, height=350, hide_index=True)

    with r4:
        st.markdown("AI analyzes column names, naming conventions, and data types to suggest missing foreign key relationships.")
        if st.button("🤖 Analyze & Suggest Relationships", type="primary", use_container_width=True):
            ag=_agent()
            if ag:
                _load_schema()
                with st.spinner("AI analyzing schema for potential relationships…"):
                    from modules.agents.orchestrator import AgentOrchestrator
                    res = AgentOrchestrator(ag).suggest_relationships(st.session_state.get("schema_cache",""))
                    st.session_state["rm_sugg"] = res
            else: st.error("Configure Azure OpenAI in Database Manager first.")

        if "rm_sugg" in st.session_state:
            s = st.session_state["rm_sugg"]
            issues  = s.get("design_issues",[])
            suggs   = s.get("suggested_relationships",[])
            recs    = s.get("recommendations",[])

            if issues:
                st.markdown("#### ⚠️ Design Issues Detected")
                for i in issues: st.markdown(f"- {i}")
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

            if suggs:
                st.markdown(f"#### 💡 {len(suggs)} Suggested Relationships")
                c1,c2,c3 = st.columns(3,gap="medium")
                high = [x for x in suggs if float(x.get("confidence",0))>=0.8]
                med  = [x for x in suggs if 0.5<=float(x.get("confidence",0))<0.8]
                low  = [x for x in suggs if float(x.get("confidence",0))<0.5]
                with c1: metric_card("High Confidence (≥80%)", len(high), color="#1a7f37")
                with c2: metric_card("Medium (50–79%)",         len(med),  color="#9a6700")
                with c3: metric_card("Low (<50%)",              len(low),  color="#cf222e")
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

                for i, s2 in enumerate(suggs):
                    conf = float(s2.get("confidence",0.5))
                    ico  = "🟢" if conf>=0.8 else "🟡" if conf>=0.5 else "🔴"
                    with st.expander(
                        f"{ico} [{s2.get('parent_table','')}].[{s2.get('parent_column','')}] → "
                        f"[{s2.get('ref_table','')}].[{s2.get('ref_column','')}] — {conf:.0%} confidence",
                        expanded=conf>=0.8
                    ):
                        st.markdown(f"**Reason:** {s2.get('reason','')}")
                        alter_sql = s2.get("alter_sql","")
                        if not alter_sql:
                            from modules.relationship_analyzer import RelationshipAnalyzer as RA2
                            pt=s2.get("parent_table",""); rt=s2.get("ref_table","")
                            ps=pt.split(".")[0] if "." in pt else "dbo"
                            rs=rt.split(".")[0] if "." in rt else "dbo"
                            alter_sql=RA2.generate_fk_sql(ps,pt.split(".")[-1],s2.get("parent_column",""),rs,rt.split(".")[-1],s2.get("ref_column",""))
                        st.code(alter_sql, language="sql")
                        st.caption("⚠️ Test in non-production first. Execute via SSMS or your preferred DB tool.")

            if recs:
                st.markdown("#### 📋 Design Recommendations")
                for r2 in recs: st.markdown(f"- {r2}")

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: AI ASSISTANT
# ═════════════════════════════════════════════════════════════════════════════
elif page == "ai_chat":
    page_header("AI Assistant", "6-Agent Pipeline: Schema → SQL → Validation → Optimization → Explanation → Visualization", "connected" if active_c else "disconnected")

    opt_col = st.columns([2,2,2,1,1])
    use_pipe  = opt_col[0].checkbox("🤖 Multi-Agent Pipeline", value=True)
    use_sch   = opt_col[1].checkbox("📋 Include Schema Context", value=True)
    auto_exec = opt_col[2].checkbox("▶️ Auto-Execute SQL", value=False)
    if opt_col[3].button("🗑️ Clear Chat"): st.session_state["chat_history"]=[]; st.rerun()

    # Chat history
    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask anything — 'Show top customers by revenue', 'Explain the Orders table', 'What indexes are missing?'"):
        if not st.session_state["ai_cfg"].get("api_key"):
            st.error("❌ Configure Azure OpenAI settings in **Database Manager** first.")
        else:
            st.session_state["chat_history"].append({"role":"user","content":prompt})
            with st.chat_message("user"): st.markdown(prompt)
            if use_sch: _load_schema()

            with st.chat_message("assistant"):
                if use_pipe:
                    orch = _orch()
                    if not orch: st.error("AI not configured.")
                    else:
                        with st.spinner("Running multi-agent pipeline…"):
                            result = orch.run_pipeline(prompt)

                        # Pipeline visualization
                        st.markdown("**Agent Pipeline**")
                        pcols = st.columns(len(result.steps))
                        for i, step in enumerate(result.steps):
                            ico = {"success":"✅","error":"❌","warning":"⚠️"}.get(step.status,"⏳")
                            bk  = "#e6f4ea" if step.status=="success" else "#ffebe9" if step.status=="error" else "#f6f8fa"
                            pcols[i].markdown(f"""
                            <div style='background:{bk};border-radius:8px;padding:10px;text-align:center;font-size:12px'>
                                <div style='font-weight:600;color:#1a1a2e;margin-bottom:4px'>{step.agent}</div>
                                <div>{ico} {step.status}</div>
                                <div style='color:#6e7681'>{step.duration_ms}ms</div>
                            </div>""", unsafe_allow_html=True)

                        if not result.success:
                            st.error(f"Pipeline failed: {result.error}")
                        else:
                            for step in result.steps:
                                if not step.output: continue
                                ico = {"success":"✅","error":"❌","warning":"⚠️"}.get(step.status,"⏳")
                                with st.expander(f"{ico} {step.agent} — {step.duration_ms}ms"):
                                    out = {k:v for k,v in step.output.items()
                                           if k not in ("sql","optimized_sql","corrected_sql","_raw") and v}
                                    for k,v in out.items():
                                        if isinstance(v,list): st.markdown(f"**{k}:** {', '.join(str(x) for x in v)}")
                                        else: st.markdown(f"**{k}:** {v}")
                                    for sk in ("optimized_sql","corrected_sql","sql"):
                                        s = step.output.get(sk)
                                        if s: st.code(s, language="sql"); break

                            st.markdown("---")
                            st.markdown("#### 📝 Generated T-SQL")
                            st.code(result.final_sql, language="sql")

                            if result.index_suggestions:
                                st.markdown("#### 💡 Index Recommendations")
                                for si in result.index_suggestions:
                                    st.code(si, language="sql")
                                    if _can("apply_indexes"):
                                        if st.button(f"✅ Apply", key=f"ap_{hash(si)}", type="primary"):
                                            try: st.success(_conn().execute_ddl(si))
                                            except Exception as ex: st.error(str(ex))

                            if auto_exec and st.session_state["active_conn_id"]:
                                try:
                                    df_r = _conn().execute_query(result.final_sql)
                                    st.success(f"✅ {len(df_r):,} rows returned")
                                    st.dataframe(df_r, use_container_width=True, height=min(400,len(df_r)*38+50), hide_index=True)
                                    with st.spinner("Generating business insights…"):
                                        ev = orch.explain_and_visualize(result.final_sql, df_r.head(50).to_json(orient="records"), prompt)
                                    exp = ev.get("explanation",{}); viz = ev.get("visualization",{})
                                    if exp.get("summary"):
                                        st.markdown("#### 📊 Business Insights")
                                        st.markdown(f"**{exp['summary']}**")
                                        for kf in exp.get("key_findings",[]): st.markdown(f"• {kf}")
                                        for rec in exp.get("recommendations",[]): st.info(f"💡 {rec}")
                                    if viz.get("chart_type","table")!="table":
                                        fig = _chart(df_r, viz)
                                        if fig: st.plotly_chart(fig, use_container_width=True)
                                    if _can("export_csv"):
                                        st.download_button("⬇️ Export CSV", df_r.to_csv(index=False).encode(),"results.csv","text/csv")
                                    # Save to history
                                    st.session_state["query_history"].append({
                                        "Time": datetime.now().strftime("%H:%M:%S"),
                                        "Question": prompt[:60]+"…",
                                        "Rows": len(df_r), "Status": "✅ Success"
                                    })
                                except Exception as ex: st.warning(f"Auto-execute: {ex}")

                            st.session_state["chat_history"].append({"role":"assistant","content":
                                f"**Pipeline:** {len(result.steps)} agents\n\n**SQL:**\n```sql\n{result.final_sql}\n```"})
                else:
                    ag = _agent()
                    if ag:
                        with st.spinner("Thinking…"):
                            resp = ag.chat(st.session_state["chat_history"][-12:], schema_context=st.session_state.get("schema_cache"))
                            st.markdown(resp)
                            st.session_state["chat_history"].append({"role":"assistant","content":resp})

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: QUERY STUDIO
# ═════════════════════════════════════════════════════════════════════════════
elif page == "query_studio":
    page_header("Query Studio", "Natural language to optimized T-SQL · Direct SQL editor · Export results", "connected" if active_c else "disconnected")

    qs1, qs2 = st.tabs(["🤖 Natural Language → T-SQL", "📝 SQL Editor"])

    with qs1:
        nl = st.text_area("Describe what you need:", height=100,
                         placeholder="e.g. Show the top 10 customers by total order value this quarter, grouped by region")
        c1,c2 = st.columns([3,1])
        row_lim = c1.slider("MAX rows (TOP clause):", 10, 10000, 100, 10)
        gen = c2.button("🤖 Generate SQL", type="primary", use_container_width=True)

        if gen and nl.strip():
            ag = _agent()
            if not ag: st.error("Configure Azure OpenAI in **Database Manager** first.")
            else:
                _load_schema()
                with st.spinner("Multi-agent SQL generation…"):
                    from modules.agents.orchestrator import AgentOrchestrator
                    orch = AgentOrchestrator(ag, st.session_state.get("schema_cache",""), _role())
                    res = orch.run_pipeline(nl + f"\n\n[Requirement: apply TOP {row_lim}]")

                if res.success:
                    st.session_state["qs_sql"] = res.final_sql
                    st.markdown("#### Generated & Optimized T-SQL")
                    st.code(res.final_sql, language="sql")
                    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                    agent_cols = st.columns(len(res.steps))
                    for i, step in enumerate(res.steps):
                        ico = {"success":"✅","error":"❌","warning":"⚠️"}.get(step.status,"⏳")
                        agent_cols[i].caption(f"{ico} {step.agent} · {step.duration_ms}ms")
                    if res.index_suggestions:
                        with st.expander(f"💡 {len(res.index_suggestions)} Index Suggestion(s)"):
                            for si in res.index_suggestions: st.code(si, language="sql")
                else:
                    st.error(f"Pipeline error: {res.error}")

        if "qs_sql" in st.session_state:
            st.markdown("#### Edit & Execute")
            edited = st.text_area("", value=st.session_state["qs_sql"], height=200, key="qs_edit", label_visibility="collapsed")
            c1,c2,c3 = st.columns([1,1,4])
            if c1.button("▶️ Execute", type="primary", use_container_width=True):
                if not st.session_state["active_conn_id"]: st.error("No active database connection.")
                else:
                    with st.spinner("Executing…"):
                        try:
                            df = _conn().execute_query(edited)
                            st.success(f"✅ {len(df):,} rows returned")
                            st.dataframe(df, use_container_width=True, height=min(400,len(df)*38+50), hide_index=True)
                            if _can("export_csv"):
                                st.download_button("⬇️ Export CSV", df.to_csv(index=False).encode(),"results.csv","text/csv")
                            st.session_state["query_history"].append({
                                "Time": datetime.now().strftime("%H:%M:%S"),
                                "Question": nl[:60]+"…" if nl else "Direct SQL",
                                "Rows": len(df), "Status": "✅ Success"
                            })
                        except Exception as ex: st.error(str(ex))
            if c2.button("🗑️ Clear", use_container_width=True):
                del st.session_state["qs_sql"]; st.rerun()

    with qs2:
        direct = st.text_area("T-SQL Query:", height=300,
                              placeholder="-- Write your T-SQL here\nSELECT TOP 100 ...",
                              key="direct_sql", label_visibility="collapsed")
        c1,c2 = st.columns([1,5])
        if c1.button("▶️ Execute SQL", type="primary", use_container_width=True, key="exec_d"):
            if not st.session_state["active_conn_id"]: st.error("No active database connection.")
            elif direct.strip():
                with st.spinner("Executing…"):
                    try:
                        df = _conn().execute_query(direct)
                        st.success(f"✅ {len(df):,} rows returned")
                        st.dataframe(df, use_container_width=True, height=400, hide_index=True)
                        if _can("export_csv"):
                            st.download_button("⬇️ Export CSV", df.to_csv(index=False).encode(),"results.csv","text/csv")
                    except Exception as ex: st.error(str(ex))

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: INDEX INTELLIGENCE
# ═════════════════════════════════════════════════════════════════════════════
elif page == "index_intel":
    page_header("Index Intelligence", "DMV-based analysis: missing, unused, and duplicate indexes with AI impact analysis", "connected" if active_c else "disconnected")
    c = _conn()
    if not c: st.warning("⚠️ Connect to a database in **Database Manager** first."); st.stop()

    from modules.index_advisor import IndexAdvisor
    ia = IndexAdvisor(c)
    i1,i2,i3 = st.tabs(["🔴 Missing Indexes","🟡 Unused Indexes","🔵 Duplicate Indexes"])

    with i1:
        st.markdown("Recommendations from `sys.dm_db_missing_index_details` — sorted by impact score.")
        if st.button("🔍 Analyze Missing Indexes", type="primary"):
            with st.spinner("Querying SQL Server DMVs…"): st.session_state["ii_miss"] = ia.get_missing_indexes()

        if "ii_miss" in st.session_state:
            mdf = st.session_state["ii_miss"]
            if "Error" in mdf.columns: st.error(mdf["Error"].iloc[0])
            elif mdf.empty: st.success("✅ No missing index recommendations.")
            else:
                c1,c2,c3,c4 = st.columns(4, gap="medium")
                with c1: metric_card("Recommendations", len(mdf))
                with c2: metric_card("Max Impact Score", f"{mdf['Impact Score'].max():,.0f}", color="#cf222e")
                with c3: metric_card("Avg Impact %",     f"{mdf['Avg Impact %'].mean():.1f}%", color="#9a6700")
                with c4: metric_card("Total Seeks",      f"{mdf['Seeks'].sum():,}", color="#1f6feb")
                st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

                show = [col for col in mdf.columns if col!="Suggested SQL"]
                st.dataframe(mdf[show], use_container_width=True, height=260, hide_index=True)
                try:
                    fig = px.bar(mdf.head(10), x="Table", y="Impact Score", color="Avg Impact %",
                                 title="Top 10 Index Recommendations by Impact",
                                 template="plotly_white",
                                 color_continuous_scale="RdYlGn")
                    st.plotly_chart(fig, use_container_width=True)
                except Exception: pass

                st.markdown("#### Review & Apply")
                pick = st.selectbox("Select index to review:",range(len(mdf)),
                    format_func=lambda i: f"#{i+1}  Impact:{mdf['Impact Score'].iloc[i]:,.0f}  |  {mdf['Table'].iloc[i]}  |  Avg: {mdf['Avg Impact %'].iloc[i]}%")
                sql_s = mdf["Suggested SQL"].iloc[pick]
                st.code(sql_s, language="sql")

                b1,b2 = st.columns(2)
                if b1.button("🤖 Explain Business Impact", use_container_width=True):
                    ag=_agent()
                    if ag:
                        with st.spinner():
                            r=ag.chat([{"role":"user","content":
                                f"Explain the business impact of adding this SQL Server index.\n"
                                f"Stats: Impact={mdf['Impact Score'].iloc[pick]:,.0f}, Seeks={mdf['Seeks'].iloc[pick]}, Avg Improvement={mdf['Avg Impact %'].iloc[pick]}%\n"
                                f"```sql\n{sql_s}\n```\nExplain: queries that benefit, storage cost, write overhead, maintenance."}])
                            st.markdown(r)

                if _can("apply_indexes"):
                    if b2.button("✅ Apply This Index", type="primary", use_container_width=True):
                        st.session_state["ii_pending"] = sql_s

                if "ii_pending" in st.session_state:
                    st.markdown("""
                    <div style='background:#fff8c5;border:1px solid #f0e17a;border-radius:8px;padding:16px;margin:12px 0'>
                        <b style='color:#9a6700'>⚠️ Confirm DDL Execution</b><br>
                        <span style='color:#6e7681;font-size:13px'>This will execute CREATE INDEX on your live database. 
                        Ensure you have a backup and sufficient maintenance window.</span>
                    </div>
                    """, unsafe_allow_html=True)
                    y,n = st.columns(2)
                    if y.button("✅ Confirm — Create Index", type="primary", use_container_width=True):
                        with st.spinner("Creating index…"):
                            r2 = ia.apply_index(st.session_state["ii_pending"])
                            st.success(r2)
                            del st.session_state["ii_pending"]
                            st.session_state.pop("ii_miss",None); st.rerun()
                    if n.button("❌ Cancel", use_container_width=True):
                        del st.session_state["ii_pending"]; st.rerun()

    with i2:
        st.markdown("Indexes that incur write overhead but have zero reads — candidates for removal.")
        if st.button("🔍 Find Unused Indexes", type="primary", key="iu_btn"):
            with st.spinner(): st.session_state["ii_unused"] = ia.get_unused_indexes()
        if "ii_unused" in st.session_state:
            udf = st.session_state["ii_unused"]
            if "Error" in udf.columns: st.error(udf["Error"].iloc[0])
            elif udf.empty: st.success("✅ No purely unused indexes found.")
            else:
                c1,c2 = st.columns(2,gap="medium")
                with c1: metric_card("Unused Indexes", len(udf), color="#cf222e")
                with c2: metric_card("Total Write Overhead", f"{udf['Write Cost'].sum():,}", color="#9a6700")
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                show = [col for col in udf.columns if "Drop SQL" not in col]
                st.dataframe(udf[show], use_container_width=True, hide_index=True)
                if st.button("🤖 AI Review — Which to Drop?", use_container_width=True):
                    ag=_agent()
                    if ag:
                        with st.spinner():
                            r=ag.chat([{"role":"user","content":
                                f"Review these unused SQL Server indexes. Which are safe to drop?\n"
                                f"{udf[['Table','Index Name','Write Cost']].to_string()}\n"
                                f"Consider: FK enforcement, statistics, replication, weekend-only queries."}])
                            st.markdown(r)

    with i3:
        st.markdown("Indexes with identical key columns on the same table — redundant and wasteful.")
        if st.button("🔍 Find Duplicate Indexes", type="primary", key="id_btn"):
            with st.spinner(): st.session_state["ii_dup"] = ia.get_duplicate_indexes()
        if "ii_dup" in st.session_state:
            ddf = st.session_state["ii_dup"]
            if "Error" in ddf.columns: st.error(ddf["Error"].iloc[0])
            elif ddf.empty: st.success("✅ No duplicate indexes found.")
            else:
                metric_card("Duplicate Index Pairs", len(ddf), color="#cf222e")
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                st.dataframe(ddf, use_container_width=True, hide_index=True)

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: AI INSIGHTS DASHBOARD
# ═════════════════════════════════════════════════════════════════════════════
elif page == "ai_insights":
    page_header("AI Insights Dashboard",
                "Executive health score · Performance trends · AI recommendations",
                "connected" if active_c else "disconnected")
    if not active_c:
        st.warning("⚠️ Connect to a database in **Database Manager** first.")
        st.stop()

    from modules.health_monitor import HealthMonitor
    hm0 = HealthMonitor(_conn())

    if st.button("🔄 Refresh Dashboard", type="primary"):
        with st.spinner("Calculating metrics…"):
            st.session_state["ins_health"] = hm0.get_health_score()
            st.session_state["ins_conns"]  = hm0.get_active_connections()
            st.session_state["ins_waits"]  = hm0.get_wait_stats()
            st.session_state["ins_io"]     = hm0.get_disk_io()

    h0 = st.session_state.get("ins_health", {})
    if h0:
        score0 = h0["score"]; grade0 = h0["grade"]; color0 = h0["color"]
        cc1, cc2, cc3, cc4, cc5 = st.columns([2,1,1,1,1], gap="medium")
        with cc1:
            st.markdown(f"""
            <div style='background:{color0};border-radius:12px;padding:28px 24px;
            text-align:center;color:#fff;box-shadow:0 4px 16px rgba(0,0,0,.15)'>
                <div style='font-size:64px;font-weight:900;line-height:1'>{score0}</div>
                <div style='font-size:14px;font-weight:600;margin-top:8px;opacity:.9'>
                    HEALTH SCORE</div>
                <div style='font-size:28px;font-weight:800;margin-top:6px'>
                    Grade {grade0}</div>
            </div>""", unsafe_allow_html=True)
        conn_df0 = st.session_state.get("ins_conns", pd.DataFrame())
        wait_df0 = st.session_state.get("ins_waits", pd.DataFrame())
        with cc2: metric_card("Active Sessions",
            len(conn_df0) if not conn_df0.empty and "Error" not in conn_df0.columns else "—")
        with cc3: metric_card("Wait Types",
            len(wait_df0) if not wait_df0.empty and "Error" not in wait_df0.columns else "—",
            color="#9a6700")
        with cc4: metric_card("Critical Issues", len(h0.get("issues", [])), color="#cf222e")
        with cc5: metric_card("Warnings",         len(h0.get("warnings", [])), color="#9a6700")

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        for iss in h0.get("issues",  []): st.error(f"🔴 {iss}")
        for wrn in h0.get("warnings",[]): st.warning(f"🟡 {wrn}")

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        ch1, ch2 = st.columns(2, gap="medium")
        with ch1:
            if (not wait_df0.empty and "Error" not in wait_df0.columns
                    and "Wait Type" in wait_df0.columns):
                try:
                    fig = px.bar(wait_df0.head(10), x="Wait Type", y="Total Wait (ms)",
                                 color="Category", title="Top Wait Statistics",
                                 template="plotly_white",
                                 color_discrete_sequence=px.colors.qualitative.Set2)
                    fig.update_xaxes(tickangle=45)
                    st.plotly_chart(fig, use_container_width=True)
                except Exception: pass
        with ch2:
            io_df0 = st.session_state.get("ins_io", pd.DataFrame())
            if (not io_df0.empty and "Error" not in io_df0.columns
                    and "Total Stall (ms)" in io_df0.columns):
                try:
                    fig2 = px.bar(io_df0.head(10), x="Logical File", y="Total Stall (ms)",
                                  color="File Type", title="Disk I/O Stall by File",
                                  template="plotly_white",
                                  color_discrete_sequence=px.colors.qualitative.Pastel)
                    fig2.update_xaxes(tickangle=45)
                    st.plotly_chart(fig2, use_container_width=True)
                except Exception: pass

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    _, btn_col = st.columns([4, 1])
    if btn_col.button("🤖 AI Executive Report", type="primary", use_container_width=True):
        ag0 = _agent()
        if not ag0:
            st.error("Configure Azure OpenAI in Database Manager first.")
        else:
            _load_schema()
            with st.spinner("Generating AI executive report…"):
                ctx = []
                if h0:
                    ctx.append(f"Health Score: {h0.get('score',0)}/100  Grade: {h0.get('grade','?')}")
                    if h0.get("issues"):   ctx.append("Issues: " + "; ".join(h0["issues"]))
                    if h0.get("warnings"): ctx.append("Warnings: " + "; ".join(h0["warnings"]))
                w0 = st.session_state.get("ins_waits", pd.DataFrame())
                if not w0.empty and "Error" not in w0.columns and "Wait Type" in w0.columns:
                    ctx.append("Top wait types: " + ", ".join(w0["Wait Type"].head(5).tolist()))
                prompt = (
                    "Generate an executive-level SQL Server health report.\n\n"
                    "Context:\n" + "\n".join(ctx) + "\n\n"
                    "Schema:\n" + (st.session_state.get("schema_cache", "") or "N/A") + "\n\n"
                    "Sections:\n"
                    "## 1. Executive Summary\n"
                    "## 2. Health Score Assessment\n"
                    "## 3. Critical Issues & Root Causes\n"
                    "## 4. Top 5 Performance Recommendations\n"
                    "## 5. Resource & Capacity Outlook\n"
                    "## 6. Immediate Actions (this week)\n"
                    "## 7. 90-Day Roadmap"
                )
                st.session_state["ins_report"] = ag0.chat([{"role":"user","content":prompt}])

    if "ins_report" in st.session_state:
        st.markdown(st.session_state["ins_report"])
        st.download_button("⬇️ Download Report",
                           st.session_state["ins_report"].encode(),
                           "db_health_report.md", "text/markdown")

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: HEALTH MONITOR
# ═════════════════════════════════════════════════════════════════════════════
elif page == "health_monitor":
    page_header("Health Monitor",
                "Real-time CPU · Memory · I/O · Connections · Blocking",
                "connected" if active_c else "disconnected")
    c_hm = _conn()
    if not c_hm: st.warning("⚠️ Connect to a database in **Database Manager** first."); st.stop()

    from modules.health_monitor import HealthMonitor
    hm = HealthMonitor(c_hm)
    h1,h2,h3,h4,h5,h6 = st.tabs(
        ["👥 Active Sessions","⏳ Wait Stats","🔒 Blocking","💽 Disk I/O","🧠 Memory","🔥 Top Queries"])

    with h1:
        if st.button("🔄 Load Active Sessions", type="primary"):
            with st.spinner(): st.session_state["hm_sess"] = hm.get_active_connections()
        if "hm_sess" in st.session_state:
            df = st.session_state["hm_sess"]
            if "Error" in df.columns: st.error(df["Error"].iloc[0])
            else:
                c1,c2,c3 = st.columns(3, gap="medium")
                with c1: metric_card("Active Sessions", len(df))
                if "CPU (ms)" in df.columns:
                    with c2: metric_card("Total CPU (ms)", f"{df['CPU (ms)'].sum():,}", color="#cf222e")
                if "Reads" in df.columns:
                    with c3: metric_card("Total Reads", f"{df['Reads'].sum():,}", color="#1f6feb")
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                st.dataframe(df, use_container_width=True, height=350, hide_index=True)

    with h2:
        if st.button("🔄 Load Wait Stats", type="primary", key="hm_ws_btn"):
            with st.spinner(): st.session_state["hm_waits"] = hm.get_wait_stats()
        if "hm_waits" in st.session_state:
            df = st.session_state["hm_waits"]
            if "Error" in df.columns: st.error(df["Error"].iloc[0])
            else:
                st.dataframe(df, use_container_width=True, height=280, hide_index=True)
                try:
                    fig = px.bar(df.head(10), x="Wait Type", y="Total Wait (ms)",
                                 color="Category", title="Top Wait Statistics",
                                 template="plotly_white",
                                 color_discrete_sequence=px.colors.qualitative.Set2)
                    fig.update_xaxes(tickangle=45)
                    st.plotly_chart(fig, use_container_width=True)
                except Exception: pass
                if st.button("🤖 AI Wait Analysis", use_container_width=True, key="hm_ws_ai"):
                    ag = _agent()
                    if ag:
                        with st.spinner():
                            r = ag.chat([{"role":"user","content":
                                f"Analyze these SQL Server wait statistics. Explain each wait type, "
                                f"root cause, and provide actionable fixes:\n{df.to_string()}"}])
                            st.markdown(r)

    with h3:
        if st.button("🔄 Check Blocking", type="primary", key="hm_blk_btn"):
            with st.spinner(): st.session_state["hm_block"] = hm.get_blocking()
        if "hm_block" in st.session_state:
            df = st.session_state["hm_block"]
            if "Error" in df.columns: st.error(df["Error"].iloc[0])
            elif df.empty: st.success("✅ No active blocking detected.")
            else:
                metric_card("Active Blocking Chains", len(df), color="#cf222e")
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                st.dataframe(df, use_container_width=True, hide_index=True)
                if st.button("🤖 Explain & Resolve Blocking", use_container_width=True, key="hm_blk_ai"):
                    ag = _agent()
                    if ag:
                        with st.spinner():
                            r = ag.chat([{"role":"user","content":
                                f"Analyze this SQL Server blocking situation. Explain what is happening, "
                                f"which session is the blocker, and provide T-SQL resolution steps:\n{df.to_string()}"}])
                            st.markdown(r)

    with h4:
        if st.button("🔄 Load Disk I/O", type="primary", key="hm_io_btn"):
            with st.spinner(): st.session_state["hm_io"] = hm.get_disk_io()
        if "hm_io" in st.session_state:
            df = st.session_state["hm_io"]
            if "Error" in df.columns: st.error(df["Error"].iloc[0])
            else:
                c1,c2,c3 = st.columns(3, gap="medium")
                if "Total Stall (ms)" in df.columns:
                    with c1: metric_card("Total I/O Stall (ms)", f"{df['Total Stall (ms)'].sum():,}", color="#cf222e")
                if "Avg Read (ms)" in df.columns:
                    with c2: metric_card("Max Avg Read (ms)", f"{df['Avg Read (ms)'].max():,.1f}", color="#9a6700")
                if "Avg Write (ms)" in df.columns:
                    with c3: metric_card("Max Avg Write (ms)", f"{df['Avg Write (ms)'].max():,.1f}", color="#9a6700")
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                st.dataframe(df, use_container_width=True, height=300, hide_index=True)

    with h5:
        if st.button("🔄 Load Memory", type="primary", key="hm_mem_btn"):
            with st.spinner(): st.session_state["hm_mem"] = hm.get_memory_usage()
        if "hm_mem" in st.session_state:
            df = st.session_state["hm_mem"]
            if "Error" in df.columns: st.error(df["Error"].iloc[0])
            else:
                if "Memory (MB)" in df.columns:
                    metric_card("Total SQL Server Memory", f"{df['Memory (MB)'].sum():,.0f} MB")
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                st.dataframe(df, use_container_width=True, height=260, hide_index=True)
                if "Memory (MB)" in df.columns:
                    try:
                        fig = px.pie(df.head(8), names="Clerk", values="Memory (MB)",
                                     title="Memory Distribution by Clerk", template="plotly_white")
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception: pass

    with h6:
        if st.button("🔄 Load Top Queries", type="primary", key="hm_qry_btn"):
            with st.spinner(): st.session_state["hm_qry"] = hm.get_top_queries()
        if "hm_qry" in st.session_state:
            df = st.session_state["hm_qry"]
            if "Error" in df.columns: st.error(df["Error"].iloc[0])
            else:
                st.dataframe(df, use_container_width=True, height=300, hide_index=True)
                if len(df) > 0:
                    sel_hm = st.selectbox("Select query for AI optimization:", range(len(df)),
                        format_func=lambda i: f"#{i+1} CPU:{df['Avg CPU (ms)'].iloc[i]}ms | {df['Query'].iloc[i][:80]}",
                        key="hm_qsel")
                    if st.button("🤖 Optimize This Query", type="primary", key="hm_qopt"):
                        ag = _agent()
                        if ag:
                            with st.spinner():
                                r = ag.chat([{"role":"user","content":
                                    f"Analyze and optimize this SQL Server query.\n"
                                    f"Execution stats: {df['Executions'].iloc[sel_hm]} executions, "
                                    f"avg {df['Avg CPU (ms)'].iloc[sel_hm]}ms CPU, "
                                    f"{df['Avg Reads'].iloc[sel_hm]} avg reads.\n"
                                    f"```sql\n{df['Query'].iloc[sel_hm]}\n```\n"
                                    f"Provide: 🔴 Issues | ✅ Optimized SQL | 📊 Missing Indexes | 💡 Execution Plan Tips"}])
                                st.markdown(r)

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: QUERY OPTIMIZER
# ═════════════════════════════════════════════════════════════════════════════
elif page == "query_optimizer":
    page_header("Query Optimizer",
                "Execution analysis · Blocking · Fragmentation · AI-powered rewrites",
                "connected" if active_c else "disconnected")
    c_qo = _conn()
    if not c_qo: st.warning("⚠️ Connect to a database in **Database Manager** first."); st.stop()

    from modules.query_optimizer import QueryOptimizer
    qo = QueryOptimizer(c_qo)
    q1,q2,q3,q4,q5,q6 = st.tabs(
        ["🔥 Top CPU","💽 Top I/O","🔒 Blocking Chains","⏱️ Long Running","⏳ Waits","🗂️ Fragmentation"])

    def _qo_ai_optimize(query_text, stats_str=""):
        ag = _agent()
        if ag:
            with st.spinner("AI analyzing…"):
                r = ag.chat([{"role":"user","content":
                    f"Optimize this SQL Server query.\n{stats_str}\n"
                    f"```sql\n{query_text}\n```\n"
                    f"Provide: 🔴 Issues | ✅ Optimized SQL | 📊 Suggested Indexes | 💡 Execution Plan Tips"}])
                st.markdown(r)
        else: st.error("Configure Azure OpenAI in Database Manager first.")

    with q1:
        if st.button("🔄 Load Top CPU Queries", type="primary"):
            with st.spinner(): st.session_state["qo_cpu"] = qo.get_top_cpu()
        if "qo_cpu" in st.session_state:
            df = st.session_state["qo_cpu"]
            if "Error" in df.columns: st.error(df["Error"].iloc[0])
            else:
                c1,c2,c3 = st.columns(3, gap="medium")
                if "Total CPU (ms)" in df.columns:
                    with c1: metric_card("Total CPU (ms)", f"{df['Total CPU (ms)'].sum():,}", color="#cf222e")
                if "Avg CPU (ms)" in df.columns:
                    with c2: metric_card("Max Avg CPU (ms)", f"{df['Avg CPU (ms)'].max():,}", color="#9a6700")
                if "Executions" in df.columns:
                    with c3: metric_card("Total Executions", f"{df['Executions'].sum():,}")
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                st.dataframe(df, use_container_width=True, height=280, hide_index=True)
                if "Avg CPU (ms)" in df.columns:
                    try:
                        fig = px.bar(df.head(10), x=df.head(10).index, y="Avg CPU (ms)",
                                     title="Top Queries by Avg CPU Time",
                                     template="plotly_white", color="Avg CPU (ms)",
                                     color_continuous_scale="Reds")
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception: pass
                if len(df) > 0:
                    sel_cpu = st.selectbox("Select query to optimize:", range(len(df)),
                        format_func=lambda i: f"#{i+1} Avg CPU:{df['Avg CPU (ms)'].iloc[i]}ms | {df['Query'].iloc[i][:70]}",
                        key="qo_cpu_sel")
                    if st.button("🤖 AI Optimize", type="primary", key="qo_cpu_opt"):
                        _qo_ai_optimize(df["Query"].iloc[sel_cpu],
                            f"Stats: {df['Executions'].iloc[sel_cpu]} execs, "
                            f"avg {df['Avg CPU (ms)'].iloc[sel_cpu]}ms CPU")

    with q2:
        if st.button("🔄 Load Top I/O Queries", type="primary", key="qo_io_btn"):
            with st.spinner(): st.session_state["qo_io"] = qo.get_top_io()
        if "qo_io" in st.session_state:
            df = st.session_state["qo_io"]
            if "Error" in df.columns: st.error(df["Error"].iloc[0])
            else:
                st.dataframe(df, use_container_width=True, height=300, hide_index=True)
                if len(df) > 0:
                    sel_io = st.selectbox("Select query to optimize:", range(len(df)),
                        format_func=lambda i: f"#{i+1} Reads:{df['Avg Logical Reads'].iloc[i]:,} | {df['Query'].iloc[i][:70]}",
                        key="qo_io_sel")
                    if st.button("🤖 AI Optimize", type="primary", key="qo_io_opt"):
                        _qo_ai_optimize(df["Query"].iloc[sel_io],
                            f"Stats: {df['Executions'].iloc[sel_io]} execs, "
                            f"{df['Avg Logical Reads'].iloc[sel_io]:,} avg reads")

    with q3:
        if st.button("🔄 Check Blocking Chains", type="primary", key="qo_blk_btn"):
            with st.spinner(): st.session_state["qo_blk"] = qo.get_blocking()
        if "qo_blk" in st.session_state:
            df = st.session_state["qo_blk"]
            if "Error" in df.columns: st.error(df["Error"].iloc[0])
            elif df.empty: st.success("✅ No blocking detected.")
            else:
                metric_card("Blocking Sessions", len(df), color="#cf222e")
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                st.dataframe(df, use_container_width=True, hide_index=True)
                if st.button("🤖 Analyze & Resolve Blocking", use_container_width=True, key="qo_blk_ai"):
                    ag = _agent()
                    if ag:
                        with st.spinner():
                            r = ag.chat([{"role":"user","content":
                                f"Analyze this SQL Server blocking chain and provide resolution steps:\n{df.to_string()}"}])
                            st.markdown(r)

    with q4:
        thr_lr = st.slider("Minimum elapsed time (seconds):", 1, 300, 5, key="qo_thr")
        if st.button("🔄 Find Long Running", type="primary", key="qo_lr_btn"):
            with st.spinner(): st.session_state["qo_lr"] = qo.get_long_running(thr_lr)
        if "qo_lr" in st.session_state:
            df = st.session_state["qo_lr"]
            if "Error" in df.columns: st.error(df["Error"].iloc[0])
            elif df.empty: st.success(f"✅ No queries running longer than {thr_lr}s.")
            else:
                metric_card("Long Running Queries", len(df), color="#cf222e")
                st.dataframe(df, use_container_width=True, hide_index=True)

    with q5:
        if st.button("🔄 Load Wait Statistics", type="primary", key="qo_ws_btn"):
            with st.spinner(): st.session_state["qo_ws"] = qo.get_wait_stats()
        if "qo_ws" in st.session_state:
            df = st.session_state["qo_ws"]
            if "Error" in df.columns: st.error(df["Error"].iloc[0])
            else:
                st.dataframe(df, use_container_width=True, height=280, hide_index=True)
                if "Wait Type" in df.columns and "Total Wait (ms)" in df.columns:
                    try:
                        fig = px.pie(df, names="Wait Type", values="Total Wait (ms)",
                                     color="Category", title="Wait Time Distribution",
                                     template="plotly_white")
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception: pass

    with q6:
        st.info("⚠️ Fragmentation scan uses SAMPLED mode — may take 30–90s on large databases.")
        if st.button("🔄 Analyze Fragmentation", type="primary", key="qo_frag_btn"):
            with st.spinner("Scanning index physical stats…"):
                st.session_state["qo_frag"] = qo.get_fragmentation()
        if "qo_frag" in st.session_state:
            df = st.session_state["qo_frag"]
            if "Error" in df.columns: st.error(df["Error"].iloc[0])
            elif df.empty: st.success("✅ No heavily fragmented indexes found.")
            else:
                rebuild = df[df["Action"] == "🔴 Rebuild"]  if "Action" in df.columns else pd.DataFrame()
                reorg   = df[df["Action"] == "🟡 Reorganize"] if "Action" in df.columns else pd.DataFrame()
                c1,c2,c3 = st.columns(3, gap="medium")
                with c1: metric_card("Need Rebuild",    len(rebuild), color="#cf222e")
                with c2: metric_card("Need Reorganize", len(reorg),   color="#9a6700")
                with c3: metric_card("Total Scanned",   len(df))
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                st.dataframe(df, use_container_width=True, height=350, hide_index=True)
                if st.button("🤖 Generate Maintenance Script", use_container_width=True, key="qo_maint"):
                    ag = _agent()
                    if ag:
                        with st.spinner():
                            top_txt = df[["Schema","Table","Index","Frag %","Action"]].head(15).to_string() \
                                      if "Frag %" in df.columns else df.head(15).to_string()
                            r = ag.chat([{"role":"user","content":
                                f"Generate a T-SQL index maintenance script.\n"
                                f"Use ALTER INDEX REBUILD for >30% fragmentation, REORGANIZE for 10-30%.\n"
                                f"Include WITH (ONLINE=ON) and sorting by fragmentation.\n\n{top_txt}"}])
                            st.markdown(r)

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: DATA QUALITY & GOVERNANCE
# ═════════════════════════════════════════════════════════════════════════════
elif page == "data_quality":
    page_header("Data Quality & Governance",
                "Referential integrity · Column analysis · Constraints · AI compliance report",
                "connected" if active_c else "disconnected")
    c_dq = _conn()
    if not c_dq: st.warning("⚠️ Connect to a database in **Database Manager** first."); st.stop()

    from modules.data_quality import DataQualityAnalyzer
    dqa = DataQualityAnalyzer(c_dq)
    dq1,dq2,dq3,dq4,dq5 = st.tabs(
        ["📊 Data Overview","🔗 Referential Integrity","🔍 Column Analysis","⚠️ Disabled Constraints","🤖 AI Governance Report"])

    with dq1:
        if st.button("🔄 Load Data Overview", type="primary"):
            with st.spinner(): st.session_state["dq_ov"] = dqa.get_data_overview()
        if "dq_ov" in st.session_state:
            df = st.session_state["dq_ov"]
            if "Error" in df.columns: st.error(df["Error"].iloc[0])
            else:
                c1,c2,c3,c4 = st.columns(4, gap="medium")
                with c1: metric_card("Tables", len(df))
                if "Rows" in df.columns:
                    with c2: metric_card("Total Rows", f"{df['Rows'].sum():,}")
                if "Nullable Cols" in df.columns:
                    with c3: metric_card("Nullable Columns", f"{df['Nullable Cols'].sum():,}", color="#9a6700")
                if "FKs Out" in df.columns:
                    with c4: metric_card("FK Constraints", f"{df['FKs Out'].sum():,}", color="#1f6feb")
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                st.dataframe(df, use_container_width=True, height=350, hide_index=True)
                if "Rows" in df.columns:
                    try:
                        fig = px.bar(df.head(15).sort_values("Rows", ascending=False),
                                     x="Table", y="Rows", color="Schema",
                                     title="Top 15 Tables by Row Count",
                                     template="plotly_white")
                        fig.update_xaxes(tickangle=45)
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception: pass

    with dq2:
        if st.button("🔄 Check Referential Integrity", type="primary", key="dq_ri_btn"):
            with st.spinner(): st.session_state["dq_ri"] = dqa.get_referential_integrity()
        if "dq_ri" in st.session_state:
            df = st.session_state["dq_ri"]
            if "Error" in df.columns: st.error(df["Error"].iloc[0])
            elif df.empty: st.info("No foreign key constraints found.")
            else:
                disabled_ri = df[df["Enabled"].str.contains("DISABLED", na=False)]  if "Enabled" in df.columns else pd.DataFrame()
                untrusted   = df[df["Trusted"].str.contains("NOT TRUSTED", na=False)] if "Trusted" in df.columns else pd.DataFrame()
                c1,c2,c3 = st.columns(3, gap="medium")
                with c1: metric_card("Total FK Constraints", len(df))
                with c2: metric_card("Disabled FKs",  len(disabled_ri),  color="#cf222e")
                with c3: metric_card("Untrusted FKs", len(untrusted), color="#9a6700")
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                st.dataframe(df, use_container_width=True, height=350, hide_index=True)
                if not disabled_ri.empty or not untrusted.empty:
                    st.warning(f"⚠️ {len(disabled_ri)} disabled and {len(untrusted)} untrusted constraints detected.")
                    if st.button("🤖 Explain & Fix Integrity Issues", use_container_width=True, key="dq_ri_ai"):
                        ag = _agent()
                        if ag:
                            with st.spinner():
                                parts = []
                                if not disabled_ri.empty: parts.append(f"Disabled FKs:\n{disabled_ri.to_string()}")
                                if not untrusted.empty:   parts.append(f"Untrusted FKs:\n{untrusted.to_string()}")
                                r = ag.chat([{"role":"user","content":
                                    "Analyze these SQL Server referential integrity issues. "
                                    "Explain risks and provide T-SQL to re-enable constraints and rebuild trust:\n\n"
                                    + "\n\n".join(parts)}])
                                st.markdown(r)

    with dq3:
        tbl_dq = dqa.get_tables_list()
        if "Error" in tbl_dq.columns:
            st.error(tbl_dq["Error"].iloc[0])
        else:
            opts_dq = [f"{r['Schema']}.{r['Table']}" for _,r in tbl_dq.iterrows()]
            sel_dq = st.selectbox("Select table to analyze:", [""]+opts_dq, key="dq_col_sel")
            if sel_dq and st.button("🔍 Analyze Columns", type="primary", key="dq_col_btn"):
                sch_dq, tbl_dq2 = sel_dq.split(".",1)
                with st.spinner(): st.session_state["dq_col"] = dqa.get_column_stats(sch_dq, tbl_dq2)
                st.session_state["dq_col_name"] = sel_dq
            if "dq_col" in st.session_state:
                df = st.session_state["dq_col"]
                nm = st.session_state.get("dq_col_name", "")
                st.markdown(f"#### Column Profile: `{nm}`")
                if "Error" in df.columns: st.error(df["Error"].iloc[0])
                else:
                    c1,c2,c3,c4 = st.columns(4, gap="medium")
                    with c1: metric_card("Total Columns", len(df))
                    if "Nullable" in df.columns:
                        null_n = int(df["Nullable"].apply(lambda x: 1 if x else 0).sum())
                        with c2: metric_card("Nullable", null_n, color="#9a6700")
                    if "PK" in df.columns:
                        with c3: metric_card("PK Columns", int(df["PK"].apply(lambda x: 1 if x=="✅" else 0).sum()))
                    if "FK" in df.columns:
                        with c4: metric_card("FK Columns", int(df["FK"].apply(lambda x: 1 if x=="✅" else 0).sum()), color="#1f6feb")
                    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    if st.button("🤖 AI Data Dictionary", type="primary", key="dq_dict_btn"):
                        ag = _agent()
                        if ag:
                            with st.spinner():
                                r = ag.chat([{"role":"user","content":
                                    f"Generate a professional data dictionary for SQL Server table `{nm}`.\n"
                                    f"For each column provide: business meaning, valid values/range, "
                                    f"data quality rules, and constraints.\n\nColumn info:\n{df.to_string()}"}])
                                st.markdown(r)

    with dq4:
        if st.button("🔄 Find Disabled Constraints", type="primary", key="dq_dc_btn"):
            with st.spinner(): st.session_state["dq_dc"] = dqa.get_disabled_constraints()
        if "dq_dc" in st.session_state:
            df = st.session_state["dq_dc"]
            if "Error" in df.columns: st.error(df["Error"].iloc[0])
            elif df.empty: st.success("✅ No disabled constraints — database integrity is intact.")
            else:
                metric_card("Disabled Constraints", len(df), color="#cf222e")
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.warning("⚠️ Disabled constraints can allow dirty data. Review before re-enabling.")
                if st.button("🤖 Generate Re-enable Script", use_container_width=True, key="dq_dc_ai"):
                    ag = _agent()
                    if ag:
                        with st.spinner():
                            r = ag.chat([{"role":"user","content":
                                f"Generate a T-SQL script to safely re-enable these disabled SQL Server constraints.\n"
                                f"Include WITH CHECK NOCHECK appropriately, add safety comments:\n\n{df.to_string()}"}])
                            st.markdown(r)

    with dq5:
        st.markdown("Generates a comprehensive data governance and compliance assessment using AI.")
        if st.button("🤖 Generate Governance Report", type="primary", use_container_width=True, key="dq_gov_btn"):
            ag = _agent()
            if ag:
                _load_schema()
                with st.spinner("AI generating governance report…"):
                    ov  = st.session_state.get("dq_ov", pd.DataFrame())
                    ri  = st.session_state.get("dq_ri", pd.DataFrame())
                    dc  = st.session_state.get("dq_dc", pd.DataFrame())
                    ctx = []
                    if not ov.empty and "Error" not in ov.columns and "Rows" in ov.columns:
                        ctx.append(f"Tables: {len(ov)}, Total Rows: {ov['Rows'].sum():,}")
                    if not ri.empty and "Error" not in ri.columns and "Enabled" in ri.columns:
                        dis_ri = ri[ri["Enabled"].str.contains("DISABLED", na=False)]
                        ctx.append(f"FK Constraints: {len(ri)}, Disabled: {len(dis_ri)}")
                    if not dc.empty and "Error" not in dc.columns:
                        ctx.append(f"Disabled Constraints: {len(dc)}")
                    r = ag.chat([{"role":"user","content":
                        "Generate a SQL Server data governance and compliance report.\n\n"
                        "Context:\n" + "\n".join(ctx) + "\n\n"
                        "Schema:\n" + (st.session_state.get("schema_cache","") or "") + "\n\n"
                        "Sections:\n"
                        "## 1. Data Governance Scorecard\n"
                        "## 2. Referential Integrity Assessment\n"
                        "## 3. Data Quality Risks\n"
                        "## 4. PII / Sensitive Data Identification\n"
                        "## 5. Compliance Checklist (GDPR, SOX, HIPAA)\n"
                        "## 6. Recommended Governance Policies\n"
                        "## 7. Prioritized Action Plan"}])
                    st.session_state["dq_report"] = r
            else: st.error("Configure Azure OpenAI in Database Manager first.")
        if "dq_report" in st.session_state:
            st.markdown(st.session_state["dq_report"])
            st.download_button("⬇️ Download Report",
                               st.session_state["dq_report"].encode(),
                               "governance_report.md", "text/markdown")

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: DATA EDITOR  (AI-powered DML with approval workflow)
# ═════════════════════════════════════════════════════════════════════════════
elif page == "data_editor":
    page_header("Data Editor",
                "Browse · Inline edit · AI-generated DML with approval workflow",
                "connected" if active_c else "disconnected")
    c_de = _conn()
    if not c_de: st.warning("⚠️ Connect to a database in **Database Manager** first."); st.stop()

    if role not in ("Admin", "DBA", "Developer"):
        st.warning("🔒 Developer role or higher required to edit data.")
        st.stop()

    from modules.data_quality import DataQualityAnalyzer
    dqa_de = DataQualityAnalyzer(c_de)
    tbl_list = dqa_de.get_tables_list()
    de1, de2, de3 = st.tabs(["📋 Browse & Edit", "🤖 AI DML Assistant", "📜 Audit Log"])

    with de1:
        if "Error" in tbl_list.columns:
            st.error(tbl_list["Error"].iloc[0])
        else:
            opts_de = [f"{r['Schema']}.{r['Table']}" for _,r in tbl_list.iterrows()]
            col_l, col_r = st.columns([3,1])
            sel_de = col_l.selectbox("Select table:", [""]+opts_de, key="de_tbl")
            row_lim = col_r.number_input("Max rows:", min_value=10, max_value=5000, value=100, step=10)

            if sel_de and st.button("📋 Load Data", type="primary"):
                sch_de, tbl_de = sel_de.split(".",1)
                with st.spinner(f"Loading {sel_de}…"):
                    try:
                        df_raw = c_de.execute_query(
                            f"SELECT TOP {int(row_lim)} * FROM [{sch_de}].[{tbl_de}]")
                        st.session_state["de_df"]       = df_raw.copy()
                        st.session_state["de_orig"]     = df_raw.copy()
                        st.session_state["de_tbl_name"] = sel_de
                    except Exception as ex:
                        st.error(str(ex))

            if "de_df" in st.session_state:
                tbl_nm = st.session_state.get("de_tbl_name","")
                df_orig = st.session_state["de_orig"]
                st.markdown(f"#### `{tbl_nm}` — {len(df_orig):,} rows loaded")
                st.info("✏️ Edit cells directly in the table below. Click **Save Changes** to generate UPDATE statements for approval.")

                edited_df = st.data_editor(
                    df_orig, use_container_width=True, hide_index=False,
                    num_rows="dynamic", key="de_editor")

                b1, b2, b3 = st.columns([2,2,3])
                if b1.button("💾 Save Changes", type="primary", use_container_width=True):
                    if edited_df is not None:
                        st.session_state["de_edited"] = edited_df.copy()
                        st.session_state["de_dml_pending"] = None
                        # Detect changed rows
                        try:
                            changed = edited_df.compare(df_orig, keep_equal=False)
                            if changed.empty:
                                st.info("No changes detected.")
                            else:
                                st.session_state["de_changes"] = changed
                                st.success(f"✅ {len(changed)} row(s) changed — review and approve below.")
                        except Exception:
                            st.session_state["de_changes"] = None
                            st.warning("Changes detected — review the UPDATE statements below.")

                if b2.button("🔄 Refresh", use_container_width=True):
                    for k in ["de_df","de_orig","de_edited","de_changes","de_dml_pending"]:
                        st.session_state.pop(k, None)
                    st.rerun()

                # Show generated UPDATE SQL for approval
                if "de_changes" in st.session_state or "de_edited" in st.session_state:
                    st.markdown("#### ✍️ Review Generated UPDATE Statements")
                    edited = st.session_state.get("de_edited", edited_df)
                    sch_de2, tbl_de2 = tbl_nm.split(".",1)
                    pk_col = df_orig.columns[0]  # assume first column is PK

                    update_stmts = []
                    try:
                        for idx in range(len(edited)):
                            row_new = edited.iloc[idx]
                            row_old = df_orig.iloc[idx]
                            if not row_new.equals(row_old):
                                sets = ", ".join(
                                    f"[{c}] = '{row_new[c]}'"
                                    for c in edited.columns
                                    if c != pk_col and row_new[c] != row_old[c]
                                )
                                if sets:
                                    pk_val = row_old[pk_col]
                                    stmt = (f"UPDATE [{sch_de2}].[{tbl_de2}]\n"
                                            f"SET {sets}\n"
                                            f"WHERE [{pk_col}] = '{pk_val}';")
                                    update_stmts.append(stmt)
                    except Exception as ex:
                        st.warning(f"Could not auto-generate UPDATE SQL: {ex}")

                    if update_stmts:
                        for stmt in update_stmts:
                            st.code(stmt, language="sql")
                        st.markdown("""
                        <div style='background:#fff8c5;border:1px solid #f0e17a;
                        border-radius:8px;padding:16px;margin:12px 0'>
                            <b style='color:#9a6700'>⚠️ Approval Required</b><br>
                            <span style='font-size:13px;color:#6e7681'>
                            Review the UPDATE statements above carefully before approving.
                            These changes will be written to the live database.</span>
                        </div>
                        """, unsafe_allow_html=True)
                        confirm = st.checkbox("I have reviewed the changes and approve execution", key="de_confirm")
                        if confirm and st.button("✅ Execute Changes", type="primary"):
                            results = []
                            for stmt in update_stmts:
                                res = c_de.execute_dml(stmt)
                                results.append(res)
                                if "audit_log" not in st.session_state:
                                    st.session_state["audit_log"] = []
                                st.session_state["audit_log"].append({
                                    "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "User": user["name"], "Table": tbl_nm,
                                    "SQL": stmt[:100]+"…", "Result": res})
                            for r in results:
                                (st.success if "✅" in r else st.error)(r)
                            # Reload
                            for k in ["de_df","de_orig","de_edited","de_changes"]:
                                st.session_state.pop(k, None)
                    else:
                        st.info("No row differences detected between original and edited data.")

    with de2:
        st.markdown("#### 🤖 AI-Generated DML")
        st.markdown("Describe what you want to change in natural language — AI generates the safe DML SQL for your approval.")
        if "Error" not in tbl_list.columns:
            opts_de2 = [f"{r['Schema']}.{r['Table']}" for _,r in tbl_list.iterrows()]
            sel_de2 = st.selectbox("Target table:", [""]+opts_de2, key="de2_tbl")
        nl_dml = st.text_area("Describe the change:",
            placeholder="e.g. Update status to 'Inactive' for all customers whose last_order_date is before 2023-01-01",
            height=80, key="de2_nl")

        if st.button("🤖 Generate DML SQL", type="primary") and nl_dml.strip():
            ag = _agent()
            if not ag:
                st.error("Configure Azure OpenAI in Database Manager first.")
            elif not sel_de2:
                st.error("Select a target table first.")
            else:
                _load_schema()
                with st.spinner("AI generating DML…"):
                    schema_ctx = st.session_state.get("schema_cache","")
                    r = ag.chat([{"role":"user","content":
                        f"Generate a safe, precise T-SQL DML statement for this request.\n"
                        f"Target table: {sel_de2}\n"
                        f"Request: {nl_dml}\n\n"
                        f"Schema context:\n{schema_ctx}\n\n"
                        f"Rules:\n"
                        f"- Use WHERE clauses to minimize affected rows\n"
                        f"- Add a comment explaining what this does\n"
                        f"- Show estimated rows affected\n"
                        f"- Provide a SELECT to verify before running\n"
                        f"- Format: return ONLY the DML SQL block (UPDATE/INSERT/DELETE)\n"
                        f"- NO DROP, TRUNCATE, ALTER, or DDL\n\n"
                        f"Return the SQL in a ```sql code block, followed by a verification SELECT."}])
                    st.session_state["de2_generated"] = r

        if "de2_generated" in st.session_state:
            st.markdown(st.session_state["de2_generated"])
            # Extract SQL block
            raw = st.session_state["de2_generated"]
            sql_match = re.search(r"```sql\s*(.*?)```", raw, re.DOTALL | re.IGNORECASE)
            extracted = sql_match.group(1).strip() if sql_match else ""
            # Show only the DML (first statement)
            dml_lines = [ln for ln in extracted.split("\n")
                         if ln.strip().upper().startswith(("UPDATE","INSERT","DELETE"))]
            dml_sql = "\n".join(dml_lines) if dml_lines else extracted

            if dml_sql:
                st.markdown("#### ✍️ Editable DML — Review Before Approving")
                dml_editable = st.text_area("Edit if needed:", value=dml_sql, height=120, key="de2_dml_edit")
                st.markdown("""
                <div style='background:#fff8c5;border:1px solid #f0e17a;
                border-radius:8px;padding:14px;margin:12px 0'>
                    <b style='color:#9a6700'>⚠️ Approval Required</b><br>
                    <span style='font-size:13px;color:#6e7681'>
                    AI-generated DML — verify correctness before executing on live data.</span>
                </div>
                """, unsafe_allow_html=True)
                confirm2 = st.checkbox("I have reviewed the SQL and approve execution", key="de2_confirm")
                if confirm2 and st.button("✅ Execute DML", type="primary", key="de2_exec"):
                    res_dml = c_de.execute_dml(dml_editable)
                    (st.success if "✅" in res_dml else st.error)(res_dml)
                    if "audit_log" not in st.session_state:
                        st.session_state["audit_log"] = []
                    st.session_state["audit_log"].append({
                        "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "User": user["name"], "Table": sel_de2,
                        "SQL": dml_editable[:120]+"…", "Result": res_dml})
                    del st.session_state["de2_generated"]

    with de3:
        st.markdown("#### 📜 DML Audit Log (Session)")
        audit = st.session_state.get("audit_log", [])
        if not audit:
            st.info("No DML operations executed in this session yet.")
        else:
            audit_df = pd.DataFrame(audit)
            st.dataframe(audit_df, use_container_width=True, hide_index=True)
            if _can("export_csv"):
                st.download_button("⬇️ Export Audit Log",
                                   audit_df.to_csv(index=False).encode(),
                                   "audit_log.csv", "text/csv")
            if st.button("🗑️ Clear Audit Log", key="de3_clear"):
                st.session_state["audit_log"] = []
                st.rerun()

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: SECURITY CENTER
# ═════════════════════════════════════════════════════════════════════════════
elif page == "security_center":
    page_header("Security Center",
                "Logins · DB Users · Roles · Permissions · Risk Audit",
                "connected" if active_c else "disconnected")
    c_sc = _conn()
    if not c_sc: st.warning("⚠️ Connect to a database in **Database Manager** first."); st.stop()
    if role not in ("Admin","DBA"):
        st.warning("🔒 DBA or Admin role required."); st.stop()

    from modules.security_center import SecurityCenter
    sc = SecurityCenter(c_sc)
    s1,s2,s3,s4,s5,s6 = st.tabs([
        "🔑 Server Logins","👤 DB Users","👥 Server Roles",
        "🗂️ DB Role Members","🔒 Permissions","⚠️ Risk Audit"
    ])

    with s1:
        if st.button("🔄 Load Server Logins", type="primary", key="sc_logins_btn"):
            with st.spinner(): st.session_state["sc_logins"] = sc.get_server_logins()
        if "sc_logins" in st.session_state:
            df = st.session_state["sc_logins"]
            if "Error" in df.columns: st.error(df["Error"].iloc[0])
            else:
                enabled  = df[df["Status"]=="Enabled"]  if "Status" in df.columns else df
                disabled = df[df["Status"]=="Disabled"] if "Status" in df.columns else pd.DataFrame()
                c1,c2,c3 = st.columns(3, gap="medium")
                with c1: metric_card("Total Logins", len(df))
                with c2: metric_card("Enabled", len(enabled))
                with c3: metric_card("Disabled", len(disabled), color="#dc2626")
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                st.dataframe(df, use_container_width=True, height=380, hide_index=True)
                if st.button("🤖 AI Security Assessment", use_container_width=True, key="sc_logins_ai"):
                    ag = _agent()
                    if ag:
                        with st.spinner():
                            r = ag.chat([{"role":"user","content":
                                f"Analyze these SQL Server logins for security risks:\n\n{df.to_string()}\n\n"
                                "Identify: excessive privileges, weak policy settings, dormant accounts. "
                                "Provide specific remediation T-SQL and hardening recommendations."}])
                            st.markdown(r)

    with s2:
        if st.button("🔄 Load Database Users", type="primary", key="sc_users_btn"):
            with st.spinner(): st.session_state["sc_users"] = sc.get_database_users()
        if "sc_users" in st.session_state:
            df = st.session_state["sc_users"]
            if "Error" in df.columns: st.error(df["Error"].iloc[0])
            else:
                orphan = df[df["Mapped Login"]=="(no login)"] if "Mapped Login" in df.columns else pd.DataFrame()
                c1,c2 = st.columns(2, gap="medium")
                with c1: metric_card("Database Users", len(df))
                with c2: metric_card("Orphan Users", len(orphan), color="#dc2626")
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                st.dataframe(df, use_container_width=True, height=380, hide_index=True)
                if not orphan.empty:
                    st.warning(f"⚠️ {len(orphan)} orphan user(s) — users without a valid server login.")
                    if st.button("🤖 Generate Fix Script", use_container_width=True, key="sc_orphan_ai"):
                        ag = _agent()
                        if ag:
                            with st.spinner():
                                r = ag.chat([{"role":"user","content":
                                    f"Generate T-SQL to fix SQL Server orphan database users using "
                                    f"sp_change_users_login or DROP USER:\n\n{orphan.to_string()}"}])
                                st.markdown(r)

    with s3:
        if st.button("🔄 Load Server Roles", type="primary", key="sc_sroles_btn"):
            with st.spinner(): st.session_state["sc_sroles"] = sc.get_server_role_members()
        if "sc_sroles" in st.session_state:
            df = st.session_state["sc_sroles"]
            if "Error" in df.columns: st.error(df["Error"].iloc[0])
            else:
                metric_card("Server Role Assignments", len(df))
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                st.dataframe(df, use_container_width=True, height=400, hide_index=True)

    with s4:
        if st.button("🔄 Load DB Role Members", type="primary", key="sc_dbroles_btn"):
            with st.spinner(): st.session_state["sc_dbroles"] = sc.get_database_role_members()
        if "sc_dbroles" in st.session_state:
            df = st.session_state["sc_dbroles"]
            if "Error" in df.columns: st.error(df["Error"].iloc[0])
            else:
                metric_card("DB Role Assignments", len(df))
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                st.dataframe(df, use_container_width=True, height=400, hide_index=True)

    with s5:
        if st.button("🔄 Load Object Permissions", type="primary", key="sc_perms_btn"):
            with st.spinner(): st.session_state["sc_perms"] = sc.get_object_permissions()
        if "sc_perms" in st.session_state:
            df = st.session_state["sc_perms"]
            if "Error" in df.columns: st.error(df["Error"].iloc[0])
            else:
                metric_card("Permission Grants", len(df))
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                st.dataframe(df, use_container_width=True, height=400, hide_index=True)

    with s6:
        if st.button("🔄 Run Security Risk Audit", type="primary", use_container_width=True, key="sc_risks_btn"):
            with st.spinner("Scanning for security risks…"): st.session_state["sc_risks"] = sc.get_security_risks()
        if "sc_risks" in st.session_state:
            df = st.session_state["sc_risks"]
            if "Error" in df.columns: st.error(df["Error"].iloc[0])
            elif df.empty: st.success("✅ No security risks detected.")
            else:
                high = df[df["Severity"]=="HIGH"]   if "Severity" in df.columns else pd.DataFrame()
                med  = df[df["Severity"]=="MEDIUM"]  if "Severity" in df.columns else pd.DataFrame()
                low  = df[df["Severity"]=="LOW"]     if "Severity" in df.columns else pd.DataFrame()
                c1,c2,c3,c4 = st.columns(4, gap="medium")
                with c1: metric_card("Total Risks",  len(df))
                with c2: metric_card("High",   len(high),  color="#dc2626")
                with c3: metric_card("Medium", len(med),   color="#d97706")
                with c4: metric_card("Low",    len(low),   color="#2563eb")
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                if not high.empty:
                    st.error(f"🚨 {len(high)} HIGH severity risk(s) — immediate action required!")
                st.dataframe(df, use_container_width=True, height=350, hide_index=True)
                if st.button("🤖 Generate Security Hardening Plan", type="primary",
                             use_container_width=True, key="sc_harden_btn"):
                    ag = _agent()
                    if ag:
                        with st.spinner():
                            r = ag.chat([{"role":"user","content":
                                f"Generate a SQL Server security hardening plan for these risks:\n\n"
                                f"{df.to_string()}\n\nFor each risk: explain threat, provide T-SQL remediation, "
                                f"and prioritize actions by severity."}])
                            st.markdown(r)

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: SQL AGENT JOBS
# ═════════════════════════════════════════════════════════════════════════════
elif page == "agent_jobs":
    page_header("SQL Agent Jobs",
                "Monitor SQL Server Agent jobs, history, and scheduling",
                "connected" if active_c else "disconnected")
    c_aj = _conn()
    if not c_aj: st.warning("⚠️ Connect to a database in **Database Manager** first."); st.stop()

    from modules.server_monitor import ServerMonitor
    sm_aj = ServerMonitor(c_aj)
    j1,j2,j3 = st.tabs(["📋 All Jobs","📜 Job History","🤖 AI Analysis"])

    with j1:
        if st.button("🔄 Load Jobs", type="primary", key="aj_jobs_btn"):
            with st.spinner(): st.session_state["aj_jobs"] = sm_aj.get_agent_jobs()
        if "aj_jobs" in st.session_state:
            df = st.session_state["aj_jobs"]
            if "Error" in df.columns: st.error(df["Error"].iloc[0])
            elif df.empty: st.info("No SQL Agent jobs found. SQL Server Agent may not be running.")
            else:
                enabled = df[df["Status"]=="Enabled"]       if "Status"       in df.columns else df
                failed  = df[df["Last Outcome"]=="Failed"]  if "Last Outcome" in df.columns else pd.DataFrame()
                c1,c2,c3,c4 = st.columns(4, gap="medium")
                with c1: metric_card("Total Jobs",     len(df))
                with c2: metric_card("Enabled",         len(enabled))
                with c3: metric_card("Failed Last Run", len(failed),         color="#dc2626")
                with c4: metric_card("Disabled",        len(df)-len(enabled), color="#d97706")
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                if not failed.empty:
                    st.error(f"🚨 {len(failed)} job(s) failed on last run — immediate review required!")
                st.dataframe(df, use_container_width=True, height=430, hide_index=True)

    with j2:
        lim = st.slider("History records:", 20, 200, 50, 10, key="aj_hist_lim")
        if st.button("🔄 Load Job History", type="primary", key="aj_hist_btn"):
            with st.spinner(): st.session_state["aj_hist"] = sm_aj.get_job_history(lim)
        if "aj_hist" in st.session_state:
            df = st.session_state["aj_hist"]
            if "Error" in df.columns: st.error(df["Error"].iloc[0])
            else: st.dataframe(df, use_container_width=True, height=450, hide_index=True)

    with j3:
        st.markdown("Get AI analysis of job health, failure patterns, and scheduling optimizations.")
        if st.button("🤖 Analyze Job Health", type="primary", use_container_width=True, key="aj_ai_btn"):
            ag = _agent()
            if ag:
                jobs = st.session_state.get("aj_jobs", pd.DataFrame())
                hist = st.session_state.get("aj_hist", pd.DataFrame())
                if jobs.empty: st.warning("Load job data first (All Jobs tab).")
                else:
                    with st.spinner():
                        ctx = f"SQL Agent Jobs:\n{jobs.to_string()}"
                        if not hist.empty and "Error" not in hist.columns:
                            ctx += f"\n\nRecent History (last 20):\n{hist.head(20).to_string()}"
                        r = ag.chat([{"role":"user","content":
                            f"Analyze these SQL Server Agent jobs:\n\n{ctx}\n\n"
                            "Identify: frequently failing jobs, long-running jobs, overlapping schedules, "
                            "jobs with no error handling. Provide root-cause analysis and T-SQL fixes."}])
                        st.markdown(r)

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: BACKUP MONITOR
# ═════════════════════════════════════════════════════════════════════════════
elif page == "backup_monitor":
    page_header("Backup Monitor",
                "Database backup status, recovery models, and size analytics",
                "connected" if active_c else "disconnected")
    c_bm = _conn()
    if not c_bm: st.warning("⚠️ Connect to a database in **Database Manager** first."); st.stop()

    from modules.server_monitor import ServerMonitor
    sm_bm = ServerMonitor(c_bm)
    bm1,bm2,bm3 = st.tabs(["💾 Backup Status","📊 Database Sizes","🤖 AI Strategy"])

    with bm1:
        if st.button("🔄 Load Backup Status", type="primary", key="bm_backup_btn"):
            with st.spinner(): st.session_state["bm_backups"] = sm_bm.get_backup_status()
        if "bm_backups" in st.session_state:
            df = st.session_state["bm_backups"]
            if "Error" in df.columns: st.error(df["Error"].iloc[0])
            elif df.empty: st.info("No user databases found.")
            else:
                col_fs = "Full Backup Status"
                never   = df[df[col_fs]=="NEVER BACKED UP"]              if col_fs in df.columns else pd.DataFrame()
                overdue = df[df[col_fs].str.startswith("OVERDUE", na=False)] if col_fs in df.columns else pd.DataFrame()
                recent  = df[df[col_fs]=="Recent"]                       if col_fs in df.columns else pd.DataFrame()
                c1,c2,c3,c4 = st.columns(4, gap="medium")
                with c1: metric_card("Total Databases",  len(df))
                with c2: metric_card("Never Backed Up",  len(never),   color="#dc2626")
                with c3: metric_card("Overdue Backups",  len(overdue), color="#d97706")
                with c4: metric_card("Recent Backups",   len(recent),  color="#10b981")
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                if len(never)   > 0: st.error(f"🚨 {len(never)} database(s) have NEVER been backed up!")
                if len(overdue) > 0: st.warning(f"⚠️ {len(overdue)} database(s) have overdue backups!")
                st.dataframe(df, use_container_width=True, height=400, hide_index=True)

    with bm2:
        if st.button("🔄 Load Database Sizes", type="primary", key="bm_sizes_btn"):
            with st.spinner(): st.session_state["bm_sizes"] = sm_bm.get_database_sizes()
        if "bm_sizes" in st.session_state:
            df = st.session_state["bm_sizes"]
            if "Error" in df.columns: st.error(df["Error"].iloc[0])
            else:
                if "Total MB" in df.columns and not df.empty:
                    total_gb = df["Total MB"].sum() / 1024
                    c1,c2 = st.columns(2, gap="medium")
                    with c1: metric_card("Total Databases", len(df))
                    with c2: metric_card("Total Size", f"{total_gb:.1f} GB")
                    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                    try:
                        fig = px.bar(df.head(20), x="Database", y="Total MB",
                                     color="Recovery", title="Database Sizes (Top 20)",
                                     template="plotly_white",
                                     color_discrete_sequence=px.colors.qualitative.Set2)
                        fig.update_layout(height=300, margin=dict(t=40,b=20))
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception: pass
                st.dataframe(df, use_container_width=True, height=320, hide_index=True)

    with bm3:
        st.markdown("Get AI-powered backup strategy recommendations based on your database profile.")
        if st.button("🤖 Generate Backup Strategy", type="primary", use_container_width=True, key="bm_ai_btn"):
            ag = _agent()
            if ag:
                backup_data = st.session_state.get("bm_backups", pd.DataFrame())
                sizes_data  = st.session_state.get("bm_sizes",   pd.DataFrame())
                ctx = []
                if not backup_data.empty and "Error" not in backup_data.columns:
                    ctx.append(f"Backup Status:\n{backup_data.to_string()}")
                if not sizes_data.empty and "Error" not in sizes_data.columns:
                    ctx.append(f"Database Sizes:\n{sizes_data.to_string()}")
                if not ctx: st.warning("Load backup data first (other tabs).")
                else:
                    with st.spinner():
                        r = ag.chat([{"role":"user","content":
                            "Analyze this SQL Server backup status and design an enterprise backup strategy:\n\n"
                            + "\n\n".join(ctx) +
                            "\n\nInclude: RPO/RTO targets, full/differential/log backup schedule, "
                            "retention policy, T-SQL maintenance jobs, and monitoring alerts."}])
                        st.markdown(r)

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: SERVER CONFIG
# ═════════════════════════════════════════════════════════════════════════════
elif page == "server_config":
    page_header("Server Configuration",
                "Server properties, configuration options, and linked servers",
                "connected" if active_c else "disconnected")
    c_sf = _conn()
    if not c_sf: st.warning("⚠️ Connect to a database in **Database Manager** first."); st.stop()
    if role not in ("Admin","DBA"):
        st.warning("🔒 DBA or Admin role required."); st.stop()

    from modules.server_monitor import ServerMonitor
    sm_sf = ServerMonitor(c_sf)
    sc1,sc2,sc3,sc4 = st.tabs([
        "🖥️ Server Properties","⚙️ Configuration","🔗 Linked Servers","🤖 AI Tuning"
    ])

    with sc1:
        if st.button("🔄 Load Server Properties", type="primary", key="sf_props_btn"):
            with st.spinner(): st.session_state["sf_props"] = sm_sf.get_server_properties()
        if "sf_props" in st.session_state:
            df = st.session_state["sf_props"]
            if "Error" in df.columns: st.error(df["Error"].iloc[0])
            else:
                st.dataframe(df.T.rename(columns={0:"Value"}),
                             use_container_width=True, height=450)

    with sc2:
        if st.button("🔄 Load Configuration", type="primary", key="sf_cfg_btn"):
            with st.spinner(): st.session_state["sf_cfg"] = sm_sf.get_server_config()
        if "sf_cfg" in st.session_state:
            df = st.session_state["sf_cfg"]
            if "Error" in df.columns: st.error(df["Error"].iloc[0])
            else:
                pending = (df[df["Configured Value"] != df["Running Value"]]
                           if "Configured Value" in df.columns else pd.DataFrame())
                c1,c2 = st.columns(2, gap="medium")
                with c1: metric_card("Config Options", len(df))
                with c2: metric_card("Pending Restart", len(pending), color="#d97706")
                if not pending.empty:
                    st.warning(f"⚠️ {len(pending)} setting(s) require a server restart to take effect.")
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                search_sf = st.text_input("🔍 Filter options:", key="sf_search")
                flt = (df[df["Configuration Option"].str.contains(search_sf, case=False, na=False)]
                       if search_sf else df)
                st.dataframe(flt, use_container_width=True, height=380, hide_index=True)

    with sc3:
        if st.button("🔄 Load Linked Servers", type="primary", key="sf_ls_btn"):
            with st.spinner(): st.session_state["sf_ls"] = sm_sf.get_linked_servers()
        if "sf_ls" in st.session_state:
            df = st.session_state["sf_ls"]
            if "Error" in df.columns: st.error(df["Error"].iloc[0])
            elif df.empty: st.info("No linked servers configured.")
            else:
                metric_card("Linked Servers", len(df))
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                st.dataframe(df, use_container_width=True, height=380, hide_index=True)

    with sc4:
        st.markdown("AI analysis of your SQL Server configuration for performance and security tuning.")
        if st.button("🤖 Analyze & Tune Configuration", type="primary",
                     use_container_width=True, key="sf_ai_btn"):
            ag = _agent()
            if ag:
                props = st.session_state.get("sf_props", pd.DataFrame())
                cfg   = st.session_state.get("sf_cfg",   pd.DataFrame())
                ctx = []
                if not props.empty and "Error" not in props.columns:
                    ctx.append(f"Server Properties:\n{props.to_string()}")
                if not cfg.empty and "Error" not in cfg.columns:
                    ctx.append(f"Configuration:\n{cfg.to_string()}")
                if not ctx: st.warning("Load configuration data first (other tabs).")
                else:
                    with st.spinner():
                        r = ag.chat([{"role":"user","content":
                            "Analyze this SQL Server configuration for enterprise best practices:\n\n"
                            + "\n\n".join(ctx) +
                            "\n\nProvide: performance tuning recommendations (max server memory, "
                            "MAXDOP, cost threshold), security hardening settings, under-utilized "
                            "features, and T-SQL sp_configure commands to apply the changes."}])
                        st.markdown(r)

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: ADMIN CONSOLE
# ═════════════════════════════════════════════════════════════════════════════
elif page == "admin":
    page_header("Admin Console", "User accounts, role management, and permissions", "operational")
    if role != "Admin":
        st.error("🔒 Administrator role required."); st.stop()

    a1,a2,a3,a4 = st.tabs(["👥 User Management","➕ Create User","🔑 Change Password","📋 Role Matrix"])

    with a1:
        users_list = RBAC.list_users()
        users_df = pd.DataFrame(users_list)
        c1,c2,c3 = st.columns(3,gap="medium")
        with c1: metric_card("Total Users", len(users_list))
        roles_cnt = users_df["role"].value_counts() if not users_df.empty else pd.Series()
        with c2: metric_card("Roles Assigned", len(roles_cnt))
        with c3: metric_card("Admin Users", int(roles_cnt.get("Admin",0)))
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.dataframe(users_df, use_container_width=True, height=250, hide_index=True)

        sel = st.selectbox("Select user to manage:", [""]+[u["username"] for u in users_list])
        if sel:
            curr_r = next((u["role"] for u in users_list if u["username"]==sel),"")
            roles_l = list(RBAC.ROLES.keys())
            new_r = st.selectbox("Change role to:", roles_l, index=roles_l.index(curr_r) if curr_r in roles_l else 0)
            b1,b2 = st.columns(2)
            if b1.button("💾 Update Role", type="primary", use_container_width=True):
                ok,msg=RBAC.update_user_role(sel,new_r)
                (st.success if ok else st.error)(msg)
            if b2.button("🗑️ Delete User", use_container_width=True):
                ok,msg=RBAC.delete_user(sel)
                (st.success if ok else st.error)(msg)
                if ok: st.rerun()

    with a2:
        with st.form("add_u", clear_on_submit=True):
            c1,c2 = st.columns(2)
            nu = c1.text_input("Username"); nn = c2.text_input("Full Name")
            c3,c4 = st.columns(2)
            nr = c3.selectbox("Role", list(RBAC.ROLES.keys()))
            np = c4.text_input("Password", type="password")
            if st.form_submit_button("➕ Create User", type="primary", use_container_width=True):
                ok,msg=RBAC.create_user(nu,nn,nr,np)
                (st.success if ok else st.error)(msg)

    with a3:
        with st.form("chg_pw"):
            c1,c2,c3 = st.columns(3)
            cu=c1.text_input("Username"); co=c2.text_input("Current Password",type="password"); cn=c3.text_input("New Password",type="password")
            if st.form_submit_button("🔑 Change Password", type="primary", use_container_width=True):
                ok,msg=RBAC.change_password(cu,co,cn)
                (st.success if ok else st.error)(msg)

    with a4:
        st.markdown("#### Role Permissions Matrix")
        rows = []
        all_perms = sorted(set(p for rd in RBAC.ROLES.values()
                               for p in (rd["permissions"] if "*" not in rd["permissions"] else ["*ALL*"])))
        for rn,rd in RBAC.ROLES.items():
            row = {"Role":f"{rd['icon']} {rn}", "Level":rd['level'], "Description":rd['description']}
            for p in all_perms:
                row[p] = "✅" if ("*" in rd["permissions"] or p in rd["permissions"]) else "—"
            rows.append(row)
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
