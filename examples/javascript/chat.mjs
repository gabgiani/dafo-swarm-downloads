// Chat completion with the official OpenAI SDK, optionally as an agent.
//   node chat.mjs "Explain OEE in two sentences."
//   AGENT=agent-... node chat.mjs "Who is the PLC contact for line 3?"
import OpenAI from "openai";

const SWARM_URL = (process.env.SWARM_URL ?? "http://127.0.0.1:43100").replace(/\/$/, "");
// The node ignores the key; distributed generation of long answers can take minutes.
const client = new OpenAI({ baseURL: `${SWARM_URL}/v1`, apiKey: "unused", timeout: 600_000 });

const { data: models } = await client.models.list();
if (models.length === 0) throw new Error("The swarm has no active model yet.");

const reply = await client.chat.completions.create({
  model: models[0].id,
  messages: [
    { role: "system", content: "You are a concise manufacturing assistant." },
    { role: "user", content: process.argv[2] ?? "Explain OEE in two sentences." },
  ],
  max_completion_tokens: 300,
  // DAFO Swarm extension: adds the agent's instructions and knowledge.
  ...(process.env.AGENT ? { agent: process.env.AGENT } : {}),
});
console.log(reply.choices[0].message.content);
console.log(`[${reply.usage.completion_tokens} tokens, finish: ${reply.choices[0].finish_reason}]`);
