// Stores facts in an agent's knowledge base, searches them, and asks a question that uses them.
//   node knowledge.mjs                  # first enabled agent
//   AGENT=agent-... node knowledge.mjs
const SWARM_URL = (process.env.SWARM_URL ?? "http://127.0.0.1:43100").replace(/\/$/, "");

async function api(path, init) {
  const response = await fetch(`${SWARM_URL}${path}`, {
    ...init,
    headers: { "content-type": "application/json", ...(init?.headers ?? {}) },
  });
  const text = await response.text();
  if (!response.ok) throw new Error(`${path}: ${response.status} ${text}`);
  return text ? JSON.parse(text) : null;
}

const agents = (await api("/v1/agents")).data;
const agent = process.env.AGENT ?? agents[0]?.id;
if (!agent) throw new Error("No enabled agent. Create one in the dashboard first.");

const facts = [
  { subject: "Line 3", predicate: "plc_supplier", object: "Siemens",
    content: "Line 3 uses a Siemens S7-1500 PLC. Contact: Carlos Gómez, carlos@example.com." },
  { subject: "Line 3", predicate: "maintenance_window", object: "Friday 06:00",
    content: "Preventive maintenance of line 3 runs every Friday from 06:00 to 08:00." },
];
for (const fact of facts) {
  const item = await api(`/api/agents/${agent}/knowledge`, { method: "POST", body: JSON.stringify(fact) });
  console.log("stored", item.id, item.subject, `[${item.predicate}]`, item.object);
}

const results = await api(`/api/agents/${agent}/knowledge/search`, {
  method: "POST",
  body: JSON.stringify({ query: "who maintains line 3 and when", limit: 3 }),
});
for (const { score, item, match_type } of results) {
  console.log(score.toFixed(2), item.subject, `[${item.predicate}]`, item.object, `(${match_type})`);
}

const model = (await api("/v1/models")).data[0].id;
const reply = await api("/v1/chat/completions", {
  method: "POST",
  body: JSON.stringify({
    model,
    agent,
    messages: [{ role: "user", content: "Can we stop line 3 on Friday at 7am? Who do I call about the PLC?" }],
  }),
});
console.log("\n" + reply.choices[0].message.content);
