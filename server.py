import shlex
from typing import Any, Dict, List
import re

from librouteros import connect
from mcp.server.fastmcp import FastMCP, Context


mcp = FastMCP(
    "MikroTik Terminal",
    dependencies=["librouteros"],
)


FIND_PATTERN = re.compile(r"\[find\s+([^\]]+)\]")


def _serialize_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {str(key): value for key, value in dict(row).items()}
        for row in rows
    ]


def _parse_key_value_tokens(tokens: List[str]) -> Dict[str, Any]:
    kwargs: Dict[str, Any] = {}
    invalid_tokens: List[str] = []

    for token in tokens:
        if "=" not in token:
            invalid_tokens.append(token)
            continue

        key, value = token.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise ValueError(f"Invalid argument token: {token}")
        kwargs[key] = value

    if invalid_tokens:
        raise ValueError(
            "All command arguments must use key=value format. "
            f"Invalid token(s): {', '.join(invalid_tokens)}"
        )

    return kwargs


@mcp.tool()
def mikrotik_terminal(
    host: str,
    username: str,
    command: str,
    password: str = "",
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Execute a RouterOS API command directly against a MikroTik router.

    Args:
        host: Router IP or hostname
        username: Router username
        password: Router password
        command: Full RouterOS API-style command such as:
            - /system/resource/print
            - /ip/service/print
            - /ip/service/set numbers=telnet disabled=yes
            - /ip/service/set [find name=telnet] disabled=yes
            - /interface/disable numbers=ether2
            - /ip/firewall/filter/add chain=input action=drop comment="Block input"
    """
    if not host:
        raise ValueError("host is required")
    if not username:
        raise ValueError("username is required")
    if password is None:
        raise ValueError("password is required")
    if not command.strip():
        raise ValueError("command is required")

    find_match = FIND_PATTERN.search(command)
    find_expression = find_match.group(1).strip() if find_match else None
    normalized_command = FIND_PATTERN.sub("", command).strip()

    tokens = shlex.split(normalized_command)
    if not tokens:
        raise ValueError("command is required")

    api_command = tokens[0].strip()
    if not api_command.startswith("/"):
        raise ValueError("command must start with an absolute RouterOS path such as /ip/service/print")

    kwargs = _parse_key_value_tokens(tokens[1:])

    masked_target = f"{username}@{host}"
    if ctx:
        ctx.info(f"Executing MikroTik command on {masked_target}: {api_command}")

    api = connect(host=host, username=username, password=password)
    try:
        matched_rows: List[Dict[str, Any]] = []

        if find_expression:
            find_kwargs = _parse_key_value_tokens(shlex.split(find_expression))
            base_path, _, action = api_command.rpartition("/")
            if not base_path or not action:
                raise ValueError("Could not resolve base path for [find ...] command")

            source_rows = _serialize_rows(list(api(f"{base_path}/print")))
            matched_rows = [
                row
                for row in source_rows
                if all(str(row.get(key, "")) == str(value) for key, value in find_kwargs.items())
            ]

            if not matched_rows:
                return {
                    "success": False,
                    "target": masked_target,
                    "command": api_command,
                    "arguments": kwargs,
                    "find": find_kwargs,
                    "error": "No rows matched the [find ...] expression.",
                }

            matched_ids = [row.get(".id") for row in matched_rows if row.get(".id")]
            if not matched_ids:
                return {
                    "success": False,
                    "target": masked_target,
                    "command": api_command,
                    "arguments": kwargs,
                    "find": find_kwargs,
                    "error": "Matched rows do not expose .id values required for execution.",
                }

            kwargs[".id"] = ",".join(str(item_id) for item_id in matched_ids)

        rows = list(api(api_command, **kwargs))
        serialized_rows = _serialize_rows(rows)

        return {
            "success": True,
            "target": masked_target,
            "command": api_command,
            "arguments": kwargs,
            "matched_rows": matched_rows,
            "count": len(serialized_rows),
            "rows": serialized_rows,
        }
    finally:
        api.close()


@mcp.prompt()
def mikrotik_terminal_prompt() -> str:
    return """I want to manage a MikroTik router through one MCP tool.

Provide:
- host
- username
- password
- a full RouterOS command

Use commands in the form:
- /system/resource/print
- /ip/service/print
- /ip/service/set numbers=telnet disabled=yes
- /ip/service/set [find name=telnet] disabled=yes
- /interface/disable numbers=ether2
- /ip/firewall/filter/add chain=input action=drop comment="Block input"
"""


if __name__ == "__main__":
    mcp.run()
