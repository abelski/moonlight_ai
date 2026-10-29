---
name: productivity-grilling
description: Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking, or uses any 'grill' trigger phrases.
---

Interview the user relentlessly until you reach a shared understanding. Map this as a **design tree**: every decision branches into the decisions that hang off it.

Ask **one question per turn**. Pick it from the **frontier**: the decisions whose prerequisites are already settled, the questions you can ask _now_ without guessing at answers you haven't heard yet. Give your recommended answer with the question, then wait for the reply. Recompute the frontier after every answer.

**Big ideas.** If the tree has many open branches (more than about five questions on the frontier at once), ask once, before the next question: "One at a time, or in rounds?" Follow the answer until the user changes it. In rounds, number the questions in each round, give a recommended answer for each, and wait for all of them before the next round.

Format a question like so:

```
❓ **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>
```

Finding _facts_ is your job, never the user's. When a frontier question needs a fact from the environment (filesystem, tools, etc.), dispatch a sub-agent to find it; don't ask the user for anything you could look up yourself. Don't block on it: a running exploration is an unsettled prerequisite, so only the questions downstream of it wait for the sub-agent to report; ask the rest of the frontier now. The _decisions_ are the user's: put each to them and wait.

The session is done when the frontier is empty: every branch of the design tree visited, nothing left silently assumed. Do not act on it until the user confirms you have reached a shared understanding.
