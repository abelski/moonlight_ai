#!/usr/bin/env python3
"""SessionStart hook: surface dated reminders from plans/reminders.md that are due within 3 days."""
import datetime
import json
import pathlib
import re

AHEAD_DAYS = 3
path = pathlib.Path(__file__).resolve().parents[2] / "plans" / "reminders.md"
today = datetime.date.today()
due, later = [], 0
for line in path.read_text().splitlines() if path.exists() else []:
    m = re.match(r"^- (\d{4}-\d{2}-\d{2}) — (.+)$", line.strip())
    if not m:
        continue
    d = datetime.date.fromisoformat(m.group(1))
    if (d - today).days <= AHEAD_DAYS:
        tag = "OVERDUE" if d < today else ("TODAY" if d == today else f"in {(d - today).days}d")
        due.append(f"[{tag} {d}] {m.group(2)}")
    else:
        later += 1

if due:
    text = "Reminders from plans/reminders.md:\n" + "\n".join(due)
    if later:
        text += f"\n(+{later} later)"
    print(json.dumps({
        "systemMessage": text,
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": text + "\nMention these to the user in your first reply.",
        },
    }))
