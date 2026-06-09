from typing import List, Dict, Optional

_SYSTEM_PROMPT = """You are an Enterprise SQL Server Data Intelligence Agent. You:

1. Convert natural language questions into optimized T-SQL (SQL Server only).
2. Explain database schemas, entity relationships, FK/PK constraints in business terms.
3. Analyze stored procedures — identify N+1 queries, cursor misuse, implicit conversions,
   missing index hints, parameter sniffing issues, and suggest rewrites.
4. Recommend indexes with CREATE INDEX statements and explain the business impact.
5. Present data findings in non-technical, business-friendly language.
6. NEVER suggest DROP, DELETE, UPDATE, INSERT, ALTER, EXEC, xp_cmdshell, or TRUNCATE.
7. Always use schema-qualified names, avoid SELECT *, add TOP clauses, and explain
   query plan considerations.
8. Format responses with clear Markdown headings, bullet points, and SQL code blocks.

When generating SQL:
- Use `schema.table` qualified names.
- Add comments explaining each major step.
- Prefer indexed columns in WHERE / JOIN predicates.
- Suggest covering index columns when relevant.
"""


class AIAgent:
    """Calls Azure OpenAI using the official openai SDK (AzureOpenAI client)."""

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        model: str = "gpt-4.1-mini",
        api_version: str = "2024-12-01-preview",
    ):
        from openai import AzureOpenAI
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.api_version = api_version
        self._client = AzureOpenAI(
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
            api_version=self.api_version,
        )

    # ── public interface ──────────────────────────────────────────────────
    def chat(
        self,
        messages: List[Dict],
        schema_context: Optional[str] = None,
    ) -> str:
        system_content = _SYSTEM_PROMPT
        if schema_context:
            system_content += (
                "\n\n---\nCURRENT DATABASE SCHEMA CONTEXT\n"
                + "=" * 50 + "\n"
                + schema_context
            )

        full_messages = [{"role": "system", "content": system_content}]
        full_messages.extend(messages)

        response = self._client.chat.completions.create(
            model=self.model,
            messages=full_messages,
            max_tokens=8192,
            temperature=0.7,
        )
        return response.choices[0].message.content

    def test(self) -> str:
        return self.chat([{"role": "user", "content": "Reply with exactly: CONNECTED"}])
