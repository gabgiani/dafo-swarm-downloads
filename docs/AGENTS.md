# Agents that work together

This guide explains how DAFO Swarm agents delegate work to each other, where the data they gather goes, and how to design a team of agents. It describes version `0.1.0-20261015.1`.

## Contents

1. [One agent, many tools: why not](#1-one-agent-many-tools-why-not)
2. [Principal and subagents](#2-principal-and-subagents)
3. [What happens when an agent delegates](#3-what-happens-when-an-agent-delegates)
4. [The conversation workspace](#4-the-conversation-workspace)
5. [Background tasks (agents in other apps)](#5-background-tasks-agents-in-other-apps)
6. [Stopping work](#6-stopping-work)
7. [Tuning the delegation instructions](#7-tuning-the-delegation-instructions)
8. [Designing a team: checklist](#8-designing-a-team-checklist)
9. [Limits](#9-limits)

---

## 1. One agent, many tools: why not

Every tool an agent can use is described to the model on every turn. An agent connected to several MCP servers (SAP, MES, email, web, databases...) carries dozens of tool descriptions, and with them:

- **Less room in the context** for the conversation and the data. Small local models feel this first.
- **Worse tool choice.** With many similar tools the model picks the wrong one, mixes arguments between servers or loops through calls that do not help.
- **Longer, slower turns.** More tokens to read before every answer.

Swarm loads large tool sets in groups on demand, which helps, but it does not replace a good design. **Do not overload one agent with MCP servers. Create several specialised agents and let them work together:** each one knows one system well, with a short tool list and a precise prompt, and one principal agent talks to the user and coordinates them.

## 2. Principal and subagents

- A **subagent** is a normal agent (its own prompt, tools, MCP servers and preferred models) that another agent may call.
- The **principal** is the agent the user talks to. In its editor (**Settings → Agents → Subagents**) you choose up to 12 subagents, write one sentence per subagent saying what it does, and pick its **mode**; the principal reads that sentence to decide whom to call.
- An agent marked **Subagent only** is hidden from the chat picker and from `/v1/agents`: users talk to the principal, not to every member of the team.
- Delegation is one level deep. An agent may be a subagent of one agent and have subagents of its own (when users talk to it directly), but a delegated turn never receives `ask_` tools, so there are no chains or loops even if A uses B and B uses A.

Each subagent works in one of three modes, each with its own instructions for the principal and for the subagent:

| Mode | The principal asks for | The subagent replies with |
|---|---|---|
| `data` (**Fetches data**, default) | Specific records: identifiers, periods, fields | One or two lines; the data goes to the workspace and the principal analyses it |
| `answer` (**Answers as an expert**) | A question, as to a specialist, with the facts it needs | A short conclusion (under 2,000 characters) citing the evidence ids it relies on |
| `action` (**Runs actions**) | One exact action, its target and the expected outcome | What it did, what is still running in the background, and what failed |

Example team (names and roles are yours):

| Agent | Tools | Role |
|---|---|---|
| Oliver (principal) | workspace, charts, knowledge | Talks to the user, analyses the data, presents tables and charts |
| William (subagent) | SAP MCP server only | Fetches SAP data: orders, stock, purchases |
| Sara (subagent) | Agent Bridge only | Sends requests to the MES development agent |

To the principal, each subagent is a single tool, `subagents::ask_<name>`, with a `task` and an optional `context`. The subagents' own tools never appear in the principal's tool list, so it stays short however large the team is.

## 3. What happens when an agent delegates

1. The principal calls `ask_william` with a short task: which records, identifiers, period and fields it needs. The subagent sees **only** that task and context, never the conversation.
2. Swarm runs a turn of William with his own prompt, tools and models. Because the task was delegated, his system prompt adds the **Working as a subagent** part of his mode; in `data` mode: fetch the requested data and stop, without analysing, summarising or writing documents.
3. Every tool result William gets is saved in the conversation's **workspace** (next section), each record list as an SQLite table.
4. The principal receives William's one-line reply and, under `data`, the references to everything he saved:

```json
{
  "subagent": "William", "status": "ok", "seconds": 18,
  "answer": "Fetched materials and procurement for production order 151.",
  "tools_used": ["investigate_materials", "investigate_procurement"],
  "data": [
    { "evidence_id": "E42", "tool": "SAPDEMO › investigate_materials",
      "arguments": { "identifier": "151" },
      "contents": ["Fields: fields", "stock: table, 2 rows, 9 columns"],
      "tables": [ { "name": "e42_stock", "rows": 2, "partial": false,
                    "columns": ["ItemCode", "WarehouseCode", "InStock", "Committed", "Ordered"] } ] }
  ]
}
```

5. The principal analyses the data **itself** with SQL (`workspace_query`), and cites the evidence ids (`[E42]`) in its answer so the user can open the data behind each statement.

The data travels as references, not as text pasted into prompts: the principal reads exactly the rows it queries, and nothing is paraphrased on the way.

## 4. The conversation workspace

Each conversation has one workspace, shared by the principal and its subagents:

- **Evidence items** `E1`, `E2`...: every tool result, with the call that produced it and the agent that made it. The answer cites them as `[E3]`.
- **SQLite tables**: each record list in a result becomes a table named after its evidence, such as `e42_stock` or `e43_purchases`. A table is marked **PARTIAL** when the source said it has more records.

Tools the agents use on it:

| Tool | Purpose |
|---|---|
| `workspace_tables` | List the tables with their columns, row counts and evidence ids |
| `workspace_query` | One read-only SQLite `SELECT` to filter, join, count or sum (up to 200 rows) |
| `workspace_load` | Read every page of a listing tool straight into a table |
| `workspace_read` | Read saved text by evidence id, page by page |
| `workspace_files` | List what each agent saved |
| `workspace_write_document` | Save a document, only when the user asks for one |
| `workspace_patch_document` | Change part of a saved document |

Only results an MCP server declares as business data become evidence items. A server can classify its tools and results with the `com.dafonet/tool-classification` and `com.dafonet/result-classification` metadata; technical results, errors and task acknowledgements stay out of the evidence list.

In the dashboard, the **W** button opens the workspace grouped by agent. Opening an item shows its data tables first; the source's notes on how to read them are folded under **Source notes**. In the **MCP tools** trace of an answer, each call shows its evidence id and opens the data it returned. Each agent's folder has its own **Delete** button, and **Delete workspace data** removes everything; the conversation and its answers stay.

## 5. Background tasks (agents in other apps)

An MCP server can answer a call with a **task** instead of a result, for example DAFO Agent Bridge, when the request goes to an AI agent working in VS Code. The turn continues, and Swarm follows the task in the background:

- The chat shows **N calls in progress** next to the agent picker. Clicking it lists each call: who started it, the server, its status and when it began.
- When every task of a delegation has finished, the principal receives the results together and writes one consolidated answer.

## 6. Stopping work

Stopping the answer in the message box (or **Stop all** in the calls list) stops everything the conversation started: the principal's turn, the subagent working at that moment, and every background task still pending, which is cancelled on its server. A late answer is not added to the chat. **Stop waiting** on a single call cancels only that one.

## 7. Tuning the delegation instructions

The delegation behaviour lives in editable parts of the system prompt (**Settings → Server → System prompt**), not in code:

| Part | Sent to | Default behaviour |
|---|---|---|
| **Delegating to subagents** | An agent that has subagents | Ask subagents only for what they do; analyse data with `workspace_tables` and `workspace_query`; cite evidence ids; do not ask again for data already saved |
| **Subagent mode: … (principal)** | The principal, in each `ask_` tool's description | How to ask a subagent of that mode |
| **Working as a subagent: …** | An agent running a delegated task; **not** when a user talks to it directly | `data`: fetch and stop, reply in one or two lines. `answer`: analyse and conclude with evidence ids. `action`: do exactly the requested action once and report |

Because the last part is only sent to delegated turns, the same agent can fetch quietly for a principal and still explain its findings when a user chats with it directly.

## 8. Designing a team: checklist

- **One system per subagent.** SAP in one agent, MES in another, web research in a third. Give each only the MCP tools of its system.
- **Write the subagent's description for the principal**: what data it can fetch, in one sentence ("Fetches SAP production orders, stock, purchases and receipts").
- **Keep the principal light.** It needs the workspace, charts and perhaps the knowledge base, not the data sources.
- **Ask for data, analyse in the principal.** Do not ask a `data` subagent to "assess the risk": ask it for the order, its materials and their stock, and let the principal decide. Use `answer` mode only when the subagent's own data needs an expert reading.
- **Use `action` mode for subagents that change things** (send a request to another app, create a record), and let them act only when the user asked for it.
- **Mark helpers as Subagent only** so users talk to one interlocutor.
- **Choose models per role.** Subagents that only fetch data work well on small local models; give the principal the stronger model.

## 9. Limits

| Limit | Value |
|---|---|
| Subagents per agent | 12 |
| Subagent calls per principal turn | 8 |
| Tool calls per turn (principal or subagent) | 16 by default |
| Time per subagent call | No fixed total: the call is stopped after the node's request timeout (300 s by default) **without activity**; every generated token or tool step resets it |
| Subagent reply text | 2,400 characters; data travels as workspace references |
| Depth | 1 (a delegated turn never delegates again) |
| Calls | Sequential, one subagent at a time |
| `workspace_query` | One `SELECT`, 10 s, 200 rows, 12,000 characters of output |

Subagents are used by the dashboard chat and Microsoft Teams bots, and by `/v1/responses` when the request names the principal in `agent`. `/v1/chat/completions` and the web chat widget do not delegate. The subagent's own tools always come from its saved configuration.
