"""Single chat completion and a short multi-turn conversation.

    python chat.py "Explain OEE in two sentences."
"""
import sys

from swarm import active_model, client

model = active_model()
question = sys.argv[1] if len(sys.argv) > 1 else "Explain OEE in two sentences."

messages = [
    {"role": "system", "content": "You are a concise manufacturing assistant."},
    {"role": "user", "content": question},
]
reply = client.chat.completions.create(model=model, messages=messages, max_completion_tokens=300, temperature=0.2)
answer = reply.choices[0].message.content
print(answer)
print(f"[{reply.usage.completion_tokens} tokens, finish: {reply.choices[0].finish_reason}]\n")

# Follow-up: send the history back, as with any OpenAI-compatible server.
messages += [{"role": "assistant", "content": answer}, {"role": "user", "content": "Give one example with numbers."}]
follow_up = client.chat.completions.create(model=model, messages=messages, max_completion_tokens=300)
print(follow_up.choices[0].message.content)
