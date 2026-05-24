# mcp-mikrotik

MCP server for executing MikroTik RouterOS commands through a single MCP tool.

This server is useful when you want an MCP client such as Codex to interact with a MikroTik router directly over the RouterOS API without building a large tool surface first.

## Features

- Exposes one MCP tool: `mikrotik_terminal`
- Accepts direct RouterOS-style commands such as `/system/resource/print`
- Supports command arguments in `key=value` format
- Supports simple `[find ...]` expressions such as `/ip/service/set [find name=telnet] disabled=yes`
- Works with empty passwords by passing `password=""`

## Tool

### `mikrotik_terminal`

Arguments:

- `host`: Router IP address or hostname
- `username`: Router username
- `password`: Router password, can be an empty string
- `command`: Full RouterOS command path and arguments

Returns:

- execution status
- target router
- command and parsed arguments
- matched rows for `[find ...]` commands
- resulting rows from the RouterOS API call

## Command format

The command must start with an absolute RouterOS path.

Valid examples:

```text
/system/resource/print
/ip/service/print
/ip/service/set numbers=telnet disabled=yes
/ip/service/set [find name=telnet] disabled=yes
/interface/disable numbers=ether2
/ip/firewall/filter/add chain=input action=drop comment="Block input"
```

All arguments after the command path must use `key=value` format.

## Installation

Using `uv`:

```bash
uv sync
```

## Run locally

```bash
uv run python server.py
```

## MCP configuration

### Codex `config.toml`

```toml
[mcp_servers.mcp-mikrotik]
command = "uv"
args = ["--directory", "/path/to/mcp-mikrotik", "run", "python", "server.py"]
```

### Generic MCP JSON config

```json
{
  "mcpServers": {
    "mcp-mikrotik": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/mcp-mikrotik",
        "run",
        "python",
        "server.py"
      ]
    }
  }
}
```

## Example usage

Example payload sent by an MCP client:

```json
{
  "host": "192.168.10.1",
  "username": "admin",
  "password": "",
  "command": "/system/resource/print"
}
```

## Notes

- This server executes commands directly on the target router, so write operations should be used carefully.
- `[find ...]` support in this project resolves matching rows first, then executes the requested command using the matched `.id` values.
