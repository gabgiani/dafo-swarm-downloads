"""Streams tokens as they are generated.

    python stream.py "Write a short paragraph about predictive maintenance."
"""
import sys

from swarm import active_model, client

prompt = sys.argv[1] if len(sys.argv) > 1 else "Write a short paragraph about predictive maintenance."
stream = client.chat.completions.create(
    model=active_model(),
    messages=[{"role": "user", "content": prompt}],
    stream=True,
    stream_options={"include_usage": True},
)
for chunk in stream:
    if chunk.choices and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
    if chunk.usage:
        print(f"\n[{chunk.usage.completion_tokens} tokens]")
