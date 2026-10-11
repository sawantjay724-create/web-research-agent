"""Tools the research agent can call: web search and page fetching."""
import ipaddress
import socket
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from ddgs import DDGS

MAX_PAGE_CHARS = 8000

TOOL_SCHEMAS = [
    {
        "name": "web_search",
        "description": "Search the web. Returns titles, URLs and snippets for the top results.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Short, specific search query"},
                "max_results": {"type": "integer", "description": "1-8, default 5"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "fetch_page",
        "description": "Download a web page and return its readable text (truncated).",
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string", "description": "Absolute http(s) URL"}},
            "required": ["url"],
        },
    },
]


def is_safe_url(url: str) -> bool:
    """Allow only public http(s) hosts (blocks localhost / private networks)."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return False
    try:
        for info in socket.getaddrinfo(parsed.hostname, None):
            ip = ipaddress.ip_address(info[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return False
    except (socket.gaierror, ValueError):
        return False
    return True


def web_search(query: str, max_results: int = 5) -> str:
    max_results = max(1, min(int(max_results), 8))
    try:
        results = DDGS().text(query, max_results=max_results)
    except Exception as exc:  # network / rate-limit errors go back to the model
        return f"Search failed: {exc}"
    if not results:
        return "No results."
    return "\n\n".join(
        f"{i}. {r.get('title')}\n   {r.get('href')}\n   {r.get('body')}"
        for i, r in enumerate(results, 1)
    )


def fetch_page(url: str) -> str:
    if not is_safe_url(url):
        return "Refused: URL must be a public http(s) address."
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "web-research-agent/1.0"})
        resp.raise_for_status()
    except requests.RequestException as exc:
        return f"Fetch failed: {exc}"
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    text = " ".join(soup.get_text(" ").split())
    return text[:MAX_PAGE_CHARS] + (" …[truncated]" if len(text) > MAX_PAGE_CHARS else "")


def run_tool(name: str, args: dict) -> str:
    if name == "web_search":
        return web_search(args["query"], args.get("max_results", 5))
    if name == "fetch_page":
        return fetch_page(args["url"])
    return f"Unknown tool: {name}"
