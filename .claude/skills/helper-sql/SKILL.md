---
name: helper-sql
description: Run SQL against this project's database. Pass a query as $ARGUMENTS or be prompted for one.
---

Run SQL against this project's database.

## How to get the connection string

Read the project's env file (e.g. `.env`, `backend/.env`) and extract the database URL
(`DATABASE_URL` or equivalent). Never hard-code it — always read the file fresh.

## Run the query

If `$ARGUMENTS` is non-empty, treat it as the SQL to run.

Otherwise use `AskUserQuestion` to ask:
- Question: "Enter the SQL to run:"
- Type: free text input

Execute with:

```bash
psql "<DATABASE_URL>" -c "<SQL>"
```

For multi-statement SQL (semicolon-separated), use `psql "<DATABASE_URL>" <<'EOF'\n<SQL>\nEOF` via bash heredoc so all statements run in one session. (Swap `psql` for the project's actual DB client if it isn't Postgres.)

## Output

- Print the full output (rows returned, UPDATE/INSERT counts, errors).
- If the query returns rows, display them as a markdown table.
- If it fails, show the error and suggest a fix.

## Notes

- Do not push any changes to git.
- For destructive queries (DROP, DELETE without WHERE, TRUNCATE) ask the user to confirm before running.
- Keep a schema reference (table → PK → key columns) in this file once the project's schema
  stabilizes, and update it whenever the models/migrations change — that's what makes this skill
  fast instead of needing a fresh schema lookup on every call.
