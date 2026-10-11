# Web Research Agent

A small, readable AI agent that researches a question on the web and writes a cited markdown report.
It runs a tool-use loop with Claude: **plan → search → read pages → cross-check → report**.

## Features
- Two tools: `web_search` (DuckDuckGo, no API key) and `fetch_page` (clean text extraction)
- Agent loop with a step budget and a forced final answer if the budget runs out
- SSRF guard: refuses localhost and private-network URLs
- Source-grounded prompt: no invented URLs, flags weak or conflicting evidence
- ~150 lines of code, easy to extend with new tools

## Quick start
```bash
git clone <your-repo-url> && cd web-research-agent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # add your ANTHROPIC_API_KEY
python agent.py "What are the main trade-offs of small modular nuclear reactors?" --out report.md
```

Options: `--model`, `--max-steps`, `--out`, `--quiet`.

## How it works
```
question ─► Claude ──tool_use──► web_search / fetch_page ──tool_result──┐
              ▲                                                         │
              └─────────────────────── loop ◄───────────────────────────┘
              └─► final cited report
```

## Extend it
Add a schema to `TOOL_SCHEMAS` and a branch in `run_tool` in `tools.py` (e.g. a PDF reader, Wikipedia, or a vector store).

## Tests
```bash
pytest
```

## Limitations
Search quality depends on DuckDuckGo results; pages that need JavaScript won't render. Always verify important claims.

## License
MIT
