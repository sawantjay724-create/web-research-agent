"""Web research agent: plans, searches, reads pages, and writes a cited report."""
import argparse
import os
import sys

from anthropic import Anthropic
from dotenv import load_dotenv

from tools import TOOL_SCHEMAS, run_tool

SYSTEM = """You are a careful web research agent.
1. Break the question into 2-4 sub-questions.
2. Use web_search, then fetch_page on the most credible results (prefer primary sources).
3. Cross-check important claims across at least two sources when possible.
4. Finish with a concise markdown report: a short answer first, key findings, then a
   'Sources' list of URLs you actually used. Say clearly where evidence is weak or conflicting.
Never invent URLs or facts that you did not see in tool results."""


def research(question: str, model: str, max_steps: int = 12, verbose: bool = True) -> str:
    client = Anthropic()
    messages = [{"role": "user", "content": question}]

    for step in range(1, max_steps + 1):
        resp = client.messages.create(
            model=model, max_tokens=4096, system=SYSTEM,
            tools=TOOL_SCHEMAS, messages=messages,
        )
        messages.append({"role": "assistant", "content": resp.content})

        if resp.stop_reason != "tool_use":
            return "".join(b.text for b in resp.content if b.type == "text")

        results = []
        for block in resp.content:
            if block.type == "tool_use":
                if verbose:
                    print(f"[step {step}] {block.name}({block.input})", file=sys.stderr)
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": run_tool(block.name, block.input),
                })
        messages.append({"role": "user", "content": results})

    # Step budget exhausted: ask for a final answer without tools.
    messages.append({"role": "user", "content": "Step limit reached. Write the final cited report now."})
    resp = client.messages.create(model=model, max_tokens=4096, system=SYSTEM, messages=messages)
    return "".join(b.text for b in resp.content if b.type == "text")


def main() -> None:
    load_dotenv()
    p = argparse.ArgumentParser(description="Web research agent")
    p.add_argument("question", help="Research question")
    p.add_argument("--model", default=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5"))
    p.add_argument("--max-steps", type=int, default=12)
    p.add_argument("--out", help="Save the report to this markdown file")
    p.add_argument("--quiet", action="store_true", help="Hide tool-call logging")
    args = p.parse_args()

    if not os.getenv("ANTHROPIC_API_KEY"):
        sys.exit("Set ANTHROPIC_API_KEY (see .env.example).")

    report = research(args.question, args.model, args.max_steps, verbose=not args.quiet)
    print(report)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(report)


if __name__ == "__main__":
    main()
