"""
Multi-Agent Orchestrator
Pipeline: Schema → SQL → Validation → Optimization → [Execute] → Explanation → Visualization
"""
import json
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AgentStep:
    agent: str
    icon: str
    status: str = "pending"   # pending | running | success | warning | error
    output: Any = None
    duration_ms: int = 0
    error: str = ""


@dataclass
class PipelineResult:
    question: str
    steps: List[AgentStep] = field(default_factory=list)
    final_sql: str = ""
    explanation: Dict = field(default_factory=dict)
    viz_spec: Dict = field(default_factory=dict)
    index_suggestions: List[str] = field(default_factory=list)
    success: bool = False
    error: str = ""


class AgentOrchestrator:
    """Chains six specialist AI agents to answer a natural-language database question."""

    def __init__(self, ai_agent, schema_context: str = "", role: str = "Analyst"):
        self.ai = ai_agent
        self.schema = schema_context
        self.role = role

    # ── Public pipeline entry point ────────────────────────────────────────
    def run_pipeline(
        self,
        question: str,
        progress_callback=None,
    ) -> PipelineResult:
        result = PipelineResult(question=question)
        ctx: Dict = {"question": question, "schema": self.schema[:6000]}

        stages = [
            ("🗂️ Schema Agent",      self._schema_agent),
            ("📝 SQL Agent",          self._sql_agent),
            ("✅ Validation Agent",   self._validation_agent),
            ("⚡ Optimization Agent", self._optimization_agent),
        ]

        for name, fn in stages:
            icon = name.split()[0]
            step = AgentStep(agent=name, icon=icon, status="running")
            result.steps.append(step)

            if progress_callback:
                progress_callback(name, "running")

            t0 = time.time()
            try:
                output = fn(ctx)
                step.output = output
                step.status = "success" if not output.get("_error") else "warning"
                step.duration_ms = int((time.time() - t0) * 1000)
                ctx[name] = output
                if progress_callback:
                    progress_callback(name, "success")
            except Exception as exc:
                step.status = "error"
                step.error = str(exc)
                step.duration_ms = int((time.time() - t0) * 1000)
                result.error = str(exc)
                if progress_callback:
                    progress_callback(name, "error")
                break

        # Extract final SQL
        opt = ctx.get("⚡ Optimization Agent", {})
        sql = ctx.get("📝 SQL Agent", {})
        result.final_sql = (
            opt.get("optimized_sql")
            or sql.get("sql")
            or ""
        )

        # Collect index suggestions from optimization agent
        result.index_suggestions = opt.get("index_suggestions", [])
        result.success = bool(result.final_sql)
        return result

    def explain_and_visualize(
        self, sql: str, df_json: str, question: str
    ) -> Dict:
        """Run explanation + visualization agents on executed results."""
        return {
            "explanation": self._explanation_agent(sql, df_json, question),
            "visualization": self._visualization_agent(df_json, question),
        }

    # ── JSON parser helper ─────────────────────────────────────────────────
    def _parse(self, text: str, default: dict) -> dict:
        for pattern in [r"```json\s*(.*?)\s*```", r"(\{[\s\S]*\})"]:
            m = re.search(pattern, text, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group(1))
                except Exception:
                    continue
        return {**default, "_raw": text[:300]}

    # ── Agent 1: Schema ────────────────────────────────────────────────────
    def _schema_agent(self, ctx: dict) -> dict:
        prompt = (
            "You are the **Schema Agent** for an Enterprise SQL Server database.\n"
            "Analyse the user question and identify the exact database objects needed.\n\n"
            f"USER QUESTION: {ctx['question']}\n\n"
            f"DATABASE SCHEMA:\n{ctx['schema'][:4000]}\n\n"
            "Reply with ONLY a JSON object — no prose:\n"
            "{\n"
            '  "relevant_tables": ["schema.TableName"],\n'
            '  "relevant_columns": ["TableName.ColumnName"],\n'
            '  "join_conditions": ["t1.col = t2.col"],\n'
            '  "business_entities": ["Entity"],\n'
            '  "complexity": "Simple|Medium|Complex",\n'
            '  "confidence": 0.0,\n'
            '  "notes": "brief"\n'
            "}"
        )
        r = self.ai.chat([{"role": "user", "content": prompt}])
        return self._parse(r, {
            "relevant_tables": [], "relevant_columns": [],
            "join_conditions": [], "business_entities": [],
            "complexity": "Unknown", "confidence": 0.5, "notes": r[:200],
        })

    # ── Agent 2: SQL Generation ────────────────────────────────────────────
    def _sql_agent(self, ctx: dict) -> dict:
        schema_info = ctx.get("🗂️ Schema Agent", {})
        tables = ", ".join(schema_info.get("relevant_tables", []))
        prompt = (
            "You are the **SQL Agent**. Generate an optimized T-SQL query.\n\n"
            f"USER QUESTION: {ctx['question']}\n"
            f"RELEVANT TABLES: {tables}\n\n"
            f"SCHEMA:\n{ctx['schema'][:3000]}\n\n"
            "Rules:\n"
            "- SQL Server T-SQL ONLY\n"
            "- Schema-qualified names (schema.table)\n"
            "- No SELECT * — only required columns\n"
            "- TOP 1000 unless count/aggregate\n"
            "- Inline comments on complex steps\n\n"
            "Reply with ONLY JSON:\n"
            "{\n"
            '  "sql": "-- T-SQL\\nSELECT ...",\n'
            '  "explanation": "what it does",\n'
            '  "estimated_rows": "~N",\n'
            '  "complexity": "Simple|Medium|Complex",\n'
            '  "tables_used": ["schema.Table"]\n'
            "}"
        )
        r = self.ai.chat([{"role": "user", "content": prompt}])
        return self._parse(r, {
            "sql": "", "explanation": r[:300],
            "estimated_rows": "Unknown", "complexity": "Unknown", "tables_used": [],
        })

    # ── Agent 3: Validation ────────────────────────────────────────────────
    def _validation_agent(self, ctx: dict) -> dict:
        sql = ctx.get("📝 SQL Agent", {}).get("sql", "")
        if not sql:
            return {"valid": False, "issues": ["No SQL generated"], "corrected_sql": ""}

        prompt = (
            "You are the **Validation Agent** for SQL Server.\n"
            "Validate this T-SQL for syntax, security, and anti-patterns.\n\n"
            f"```sql\n{sql}\n```\n\n"
            "Check:\n"
            "1. T-SQL syntax errors\n"
            "2. Forbidden commands: DROP/DELETE/UPDATE/TRUNCATE/ALTER/EXEC/xp_cmdshell\n"
            "3. Anti-patterns: SELECT *, missing TOP, cartesian products\n"
            "4. Missing schema qualifiers\n"
            "5. Potential NULL handling issues\n\n"
            "Reply with ONLY JSON:\n"
            "{\n"
            '  "valid": true,\n'
            '  "issues": [],\n'
            '  "warnings": [],\n'
            '  "security_ok": true,\n'
            '  "blocked_commands": [],\n'
            '  "corrected_sql": "same or fixed SQL",\n'
            '  "score": 90\n'
            "}"
        )
        r = self.ai.chat([{"role": "user", "content": prompt}])
        result = self._parse(r, {
            "valid": True, "issues": [], "warnings": [],
            "security_ok": True, "blocked_commands": [],
            "corrected_sql": sql, "score": 75,
        })
        if not result.get("corrected_sql"):
            result["corrected_sql"] = sql
        return result

    # ── Agent 4: Optimization ──────────────────────────────────────────────
    def _optimization_agent(self, ctx: dict) -> dict:
        val = ctx.get("✅ Validation Agent", {})
        sql_out = ctx.get("📝 SQL Agent", {})
        sql = val.get("corrected_sql") or sql_out.get("sql", "")
        if not sql:
            return {"optimized_sql": "", "changes": [], "index_suggestions": []}

        prompt = (
            "You are the **Optimization Agent** for SQL Server.\n"
            "Optimize this T-SQL for maximum performance.\n\n"
            f"```sql\n{sql}\n```\n\n"
            f"SCHEMA:\n{ctx['schema'][:2000]}\n\n"
            "Optimize:\n"
            "1. Sargable predicates for index use\n"
            "2. Replace subqueries with CTEs/JOINs\n"
            "3. Add TOP if missing\n"
            "4. Eliminate cursors → set-based\n"
            "5. Fix implicit type conversions\n"
            "6. Use EXISTS over IN for subqueries\n"
            "7. Add WITH (NOLOCK) for read-only reporting\n\n"
            "Reply with ONLY JSON:\n"
            "{\n"
            '  "optimized_sql": "-- Optimized T-SQL\\nSELECT ...",\n'
            '  "changes": ["Change: reason"],\n'
            '  "performance_notes": "explanation",\n'
            '  "index_suggestions": ["CREATE NONCLUSTERED INDEX ..."],\n'
            '  "estimated_improvement": "Low|Medium|High"\n'
            "}"
        )
        r = self.ai.chat([{"role": "user", "content": prompt}])
        result = self._parse(r, {
            "optimized_sql": sql, "changes": [],
            "performance_notes": "No changes needed.",
            "index_suggestions": [], "estimated_improvement": "Low",
        })
        if not result.get("optimized_sql"):
            result["optimized_sql"] = sql
        return result

    # ── Agent 5: Explanation ───────────────────────────────────────────────
    def _explanation_agent(self, sql: str, df_json: str, question: str) -> dict:
        prompt = (
            "You are the **Explanation Agent**.\n"
            "Turn SQL results into a concise business narrative.\n\n"
            f"ORIGINAL QUESTION: {question}\n\n"
            f"SQL:\n```sql\n{sql[:800]}\n```\n\n"
            f"RESULTS SAMPLE:\n{df_json[:2000]}\n\n"
            "Reply with ONLY JSON:\n"
            "{\n"
            '  "summary": "2-3 sentence business summary",\n'
            '  "key_findings": ["Finding 1"],\n'
            '  "trends": ["Trend if applicable"],\n'
            '  "anomalies": ["Unusual patterns"],\n'
            '  "business_insights": ["Actionable insight"],\n'
            '  "recommendations": ["Business recommendation"]\n'
            "}"
        )
        r = self.ai.chat([{"role": "user", "content": prompt}])
        return self._parse(r, {
            "summary": "Query executed successfully.",
            "key_findings": [], "trends": [], "anomalies": [],
            "business_insights": [], "recommendations": [],
        })

    # ── Agent 6: Visualization ─────────────────────────────────────────────
    def _visualization_agent(self, df_json: str, question: str) -> dict:
        prompt = (
            "You are the **Visualization Agent**.\n"
            "Recommend the best chart for these query results.\n\n"
            f"QUESTION: {question}\n"
            f"DATA SAMPLE:\n{df_json[:1500]}\n\n"
            "Reply with ONLY JSON:\n"
            "{\n"
            '  "chart_type": "bar|line|pie|scatter|histogram|heatmap|table",\n'
            '  "x_column": "column name",\n'
            '  "y_column": "metric column",\n'
            '  "color_column": null,\n'
            '  "title": "Chart title",\n'
            '  "insight": "key visual insight",\n'
            '  "why": "why this chart type"\n'
            "}"
        )
        r = self.ai.chat([{"role": "user", "content": prompt}])
        return self._parse(r, {
            "chart_type": "table", "x_column": "", "y_column": "",
            "color_column": None, "title": "Query Results",
            "insight": "", "why": "Table view for detailed data",
        })

    # ── Utility: suggest relationships ────────────────────────────────────
    def suggest_relationships(self, schema_summary: str) -> dict:
        prompt = (
            "You are a **Database Design Expert** analyzing a SQL Server database.\n"
            "Identify MISSING foreign key relationships that should exist based on:\n"
            "- Matching column names (e.g., CustomerID in multiple tables)\n"
            "- Naming conventions (e.g., table_id pattern)\n"
            "- Data type compatibility\n"
            "- Business logic\n\n"
            f"CURRENT SCHEMA:\n{schema_summary[:5000]}\n\n"
            "Reply with ONLY JSON:\n"
            "{\n"
            '  "suggested_relationships": [\n'
            '    {\n'
            '      "parent_table": "schema.Table",\n'
            '      "parent_column": "ColumnName",\n'
            '      "ref_table": "schema.Table",\n'
            '      "ref_column": "ColumnName",\n'
            '      "confidence": 0.9,\n'
            '      "reason": "why this relationship likely exists",\n'
            '      "alter_sql": "ALTER TABLE ... ADD CONSTRAINT ... FOREIGN KEY ..."\n'
            "    }\n"
            "  ],\n"
            '  "orphan_tables": ["schema.TableName"],\n'
            '  "design_issues": ["Issue description"],\n'
            '  "recommendations": ["Recommendation"]\n'
            "}"
        )
        r = self.ai.chat([{"role": "user", "content": prompt}])
        return self._parse(r, {
            "suggested_relationships": [], "orphan_tables": [],
            "design_issues": [], "recommendations": [],
        })

    def analyze_trigger(self, trigger_def: str) -> str:
        return self.ai.chat([{"role": "user", "content":
            f"Explain this SQL Server trigger in business terms.\n"
            f"Cover: purpose, when it fires, what it does, side effects, performance impact.\n\n"
            f"```sql\n{trigger_def}\n```"
        }])

    def analyze_function(self, func_def: str) -> str:
        return self.ai.chat([{"role": "user", "content":
            f"Explain this SQL Server function.\n"
            f"Cover: purpose, parameters, return value, usage examples, "
            f"performance considerations (especially if it causes row-by-row evaluation).\n\n"
            f"```sql\n{func_def}\n```"
        }])
