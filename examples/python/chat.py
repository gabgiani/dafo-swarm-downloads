"""Single chat completion and a short multi-turn conversation.

    python chat.py "Explain OEE in two sentences."
"""
import argparse
import sys

from swarm import active_model, client

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("question", nargs="?", default="Explain OEE in two sentences.")
parser.add_argument("--max-tokens", type=int, default=300, help="Maximum tokens for each answer (default: 300).")
args = parser.parse_args()
model = active_model()
question = args.question
print("Question:", question, flush=True)

messages = [
    {"role": "system", "content": "You are a concise manufacturing assistant."},
    {"role": "user", "content": question},
]
reply = client.chat.completions.create(model=model, messages=messages, max_completion_tokens=args.max_tokens, temperature=0.2)
answer = reply.choices[0].message.content
print("Answer:", answer)
print(f"[{reply.usage.completion_tokens} tokens, finish: {reply.choices[0].finish_reason}]\n")
if reply.choices[0].finish_reason == "length":
    raise SystemExit("Answer reached the token limit. Retry with --max-tokens 512 if the model context allows it.")

# Follow-up: send the history back, as with any OpenAI-compatible server.
follow_up_question = "Give one example with numbers."
print("Follow-up question:", follow_up_question, flush=True)
messages += [{"role": "assistant", "content": answer}, {"role": "user", "content": follow_up_question}]
follow_up = client.chat.completions.create(model=model, messages=messages, max_completion_tokens=args.max_tokens)
print("Follow-up answer:", follow_up.choices[0].message.content)
print(f"[{follow_up.usage.completion_tokens} tokens, finish: {follow_up.choices[0].finish_reason}]")
if follow_up.choices[0].finish_reason == "length":
    print("Follow-up reached the token limit. Retry with --max-tokens 512 if the model context allows it.", file=sys.stderr)
