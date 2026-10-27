#!/usr/bin/env python3
"""cote-walk MCP server — the walk loop as callable tools.

Exposes kb/cote.py's operations over MCP stdio so reading pages, appending
ledger rows, verifying quotes, rebuilding, gating and shipping are tool calls
rather than shell commands. No third-party dependencies; stdout is reserved for
the JSON-RPC channel, so every operation's output is captured and returned as
text content.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import traceback
from types import SimpleNamespace

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "kb"))

import cote  # noqa: E402  (the CLI module, used as a library)

PROTOCOL = "2025-06-18"

TOOLS = [
    {
        "name": "status",
        "description": "Current walk position: git branch state, uncommitted files, the last boundary marker in every ledger, and the tail of both progress files.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "next",
        "description": "Show the volume's chapter map with walked/remaining status and print the next chapter's page range plus the read commands for it. Omit vol for the first unfinished volume.",
        "inputSchema": {
            "type": "object",
            "properties": {"vol": {"type": "string", "description": "Volume id, e.g. y1v3. Omit for the first unfinished volume."}},
        },
    },
    {
        "name": "chapters",
        "description": "List a volume's chapter/section page ranges. Omit vol for the first unfinished volume.",
        "inputSchema": {
            "type": "object",
            "properties": {"vol": {"type": "string", "description": "Volume id. Omit for the first unfinished volume."}},
        },
    },
    {
        "name": "read_pages",
        "description": "Extract a page range from a volume's translated text, verbatim, in page order. Optionally flag blank and short pages so illustration pages are identified rather than guessed.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "vol": {"type": "string", "description": "Volume id, e.g. y1v2."},
                "pages": {"type": "string", "description": "Range like 152-170 or a single page 155."},
                "blank": {"type": "boolean", "description": "Also report pages with no prose or three lines or fewer."},
            },
            "required": ["vol", "pages"],
        },
    },
    {
        "name": "append",
        "description": "Append a section to a ledger file inside a volume block, keeping exactly one chapter boundary marker. The section may be given inline or read from a file.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file": {"type": "string", "description": "Repo-relative ledger path, e.g. ledgers/people/sakura-airi.md."},
                "section": {"type": "string", "description": "Section text, inline."},
                "from_file": {"type": "string", "description": "Repo-relative file holding the section text."},
                "under": {"type": "string", "description": "Volume heading to insert inside, e.g. y1v2. Omit to append at end."},
                "stamp": {"type": "string", "description": 'Boundary marker text, e.g. "y1v2 ch5 → p.189".'},
                "at_end": {"type": "boolean", "description": "Force appending at end of file."},
            },
            "required": ["file"],
        },
    },
    {
        "name": "ledger_new",
        "description": "Create a new per-entity ledger file when a named character, place or system needs its own page.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kind": {"type": "string", "description": "people, places, systems, exams, concepts or volumes."},
                "stem": {"type": "string", "description": "File stem, e.g. kanzaki-ryuuji."},
                "header": {"type": "string", "description": "Header line, e.g. 'char_id: kanzaki-ryuuji · class: Class 1-B · status: minor'."},
                "title": {"type": "string"},
                "start_vol": {"type": "string", "description": "Volume to open. Omit for the first unfinished volume."},
                "force": {"type": "boolean"},
            },
            "required": ["kind", "stem", "header"],
        },
    },
    {
        "name": "verify",
        "description": "Check every quoted line in the ledgers against the volume text: dialogue rows and all other quoted strings. Fix the row, never the checker.",
        "inputSchema": {
            "type": "object",
            "properties": {"vol": {"type": "string", "description": "Volume id; omit to check everything."}},
        },
    },
    {
        "name": "build",
        "description": "Rebuild the static site from the ledgers. With docs=true, mirror the result into the committed docs/ tree. Prints the determinism hash.",
        "inputSchema": {
            "type": "object",
            "properties": {"docs": {"type": "boolean", "description": "Mirror to docs/."}},
        },
    },
    {
        "name": "gate",
        "description": "Run the full publishing gate: links, citations, page references, wording, print bundles and PDFs.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "hash",
        "description": "Determinism hash of a generated tree (share/site by default). Run twice after a rebuild; the two values must match.",
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string", "default": "share/site"}},
        },
    },
    {
        "name": "ship",
        "description": "Stage the shipped paths, commit as the noreply identity via environment variables, and optionally push. With check=true the gate and volume verifiers must pass first. Never stages session files, share/, or local databases.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Commit message, inline."},
                "message_from": {"type": "string", "description": "Repo-relative file holding the commit message."},
                "check": {"type": "boolean", "description": "Run gate and verifiers before committing."},
                "vol": {"type": "string", "description": "Volume to verify when check=true."},
                "push": {"type": "boolean", "description": "Push after committing."},
                "branch": {"type": "string", "default": "main"},
                "add": {"type": "array", "items": {"type": "string"}, "description": "Override the staged paths."},
            },
        },
    },
]

HANDLERS = {
    "status": lambda a: cote.cmd_status(SimpleNamespace()),
    "next": lambda a: cote.cmd_next(SimpleNamespace(vol=a.get("vol"))),
    "chapters": lambda a: cote.cmd_chapters(SimpleNamespace(vol=a.get("vol"))),
    "read_pages": lambda a: cote.cmd_read(SimpleNamespace(
        vol=a["vol"], pages=a["pages"], blank=bool(a.get("blank")))),
    "append": lambda a: cote.cmd_append(SimpleNamespace(
        file=a["file"], section=a.get("section"), from_file=a.get("from_file"),
        under=a.get("under"), stamp=a.get("stamp"), at_end=bool(a.get("at_end")))),
    "ledger_new": lambda a: cote.cmd_ledger_new(SimpleNamespace(
        kind=a["kind"], stem=a["stem"], header=a["header"], title=a.get("title"),
        start_vol=a.get("start_vol"), force=bool(a.get("force")))),
    "verify": lambda a: cote.cmd_verify(SimpleNamespace(vol=a.get("vol"))),
    "build": lambda a: cote.cmd_build(SimpleNamespace(docs=bool(a.get("docs")))),
    "gate": lambda a: cote.cmd_gate(SimpleNamespace(full=False)),
    "hash": lambda a: cote.cmd_hash(SimpleNamespace(path=a.get("path") or "share/site")),
    "ship": lambda a: cote.cmd_ship(SimpleNamespace(
        message=a.get("message"), message_from=a.get("message_from"),
        check=bool(a.get("check")), vol=a.get("vol") or None,
        push=bool(a.get("push")), branch=a.get("branch") or "main",
        add=a.get("add"))),
}


def call_tool(name: str, args: dict) -> tuple[str, bool]:
    handler = HANDLERS.get(name)
    if handler is None:
        return f"unknown tool: {name}", True
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            code = handler(args) or 0
        text = buf.getvalue().strip() or "(no output)"
        return text, code != 0
    except SystemExit as exc:  # cote.die() raises SystemExit
        text = (buf.getvalue() + f"\n(exit {exc.code})").strip()
        return text, True
    except Exception:  # keep tracebacks off the protocol channel shape
        return (buf.getvalue() + "\n" + traceback.format_exc(limit=6)).strip(), True


def reply(msg_id, result=None, error=None) -> None:
    out = {"jsonrpc": "2.0", "id": msg_id}
    if error is not None:
        out["error"] = error
    else:
        out["result"] = result
    sys.stdout.write(json.dumps(out) + "\n")
    sys.stdout.flush()


def serve() -> None:
    os.chdir(ROOT)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        method = msg.get("method")
        msg_id = msg.get("id")
        if msg_id is None:
            continue  # notification
        if method == "initialize":
            reply(msg_id, {
                "protocolVersion": msg.get("params", {}).get("protocolVersion", PROTOCOL),
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "cote-walk", "version": "1.0.0"},
            })
        elif method == "ping":
            reply(msg_id, {})
        elif method == "tools/list":
            reply(msg_id, {"tools": TOOLS})
        elif method == "tools/call":
            params = msg.get("params") or {}
            name = params.get("name")
            text, failed = call_tool(name, params.get("arguments") or {})
            reply(msg_id, {"content": [{"type": "text", "text": text}], "isError": failed})
        else:
            reply(msg_id, error={"code": -32601, "message": f"method not found: {method}"})


if __name__ == "__main__":
    serve()
