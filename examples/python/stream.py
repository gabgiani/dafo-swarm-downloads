"""Streams tokens as they are generated.

    python stream.py "Write a short paragraph about predictive maintenance."
"""
import argparse
import sys

from swarm import active_model, client

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("prompt", nargs="?", default="Write a short paragraph about predictive maintenance.")
parser.add_argument("--max-tokens", type=int, default=300, help="Maximum answer tokens (default: 300).")
args = parser.parse_args()
prompt = args.prompt
print("Question:", prompt, flush=True)
print("Answer: ", end="", flush=True)
stream = client.chat.completions.create(
    model=active_model(),
    messages=[{"role": "user", "content": prompt}],
    stream=True,
    stream_options={"include_usage": True},
    max_completion_tokens=args.max_tokens,
)
finish_reason = None
for chunk in stream:
    if chunk.choices and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
    if chunk.choices and chunk.choices[0].finish_reason:
        finish_reason = chunk.choices[0].finish_reason
    if chunk.usage:
        print(f"\n[{chunk.usage.completion_tokens} tokens]")
print(f"[finish: {finish_reason}]", flush=True)
if finish_reason == "length":
    print("Answer reached the token limit; retry with --max-tokens 512 if the model context allows it.", file=sys.stderr)
